"""Guardian runtime adapters for education-commons."""

from __future__ import annotations

import json
from typing import Any, Callable


def _strip_markdown_fences(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[: cleaned.rfind("```")]
    return cleaned.strip()


def build_guardian_state(profile: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    module_state = kwargs.get("module_state")
    if isinstance(module_state, dict) and module_state:
        source = module_state
    else:
        source = profile.get("guardian_state") if isinstance(profile, dict) else {}
    source = source if isinstance(source, dict) else {}
    return {
        "turn_count": int(source.get("turn_count", 0)),
        "assigned_children": list(source.get("assigned_children") or []),
        "notification_preferences": dict(source.get("notification_preferences") or {}),
    }


def guardian_domain_step(
    state: dict[str, Any],
    task_spec: dict[str, Any],
    evidence: dict[str, Any],
    params: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state["turn_count"] = int(state.get("turn_count", 0)) + 1
    if evidence.get("requested_write_action"):
        return state, {
            "tier": "critical",
            "action": "notify_read_only_boundary",
            "should_escalate": False,
            "message": "guardian_read_only_boundary",
        }
    return state, {
        "tier": "ok",
        "action": "guardian_query",
        "should_escalate": False,
    }


def interpret_turn_input(
    call_llm: Callable[[str, str, str | None], str],
    input_text: str,
    task_context: dict[str, Any],
    prompt_text: str,
    default_fields: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    raw_response = call_llm(
        system=prompt_text,
        user=f"Guardian message: {input_text}",
        model=None,
    )
    try:
        evidence = json.loads(_strip_markdown_fences(raw_response))
    except (json.JSONDecodeError, IndexError):
        evidence = {}
    defaults = dict(default_fields or {}) or {
        "query_type": "general",
        "target_child_id": None,
        "urgency": "routine",
        "read_only": True,
        "requested_write_action": False,
    }
    for key, value in defaults.items():
        evidence.setdefault(key, value)
    return evidence
