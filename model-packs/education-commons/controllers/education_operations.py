"""Education Commons operation handlers for the admin command pipeline.

This pack owns cross-subject student support operations such as Guardian
relationship assignment. Staff/governance operations live in education-admin.
"""

from __future__ import annotations

from typing import Any

from .ops.guardian_assignments import assign_guardian

_HANDLERS: dict[str, Any] = {
    "assign_guardian": assign_guardian,
}


async def handle_operation(
    operation: str,
    params: dict[str, Any],
    user_data: dict[str, Any],
    ctx: Any,
) -> dict[str, Any] | None:
    handler = _HANDLERS.get(operation)
    if handler is None:
        return None
    return await handler(operation, params, user_data, ctx)
