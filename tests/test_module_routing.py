"""Tests for active education/education-math module routing.

The legacy education pack keeps general/guardian modules active. Math learning
modules are owned by the education-math pack, and staff/admin modules are owned
by the education-admin pack. Old domain/edu/* math/admin IDs are migration
inputs only.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
EDU_CFG = REPO_ROOT / "model-packs" / "education" / "cfg" / "runtime-config.yaml"
MATH_CFG = REPO_ROOT / "model-packs" / "education-math" / "cfg" / "runtime-config.yaml"
MATH_MODULES = REPO_ROOT / "model-packs" / "education-math" / "modules"

LEGACY_EDU_ACTIVE_MODULE_IDS = [
    "domain/edu/general-education/v1",
    "domain/edu/guardian/v1",
]

LEGACY_ADMIN_IDS = [
    "domain/edu/domain-authority/v1",
    "domain/edu/teacher/v1",
    "domain/edu/teaching-assistant/v1",
]

MATH_MODULE_IDS = [
    "domain/edumath/pre-algebra/v1",
    "domain/edumath/algebra-intro/v1",
    "domain/edumath/algebra-1/v1",
    "domain/edumath/algebra-level-1/v1",
]

LEGACY_MATH_IDS = [
    "domain/edu/pre-algebra/v1",
    "domain/edu/algebra-intro/v1",
    "domain/edu/algebra-1/v1",
    "domain/edu/algebra-level-1/v1",
]

EXPECTED_SCHEMA_IDS = {
    "domain/edumath/pre-algebra/v1": "lumina:evidence:education-math:pre-algebra:v1",
    "domain/edumath/algebra-intro/v1": "lumina:evidence:education-math:algebra-intro:v1",
    "domain/edumath/algebra-1/v1": "lumina:evidence:education-math:algebra-1:v1",
}

MODULE_DIR_MAP = {
    "domain/edumath/pre-algebra/v1": "pre-algebra",
    "domain/edumath/algebra-intro/v1": "algebra-intro",
    "domain/edumath/algebra-1/v1": "algebra-1",
}


def _load_runtime(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["runtime"]


def _merge_sidecars(module_map: dict) -> dict:
    for _mod_cfg in module_map.values():
        _mod_dir = _mod_cfg.get("module_path")
        if _mod_dir:
            _mc_path = REPO_ROOT / _mod_dir / "module-config.yaml"
            if _mc_path.is_file():
                with open(_mc_path, encoding="utf-8") as f:
                    _mc = yaml.safe_load(f)
                if isinstance(_mc, dict):
                    for _key, _value in _mc.items():
                        if _key not in _mod_cfg:
                            _mod_cfg[_key] = _value
    return module_map


@pytest.fixture(scope="module")
def edu_runtime_cfg() -> dict:
    return _load_runtime(EDU_CFG)


@pytest.fixture(scope="module")
def edu_module_map(edu_runtime_cfg) -> dict:
    return _merge_sidecars(edu_runtime_cfg.get("module_map", {}))


@pytest.fixture(scope="module")
def math_runtime_cfg() -> dict:
    return _load_runtime(MATH_CFG)


@pytest.fixture(scope="module")
def math_module_map(math_runtime_cfg) -> dict:
    return _merge_sidecars(math_runtime_cfg.get("module_map", {}))


class TestLegacyEducationModuleMapStructure:
    def test_module_map_key_exists(self, edu_runtime_cfg):
        assert "module_map" in edu_runtime_cfg

    def test_legacy_education_has_only_non_math_entries(self, edu_module_map):
        assert set(edu_module_map) == set(LEGACY_EDU_ACTIVE_MODULE_IDS)
        for legacy_math_id in LEGACY_MATH_IDS:
            assert legacy_math_id not in edu_module_map
        for legacy_admin_id in LEGACY_ADMIN_IDS:
            assert legacy_admin_id not in edu_module_map

    @pytest.mark.parametrize("domain_id", LEGACY_EDU_ACTIVE_MODULE_IDS)
    def test_expected_legacy_domain_ids_present(self, edu_module_map, domain_id):
        assert domain_id in edu_module_map

    @pytest.mark.parametrize("domain_id", LEGACY_EDU_ACTIVE_MODULE_IDS)
    def test_legacy_entries_have_domain_physics_paths(self, edu_module_map, domain_id):
        entry = edu_module_map[domain_id]
        assert isinstance(entry.get("domain_physics_path"), str)
        assert entry["domain_physics_path"].strip()


class TestEducationMathModuleMapStructure:
    def test_math_module_map_has_four_entries(self, math_module_map):
        assert set(math_module_map) == set(MATH_MODULE_IDS)

    @pytest.mark.parametrize("domain_id", MATH_MODULE_IDS)
    def test_math_entry_has_domain_physics_path(self, math_module_map, domain_id):
        entry = math_module_map[domain_id]
        assert isinstance(entry.get("domain_physics_path"), str)
        assert entry["domain_physics_path"].strip()


class TestModuleMapPhysicsPaths:
    @pytest.mark.parametrize("domain_id", LEGACY_EDU_ACTIVE_MODULE_IDS)
    def test_legacy_domain_physics_path_file_exists(self, edu_module_map, domain_id):
        path_str = edu_module_map[domain_id]["domain_physics_path"]
        assert (REPO_ROOT / path_str).exists()

    @pytest.mark.parametrize("domain_id", MATH_MODULE_IDS)
    def test_math_domain_physics_path_file_exists(self, math_module_map, domain_id):
        path_str = math_module_map[domain_id]["domain_physics_path"]
        assert (REPO_ROOT / path_str).exists()

    @pytest.mark.parametrize("domain_id", MATH_MODULE_IDS)
    def test_math_domain_physics_json_is_valid(self, math_module_map, domain_id):
        path_str = math_module_map[domain_id]["domain_physics_path"]
        data = json.loads((REPO_ROOT / path_str).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data.get("id") == domain_id or data.get("domain_id") == domain_id


class TestMathEvidenceSchemaFiles:
    @pytest.mark.parametrize("domain_id", EXPECTED_SCHEMA_IDS)
    def test_evidence_schema_file_exists(self, domain_id):
        module_dir = MODULE_DIR_MAP[domain_id]
        assert (MATH_MODULES / module_dir / "evidence-schema.json").exists()

    @pytest.mark.parametrize("domain_id", EXPECTED_SCHEMA_IDS)
    def test_evidence_schema_has_correct_schema_id(self, domain_id):
        module_dir = MODULE_DIR_MAP[domain_id]
        data = json.loads((MATH_MODULES / module_dir / "evidence-schema.json").read_text(encoding="utf-8"))
        assert data.get("schema_id") == EXPECTED_SCHEMA_IDS[domain_id]

    @pytest.mark.parametrize("domain_id", EXPECTED_SCHEMA_IDS)
    def test_evidence_schema_has_correct_domain_id(self, domain_id):
        module_dir = MODULE_DIR_MAP[domain_id]
        data = json.loads((MATH_MODULES / module_dir / "evidence-schema.json").read_text(encoding="utf-8"))
        assert data.get("domain_id") == domain_id

    @pytest.mark.parametrize("domain_id", EXPECTED_SCHEMA_IDS)
    def test_evidence_schema_has_fields(self, domain_id):
        module_dir = MODULE_DIR_MAP[domain_id]
        data = json.loads((MATH_MODULES / module_dir / "evidence-schema.json").read_text(encoding="utf-8"))
        assert len(data.get("fields", {})) >= 10

    def test_pre_algebra_has_law2_fields(self):
        data = json.loads((MATH_MODULES / "pre-algebra" / "evidence-schema.json").read_text(encoding="utf-8"))
        fields = data["fields"]
        assert "reversibility_order_correct" in fields
        assert "inequality_direction_correct" in fields

    def test_algebra_intro_has_law3_and_law5_fields(self):
        data = json.loads((MATH_MODULES / "algebra-intro" / "evidence-schema.json").read_text(encoding="utf-8"))
        fields = data["fields"]
        assert "substitution_valid" in fields
        assert "relationship_correctly_mapped" in fields
        assert "reversibility_order_correct" in fields

    def test_algebra_1_has_all_six_law_fields(self):
        data = json.loads((MATH_MODULES / "algebra-1" / "evidence-schema.json").read_text(encoding="utf-8"))
        fields = data["fields"]
        for expected_field in [
            "equivalence_preserved",
            "reversibility_order_correct",
            "inequality_direction_correct",
            "substitution_valid",
            "structure_preserved",
            "relationship_correctly_mapped",
            "model_accurately_transcribed",
        ]:
            assert expected_field in fields


class TestModuleRoutingLogic:
    """Verify module_map lookup overrides the static default."""

    def _resolve_domain_physics_path(self, runtime: dict, profile: dict) -> str:
        default_path = runtime["domain_physics_path"]
        module_map = runtime.get("module_map") or {}
        domain_id = profile.get("domain_id") or profile.get("subject_domain_id")
        if domain_id and domain_id in module_map:
            return module_map[domain_id]["domain_physics_path"]
        return default_path

    def test_legacy_no_domain_id_uses_static_default(self, edu_runtime_cfg):
        result = self._resolve_domain_physics_path(edu_runtime_cfg, {})
        assert result == edu_runtime_cfg["domain_physics_path"]

    def test_legacy_math_id_uses_static_default_until_cutover(self, edu_runtime_cfg):
        profile = {"domain_id": "domain/edu/pre-algebra/v1"}
        result = self._resolve_domain_physics_path(edu_runtime_cfg, profile)
        assert result == edu_runtime_cfg["domain_physics_path"]

    @pytest.mark.parametrize("domain_id", LEGACY_EDU_ACTIVE_MODULE_IDS)
    def test_known_legacy_domain_id_routes_to_module_path(self, edu_runtime_cfg, edu_module_map, domain_id):
        profile = {"domain_id": domain_id}
        result = self._resolve_domain_physics_path(edu_runtime_cfg, profile)
        assert result == edu_module_map[domain_id]["domain_physics_path"]

    @pytest.mark.parametrize("domain_id", MATH_MODULE_IDS)
    def test_known_math_domain_id_routes_to_math_module_path(self, math_runtime_cfg, math_module_map, domain_id):
        profile = {"domain_id": domain_id}
        result = self._resolve_domain_physics_path(math_runtime_cfg, profile)
        assert result == math_module_map[domain_id]["domain_physics_path"]

    def test_math_subject_domain_id_fallback_key(self, math_runtime_cfg):
        profile = {"subject_domain_id": "domain/edumath/algebra-intro/v1"}
        result = self._resolve_domain_physics_path(math_runtime_cfg, profile)
        assert "algebra-intro" in result
