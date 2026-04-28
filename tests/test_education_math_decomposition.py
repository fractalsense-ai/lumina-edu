from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from lumina.api.runtime_helpers import apply_tool_call_policy
from lumina.core.adapter_indexer import scan_tool_adapters
from lumina.core.runtime_loader import load_runtime_context

REPO_ROOT = Path(__file__).resolve().parents[1]
MATH_PACK = REPO_ROOT / "model-packs" / "education-math"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_education_math_runtime_loads_with_module_initializers() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-math/cfg/runtime-config.yaml")

    assert runtime["module_id"] == "domain/edumath/pre-algebra/v1"
    assert set(runtime["module_map"]) == {
        "domain/edumath/pre-algebra/v1",
        "domain/edumath/algebra-intro/v1",
        "domain/edumath/algebra-1/v1",
        "domain/edumath/algebra-level-1/v1",
    }
    for module_id, module_cfg in runtime["module_map"].items():
        assert module_cfg.get("task_initializer_fn") is not None, module_id


def test_math_problem_generator_discovers_module_sidecars() -> None:
    problem_generator = _load_module(
        "education_math_problem_generator_test",
        MATH_PACK / "controllers" / "problem_generator.py",
    )

    assert problem_generator.list_generator_ids() == [
        "domain/edumath/algebra-1/v1",
        "domain/edumath/algebra-intro/v1",
        "domain/edumath/algebra-level-1/v1",
        "domain/edumath/pre-algebra/v1",
    ]
    problem = problem_generator.generate_problem(
        0.4,
        domain_id="domain/edumath/pre-algebra/v1",
    )
    assert problem["status"] == "in_progress"
    assert "equation" in problem
    assert "expected_answer" in problem


def test_math_problem_generator_has_no_static_domain_path_map() -> None:
    source = (MATH_PACK / "controllers" / "problem_generator.py").read_text(encoding="utf-8")

    assert "_GENERATOR_PATHS" not in source
    assert '"domain/edumath/pre-algebra/v1": _MODULE_DIR' not in source


def test_education_math_tool_adapters_are_self_contained() -> None:
    adapters = scan_tool_adapters(MATH_PACK)

    assert {
        "adapter/edumath/algebra-checker/v1",
        "adapter/edumath/algebra-parser/v1",
        "adapter/edumath/calculator/v1",
        "adapter/edumath/substitution-checker/v1",
    }.issubset(set(adapters))


def test_practice_bridge_generates_similar_problem_without_solving_submitted_work() -> None:
    bridge = _load_module(
        "education_math_practice_bridge_test",
        MATH_PACK / "controllers" / "practice_bridge.py",
    )

    result = bridge.generate_similar_math_problem(
        {"expression": "please solve 2x + 3 = 11", "difficulty": 0.45}
    )

    assert result["ok"] is True
    assert result["policy"] == "similar_practice_only"
    assert "submitted_answer" in result["withheld"]
    assert result["domain_id"] == "domain/edumath/pre-algebra/v1"
    practice = result["practice_problem"]
    assert practice["status"] == "in_progress"
    assert practice["equation"] != "2x + 3 = 11"


def test_student_commons_routes_math_questions_to_practice_bridge() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-commons/cfg/runtime-config.yaml")
    evidence = runtime["turn_interpreter_fn"](
        call_llm=lambda **kwargs: "{}",
        input_text="Can you solve 2x + 3 = 11 for my homework?",
        task_context={},
        prompt_text=runtime["turn_interpretation_prompt"],
        default_fields=runtime["turn_input_defaults"],
        tool_fns=runtime["tool_fns"],
    )

    assert evidence["intent_type"] == "math_practice_request"
    state, decision = runtime["domain_step_fn"](
        state={"vocabulary_tracking": {"baseline_sessions_remaining": 0}},
        task_spec={},
        evidence=evidence,
        params={},
    )
    assert state["vocabulary_tracking"]["baseline_sessions_remaining"] == 0
    assert decision["action"] == "math_practice_request"

    tool_results = apply_tool_call_policy(
        "math_practice_request",
        prompt_contract={},
        turn_data=evidence,
        task_spec={"nominal_difficulty": 0.45},
        runtime=runtime,
    )
    assert tool_results[0]["tool_id"] == "generate_similar_math_problem"
    assert tool_results[0]["result"]["policy"] == "similar_practice_only"
    assert tool_results[0]["result"]["practice_problem"]["equation"] != "2x + 3 = 11"
