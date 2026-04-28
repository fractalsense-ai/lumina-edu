from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "education-pack-cutover-map.py"


def _load_cutover_module() -> Any:
    spec = importlib.util.spec_from_file_location("education_pack_cutover_map_test", str(SCRIPT_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["education_pack_cutover_map_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_transform_record_rewrites_nested_active_math_ids() -> None:
    cutover = _load_cutover_module()

    record = {
        "domain_id": "domain/edu/pre-algebra/v1",
        "subject_domain_id": "domain/edu/algebra-intro/v1",
        "module_id": "domain/edu/algebra-1/v1",
        "domain_key": "education",
        "governed_modules": ["domain/edu/algebra-level-1/v1"],
        "domain_roles": {"domain/edu/pre-algebra/v1": "student"},
        "modules": {
            "domain/edu/pre-algebra/v1": {"challenge": 0.4},
            "domain/edu/algebra-intro/v1": {"challenge": 0.5},
        },
        "assignment": {
            "module_ids": [
                "domain/edu/pre-algebra/v1",
                "domain/edu/algebra-intro/v1",
            ],
        },
    }

    transformed = cutover.transform_record(record)

    assert transformed["domain_id"] == "domain/edumath/pre-algebra/v1"
    assert transformed["subject_domain_id"] == "domain/edumath/algebra-intro/v1"
    assert transformed["module_id"] == "domain/edumath/algebra-1/v1"
    assert transformed["domain_key"] == "education-commons"
    assert transformed["governed_modules"] == ["domain/edumath/algebra-level-1/v1"]
    assert transformed["domain_roles"] == {"domain/edumath/pre-algebra/v1": "student"}
    assert set(transformed["modules"]) == {
        "domain/edumath/pre-algebra/v1",
        "domain/edumath/algebra-intro/v1",
    }
    assert transformed["assignment"]["module_ids"] == [
        "domain/edumath/pre-algebra/v1",
        "domain/edumath/algebra-intro/v1",
    ]
    assert record["domain_id"] == "domain/edu/pre-algebra/v1"


def test_transform_record_rewrites_nested_active_admin_ids() -> None:
    cutover = _load_cutover_module()

    record = {
        "domain_id": "domain/edu/domain-authority/v1",
        "module_id": "domain/edu/teacher/v1",
        "governed_modules": [
            "domain/edu/domain-authority/v1",
            "domain/edu/teaching-assistant/v1",
        ],
        "domain_roles": {
            "domain/edu/domain-authority/v1": "domain_authority",
            "domain/edu/teacher/v1": "teacher",
        },
        "assignment": {
            "module_ids": ["domain/edu/teacher/v1"]
        },
    }

    transformed = cutover.transform_record(record)

    assert transformed["domain_id"] == "domain/eduadm/domain-authority/v1"
    assert transformed["module_id"] == "domain/eduadm/teacher/v1"
    assert transformed["governed_modules"] == [
        "domain/eduadm/domain-authority/v1",
        "domain/eduadm/teaching-assistant/v1",
    ]
    assert transformed["domain_roles"] == {
        "domain/eduadm/domain-authority/v1": "domain_authority",
        "domain/eduadm/teacher/v1": "teacher",
    }
    assert transformed["assignment"]["module_ids"] == ["domain/eduadm/teacher/v1"]
    assert record["domain_id"] == "domain/edu/domain-authority/v1"


def test_transform_record_does_not_rewrite_immutable_commitment_records() -> None:
    cutover = _load_cutover_module()
    record = {
        "record_id": "rec-001",
        "commitment_type": "module_assignment",
        "metadata": {"module_id": "domain/edu/pre-algebra/v1"},
        "references": ["student1", "domain/edu/pre-algebra/v1"],
    }

    transformed = cutover.transform_record(record)

    assert transformed == record
    assert transformed is not record
