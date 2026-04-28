"""Deterministic Guardian NLP anchors for education-commons."""

from __future__ import annotations

import re
from typing import Any

_WRITE_RE = re.compile(r"\b(assign|change|modify|delete|resolve|hint|intervene|unlock)\b", re.IGNORECASE)
_PROGRESS_RE = re.compile(r"\b(progress|grade|module|lesson|status|report)\b", re.IGNORECASE)
_CONSENT_RE = re.compile(r"\b(consent|permission|guardian|parent|child)\b", re.IGNORECASE)


def guardian_nlp_preprocess(input_text: str, task_context: dict[str, Any] | None = None) -> dict[str, Any]:
    anchors: list[dict[str, Any]] = []
    if _WRITE_RE.search(input_text):
        anchors.append({
            "field": "requested_write_action",
            "value": True,
            "confidence": 0.8,
            "detail": "Guardian request appears to ask for a state-changing action.",
        })
    if _PROGRESS_RE.search(input_text):
        anchors.append({
            "field": "query_type",
            "value": "child_progress",
            "confidence": 0.75,
            "detail": "Guardian request mentions progress or module status.",
        })
    if _CONSENT_RE.search(input_text):
        anchors.append({
            "field": "query_type",
            "value": "consent_status",
            "confidence": 0.7,
            "detail": "Guardian request mentions consent or relationship status.",
        })
    return {"_nlp_anchors": anchors}
