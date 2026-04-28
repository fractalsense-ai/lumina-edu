"""Runtime adapters for the Education Presentation pack."""
from __future__ import annotations

import json
from typing import Any, Callable


def build_initial_state(profile: dict[str, Any]) -> dict[str, Any]:
    entity_state = profile.get("entity_state") or {}
    return {
        "score": 0.0,
        "uncertainty": 0.1,
        "turn_count": int(entity_state.get("total_sessions", 0)),
        "logic_override_attempted": False,
        "consent_boundary_obscured": False,
    }


def domain_step(
    state: dict[str, Any],
    task_spec: dict[str, Any],
    evidence: dict[str, Any],
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    new_state = dict(state)
    new_state["turn_count"] = int(new_state.get("turn_count", 0)) + 1
    new_state["logic_override_attempted"] = bool(evidence.get("logic_override_attempted", False))
    new_state["consent_boundary_obscured"] = bool(evidence.get("consent_boundary_obscured", False))

    boundary_violation = new_state["logic_override_attempted"] or new_state["consent_boundary_obscured"]
    return new_state, {
        "tier": "critical" if boundary_violation else "ok",
        "action": "halt_presentation_override" if boundary_violation else None,
        "frustration": False,
        "escalation_eligible": boundary_violation,
    }


def _strip_markdown_fences(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[: cleaned.rfind("```")]
    return cleaned.strip()


def interpret_turn_input(
    call_llm: Callable[[str, str, str | None], str],
    input_text: str,
    task_context: dict[str, Any],
    prompt_text: str,
    default_fields: dict[str, Any] | None = None,
    tool_fns: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any]:
    try:
        raw_response = call_llm(system=prompt_text, user=f"Presentation request: {input_text}", model=None)
        evidence = json.loads(_strip_markdown_fences(raw_response))
        if not isinstance(evidence, dict):
            evidence = {}
    except Exception:
        evidence = {}

    defaults = {
        "on_track": True,
        "response_latency_sec": 5.0,
        "off_task_ratio": 0.0,
        "logic_override_attempted": False,
        "consent_boundary_obscured": False,
    }
    defaults.update(default_fields or {})
    for key, value in defaults.items():
        evidence.setdefault(key, value)
    return evidence
