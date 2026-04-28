"""Deterministic NLP pre-interpreter for the Education Foundation pack."""
from __future__ import annotations

from typing import Any


def nlp_preprocess(input_text: str, task_context: dict[str, Any] | None = None) -> dict[str, Any]:
    text = (input_text or "").lower()
    boundary_terms = ("change threshold", "override policy", "mutate state", "set escalation")
    return {
        "_nlp_anchors": {
            "foundation_reference_request": True,
            "possible_boundary_change": any(term in text for term in boundary_terms),
        }
    }
