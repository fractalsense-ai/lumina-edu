"""Config-driven problem generator lookup for the education-math pack.

Each math module owns its generator path in ``modules/<name>/module-config.yaml``
under ``adapters.task_initializer``. This compatibility module keeps the old
``generate_problem`` entry point available without making this file the place
where new module paths must be manually amended.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from lumina.core.yaml_loader import load_yaml

_PACK_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _PACK_DIR.parent.parent
_MODULE_DIR = _PACK_DIR / "modules"

_loaded_modules: dict[str, Any] = {}
_generator_paths: dict[str, Path] | None = None
_physics_paths: dict[str, Path] | None = None


def _discover_modules() -> tuple[dict[str, Path], dict[str, Path]]:
    generator_paths: dict[str, Path] = {}
    physics_paths: dict[str, Path] = {}
    for module_config_path in sorted(_MODULE_DIR.glob("*/module-config.yaml")):
        module_cfg = load_yaml(module_config_path)
        physics_path_raw = module_cfg.get("domain_physics_path")
        if not isinstance(physics_path_raw, str) or not physics_path_raw:
            continue
        physics_path = _REPO_ROOT / physics_path_raw
        if not physics_path.is_file():
            continue
        with physics_path.open(encoding="utf-8") as fh:
            physics = json.load(fh)
        domain_id = physics.get("id") or physics.get("domain_id")
        if not isinstance(domain_id, str) or not domain_id:
            continue
        physics_paths[domain_id] = physics_path
        task_init = ((module_cfg.get("adapters") or {}).get("task_initializer") or {})
        module_path_raw = task_init.get("module_path")
        if isinstance(module_path_raw, str) and module_path_raw:
            generator_paths[domain_id] = _REPO_ROOT / module_path_raw
    return generator_paths, physics_paths


def _get_generator_paths() -> dict[str, Path]:
    global _generator_paths, _physics_paths
    if _generator_paths is None or _physics_paths is None:
        _generator_paths, _physics_paths = _discover_modules()
    return _generator_paths


def _get_physics_paths() -> dict[str, Path]:
    global _generator_paths, _physics_paths
    if _generator_paths is None or _physics_paths is None:
        _generator_paths, _physics_paths = _discover_modules()
    return _physics_paths


def list_generator_ids() -> list[str]:
    """Return domain IDs that expose module-local problem generators."""
    return sorted(_get_generator_paths())


def _default_domain_id() -> str:
    pack = load_yaml(_PACK_DIR / "pack.yaml")
    default_module = str(pack.get("default_module") or "")
    if default_module:
        for domain_id, path in _get_generator_paths().items():
            if path.parent.name == default_module:
                return domain_id
    ids = list_generator_ids()
    if not ids:
        raise ValueError("No education-math problem generators discovered")
    return ids[0]


def _load_generator(domain_id: str) -> Any:
    """Lazy-load and cache the per-module generator."""
    if domain_id in _loaded_modules:
        return _loaded_modules[domain_id]

    gen_path = _get_generator_paths().get(domain_id)
    if gen_path is None or not gen_path.exists():
        raise ValueError(f"No problem generator registered for domain_id={domain_id!r}")

    module_name = f"_edumath_gen_{domain_id.replace('/', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(gen_path))
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Cannot load problem generator from {gen_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _loaded_modules[domain_id] = mod
    return mod


def load_domain_physics(domain_id: str) -> dict[str, Any]:
    """Load a math module's domain physics by domain ID."""
    physics_path = _get_physics_paths().get(domain_id)
    if physics_path is None or not physics_path.exists():
        raise ValueError(f"No domain physics registered for domain_id={domain_id!r}")
    with physics_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def select_tier(difficulty: float, tiers: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the tier whose range contains *difficulty*; fallback to last tier."""
    for tier in tiers:
        lo = float(tier.get("min_difficulty", 0.0))
        hi = float(tier.get("max_difficulty", 1.0))
        if lo <= difficulty < hi:
            return tier
    return tiers[-1]


def generate_problem(
    difficulty: float,
    subsystem_configs: dict[str, Any] | None = None,
    *,
    domain_id: str | None = None,
) -> dict[str, Any]:
    """Generate a problem through the module-local generator configured by sidecar."""
    resolved_domain_id = domain_id or _default_domain_id()
    physics = load_domain_physics(resolved_domain_id)
    configs = subsystem_configs or (physics.get("subsystem_configs") or {})
    mod = _load_generator(resolved_domain_id)
    return mod.generate_problem(float(difficulty), configs)


def initialize_task(
    task_spec: dict[str, Any],
    runtime: dict[str, Any],
    *,
    domain_id: str | None = None,
) -> dict[str, Any]:
    """Task initializer adapter compatible with the core runtime hook."""
    difficulty = float(task_spec.get("nominal_difficulty", 0.5))
    subsystem_configs = (runtime.get("domain") or {}).get("subsystem_configs") or {}
    return generate_problem(difficulty, subsystem_configs, domain_id=domain_id)