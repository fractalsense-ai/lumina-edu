from __future__ import annotations

import json
from pathlib import Path

import yaml

from lumina.core.adapter_indexer import scan_tool_adapters
from lumina.core.runtime_loader import load_runtime_context

REPO_ROOT = Path(__file__).resolve().parents[1]
ADMIN_PACK = REPO_ROOT / "model-packs" / "education-admin"
COMMONS_PACK = REPO_ROOT / "model-packs" / "education-commons"
ADMIN_MODULE_IDS = {
    "domain/eduadm/domain-authority/v1",
    "domain/eduadm/teacher/v1",
    "domain/eduadm/teaching-assistant/v1",
}
LEGACY_ADMIN_IDS = {
    "domain/edu/domain-authority/v1",
    "domain/edu/teacher/v1",
    "domain/edu/teaching-assistant/v1",
}


def test_education_admin_runtime_loads_admin_modules() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-admin/cfg/runtime-config.yaml")

    assert runtime["module_id"] == "domain/eduadm/v1"
    assert set(runtime["module_map"]) == ADMIN_MODULE_IDS
    assert runtime["role_to_default_module"] == {
        "domain_authority": "domain/eduadm/domain-authority/v1",
        "teacher": "domain/eduadm/teacher/v1",
        "teaching_assistant": "domain/eduadm/teaching-assistant/v1",
    }
    assert runtime["state_builder_fn"] is not None
    assert runtime["turn_interpreter_fn"] is not None


def test_education_admin_module_sidecars_are_retargeted() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-admin/cfg/runtime-config.yaml")

    for module_id, module_cfg in runtime["module_map"].items():
        module_path = Path(module_cfg["module_path"])
        assert module_path.parts[:2] == ("model-packs", "education-admin")
        assert module_cfg.get("local_only") is True
        assert module_cfg.get("domain_physics_path")
        physics = module_cfg.get("domain_physics")
        assert isinstance(physics, dict), module_id
        assert physics["id"] == module_id
        resolved_physics_path = module_cfg["domain_physics_path"].replace("\\", "/")
        assert "model-packs/education-admin" in resolved_physics_path


def test_education_admin_pack_manifest_matches_runtime_modules() -> None:
    pack = yaml.safe_load((ADMIN_PACK / "pack.yaml").read_text(encoding="utf-8"))
    module_ids = {entry["module_id"] for entry in pack["modules"]}

    assert pack["pack_id"] == "education-admin"
    assert pack["module_prefix"] == "eduadm"
    assert pack["default_module"] == "domain-authority"
    assert module_ids == ADMIN_MODULE_IDS


def test_education_admin_tool_adapters_are_self_contained() -> None:
    adapters = scan_tool_adapters(ADMIN_PACK)

    assert {
        "adapter/eduadm/role-assignment/v1",
        "adapter/eduadm/physics-staging/v1",
        "adapter/eduadm/progress-overview/v1",
        "adapter/eduadm/ingestion/v1",
        "adapter/eduadm/student-roster/v1",
        "adapter/eduadm/module-assignment/v1",
        "adapter/eduadm/escalation-handler/v1",
        "adapter/eduadm/student-view/v1",
        "adapter/eduadm/hint-delivery/v1",
    }.issubset(set(adapters))


def test_education_admin_owns_staff_roles_not_guardian_runtime() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-admin/cfg/runtime-config.yaml")
    domain_roles = runtime["domain"]["domain_roles"]["roles"]
    role_ids = {role["role_id"] for role in domain_roles}
    dispatcher_source = (ADMIN_PACK / "controllers" / "education_operations.py").read_text(encoding="utf-8")

    assert role_ids == {"domain_authority", "teacher", "teaching_assistant"}
    assert "assign_guardian" not in dispatcher_source
    assert "assign_commons" not in dispatcher_source
    assert "domain/educom/guardian/v1" not in json.dumps(runtime["domain"])


def test_legacy_education_no_longer_actively_owns_staff_admin_or_guardian_modules() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education/cfg/runtime-config.yaml")
    module_ids = set(runtime.get("module_map") or {})
    role_defaults = runtime.get("role_to_default_module") or {}
    operations = yaml.safe_load(
        (REPO_ROOT / "model-packs" / "education" / "cfg" / "runtime-config.yaml").read_text(encoding="utf-8")
    ).get("operation_handlers") or {}

    assert module_ids == {"domain/edu/general-education/v1"}
    assert module_ids.isdisjoint(LEGACY_ADMIN_IDS)
    assert "domain_authority" not in role_defaults
    assert "teacher" not in role_defaults
    assert "teaching_assistant" not in role_defaults
    assert "parent" not in role_defaults
    assert "assign_guardian" not in operations
    assert "assign_module" not in operations
    assert "assign_student" not in operations


def test_education_commons_owns_guardian_runtime_and_operation() -> None:
    runtime = load_runtime_context(REPO_ROOT, "model-packs/education-commons/cfg/runtime-config.yaml")
    module_ids = set(runtime.get("module_map") or {})
    role_defaults = runtime.get("role_to_default_module") or {}
    operations = yaml.safe_load(
        (COMMONS_PACK / "cfg" / "runtime-config.yaml").read_text(encoding="utf-8")
    ).get("operation_handlers") or {}

    assert {"domain/educom/student-commons/v1", "domain/educom/guardian/v1"}.issubset(module_ids)
    assert role_defaults["parent"] == "domain/educom/guardian/v1"
    assert "assign_guardian" in operations
    assert operations["assign_guardian"]["module_path"] == "model-packs/education-commons/controllers/education_operations.py"
