"""SVA convenience helpers built on the generic signal framework.

The core signal math lives in :mod:`lumina.signals.baseline` and is
signal-name agnostic. This module keeps the Salience/Valence/Arousal
compatibility shape used by journaling code while avoiding dependencies on
any domain pack implementation.
"""

from __future__ import annotations

from typing import Any

from .baseline import (
    _initial_run,
    _update_rhythm,
    _z,
    check_shape_deviation as _check_signal_shape_deviation,
)


DEFAULT_PARAMS: dict[str, Any] = {
    "ewma_alpha": 0.1,
    "ewma_initial_variance": 0.04,
    "rhythm_noise_floor": 0.05,
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _baseline_axis(global_baseline: Any, axis: str, default: float) -> float:
    if isinstance(global_baseline, dict):
        return float(global_baseline.get(axis, default))
    return float(getattr(global_baseline, axis, default))


def update_relational_baseline(
    relational_baseline: dict[str, Any],
    entity_hash: str,
    valence_delta: float,
    arousal_delta: float,
    salience_delta: float,
    params: dict[str, Any] | None = None,
    global_baseline: Any | None = None,
) -> dict[str, Any]:
    """Update a privacy-preserving per-entity SVA baseline.

    ``entity_hash`` is expected to be an opaque value such as ``Entity_A4F9``;
    raw entity text should never be passed here.
    """
    p = {**DEFAULT_PARAMS, **dict(params or {})}
    alpha = float(p["ewma_alpha"])
    seed_var = float(p["ewma_initial_variance"])
    noise_floor = float(p["rhythm_noise_floor"])

    seed_salience = _baseline_axis(global_baseline, "salience", 0.5) if global_baseline is not None else 0.5
    seed_valence = _baseline_axis(global_baseline, "valence", 0.0) if global_baseline is not None else 0.0
    seed_arousal = _baseline_axis(global_baseline, "arousal", 0.5) if global_baseline is not None else 0.5

    entry = relational_baseline.get(entity_hash)
    if entry is None:
        entry = {
            "salience": round(_clamp(seed_salience + salience_delta * alpha, 0.0, 1.0), 6),
            "valence": round(_clamp(seed_valence + valence_delta * alpha, -1.0, 1.0), 6),
            "arousal": round(_clamp(seed_arousal + arousal_delta * alpha, 0.0, 1.0), 6),
            "salience_variance": round(seed_var, 6),
            "valence_variance": round(seed_var, 6),
            "arousal_variance": round(seed_var, 6),
            "salience_crossing_rate": 0.5,
            "valence_crossing_rate": 0.5,
            "arousal_crossing_rate": 0.5,
            "salience_run_length": _initial_run(salience_delta, noise_floor),
            "valence_run_length": _initial_run(valence_delta, noise_floor),
            "arousal_run_length": _initial_run(arousal_delta, noise_floor),
            "sample_count": 1,
        }
    else:
        prev_salience = float(entry.get("salience", seed_salience))
        prev_valence = float(entry.get("valence", seed_valence))
        prev_arousal = float(entry.get("arousal", seed_arousal))
        prev_salience_var = float(entry.get("salience_variance", seed_var))
        prev_valence_var = float(entry.get("valence_variance", seed_var))
        prev_arousal_var = float(entry.get("arousal_variance", seed_var))
        prev_salience_run = int(entry.get("salience_run_length", 0))
        prev_valence_run = int(entry.get("valence_run_length", 0))
        prev_arousal_run = int(entry.get("arousal_run_length", 0))
        prev_salience_cross = float(entry.get("salience_crossing_rate", 0.5))
        prev_valence_cross = float(entry.get("valence_crossing_rate", 0.5))
        prev_arousal_cross = float(entry.get("arousal_crossing_rate", 0.5))

        salience_run, salience_cross = _update_rhythm(
            salience_delta, prev_salience_run, prev_salience_cross, alpha, noise_floor
        )
        valence_run, valence_cross = _update_rhythm(
            valence_delta, prev_valence_run, prev_valence_cross, alpha, noise_floor
        )
        arousal_run, arousal_cross = _update_rhythm(
            arousal_delta, prev_arousal_run, prev_arousal_cross, alpha, noise_floor
        )

        entry = {
            "salience": round(_clamp(alpha * (prev_salience + salience_delta) + (1 - alpha) * prev_salience, 0.0, 1.0), 6),
            "valence": round(_clamp(alpha * (prev_valence + valence_delta) + (1 - alpha) * prev_valence, -1.0, 1.0), 6),
            "arousal": round(_clamp(alpha * (prev_arousal + arousal_delta) + (1 - alpha) * prev_arousal, 0.0, 1.0), 6),
            "salience_variance": round(alpha * (salience_delta ** 2) + (1 - alpha) * prev_salience_var, 6),
            "valence_variance": round(alpha * (valence_delta ** 2) + (1 - alpha) * prev_valence_var, 6),
            "arousal_variance": round(alpha * (arousal_delta ** 2) + (1 - alpha) * prev_arousal_var, 6),
            "salience_crossing_rate": round(salience_cross, 6),
            "valence_crossing_rate": round(valence_cross, 6),
            "arousal_crossing_rate": round(arousal_cross, 6),
            "salience_run_length": salience_run,
            "valence_run_length": valence_run,
            "arousal_run_length": arousal_run,
            "sample_count": int(entry.get("sample_count", 1)) + 1,
        }

    relational_baseline[entity_hash] = entry
    return relational_baseline


def check_relational_deviation(
    entry: dict[str, Any] | None,
    valence: float,
    arousal: float,
    salience: float,
    k_sigma: float,
    min_samples: int = 5,
    min_variance_floor: float = 0.001,
) -> dict[str, Any]:
    """Run an SVA z-score envelope check against one relational baseline."""
    if entry is None or int(entry.get("sample_count", 0)) < int(min_samples):
        return {
            "triggered": False,
            "axis": None,
            "z_score": 0.0,
            "reason": "baseline_immature",
            "mature": False,
        }

    scores = {
        "valence": _z(valence, float(entry.get("valence", 0.0)), float(entry.get("valence_variance", min_variance_floor)), min_variance_floor),
        "arousal": _z(arousal, float(entry.get("arousal", 0.5)), float(entry.get("arousal_variance", min_variance_floor)), min_variance_floor),
        "salience": _z(salience, float(entry.get("salience", 0.5)), float(entry.get("salience_variance", min_variance_floor)), min_variance_floor),
    }
    worst_axis, worst_z = max(scores.items(), key=lambda item: item[1])
    triggered = worst_z > float(k_sigma)
    return {
        "triggered": triggered,
        "axis": worst_axis if triggered else None,
        "z_score": round(worst_z, 4),
        "reason": "envelope_exceeded" if triggered else "within_envelope",
        "mature": True,
    }


def check_shape_deviation(
    crossing_rate: float,
    run_length: int,
    sample_count: int,
    k_shape: float = 2.0,
    min_samples: int = 10,
    min_crossing_rate: float = 0.05,
) -> dict[str, Any]:
    """Run the SVA heartbeat-shape check using generic signal math."""
    return _check_signal_shape_deviation(
        {
            "crossing_rate": crossing_rate,
            "run_length": run_length,
            "sample_count": sample_count,
        },
        k_shape=k_shape,
        min_samples=min_samples,
        min_crossing_rate=min_crossing_rate,
    )