"""Deterministic NLP pre-interpreter for the Education Presentation pack."""
from __future__ import annotations

from typing import Any


def nlp_preprocess(input_text: str, task_context: dict[str, Any] | None = None) -> dict[str, Any]:
    text = (input_text or "").lower()
    logic_terms = ("change threshold", "override physics", "change escalation", "mutate state")
    consent_terms = ("hide consent", "skip consent", "obscure consent")
    return {
        "_nlp_anchors": {
            "presentation_reference_request": True,
            "possible_logic_override": any(term in text for term in logic_terms),
            "possible_consent_boundary_issue": any(term in text for term in consent_terms),
        }
    }
