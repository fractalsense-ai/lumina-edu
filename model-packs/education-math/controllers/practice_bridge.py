"""Math practice bridge for safe cross-pack requests.

This tool intentionally does not solve the student's submitted expression. It
selects an appropriate math module and returns a fresh analogous practice item
from that module's configured generator.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

_THIS_DIR = Path(__file__).resolve().parent
_GEN_SPEC = importlib.util.spec_from_file_location(
    "edumath_problem_generator_bridge",
    str(_THIS_DIR / "problem_generator.py"),
)
if _GEN_SPEC is None or _GEN_SPEC.loader is None:
    raise ModuleNotFoundError("Cannot load education-math problem generator bridge")
if "edumath_problem_generator_bridge" not in sys.modules:
    _GEN_MOD = importlib.util.module_from_spec(_GEN_SPEC)
    sys.modules["edumath_problem_generator_bridge"] = _GEN_MOD
    _GEN_SPEC.loader.exec_module(_GEN_MOD)
else:
    _GEN_MOD = sys.modules["edumath_problem_generator_bridge"]

_DOMAIN_PRE_ALGEBRA = "domain/edumath/pre-algebra/v1"
_DOMAIN_ALGEBRA_INTRO = "domain/edumath/algebra-intro/v1"
_DOMAIN_ALGEBRA_1 = "domain/edumath/algebra-1/v1"


def _coerce_difficulty(value: Any) -> float:
    try:
        difficulty = float(value)
    except (TypeError, ValueError):
        difficulty = 0.5
    return max(0.0, min(1.0, difficulty))


def _infer_domain_id(expression: str, requested_domain_id: str | None) -> str:
    if requested_domain_id in _GEN_MOD.list_generator_ids():
        return requested_domain_id
    lower = expression.lower()
    if re.search(r"\bx\s*\^\s*2\b|quadratic|factor|polynomial", lower):
        return _DOMAIN_ALGEBRA_1
    if re.search(r"\by\s*=|slope|system|graph|intercept", lower):
        return _DOMAIN_ALGEBRA_INTRO
    return _DOMAIN_PRE_ALGEBRA


def generate_similar_math_problem(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a similar practice problem without solving submitted work.

    Expected payload keys are intentionally broad so Commons can pass either raw
    turn data or a normalized practice request:
    ``expression``/``student_expression``, optional ``domain_id``/``module_id``,
    and optional ``difficulty``.
    """
    request = payload or {}
    expression = str(
        request.get("student_expression")
        or request.get("expression")
        or request.get("tool_expression")
        or ""
    )
    requested_domain_id = request.get("domain_id") or request.get("module_id")
    if requested_domain_id is not None:
        requested_domain_id = str(requested_domain_id)
    domain_id = _infer_domain_id(expression, requested_domain_id)
    difficulty = _coerce_difficulty(request.get("difficulty") or request.get("nominal_difficulty"))
    problem = _GEN_MOD.generate_problem(difficulty, domain_id=domain_id)
    return {
        "ok": True,
        "policy": "similar_practice_only",
        "domain_id": domain_id,
        "withheld": ["submitted_solution", "submitted_answer"],
        "practice_problem": problem,
    }