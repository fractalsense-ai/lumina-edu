"""Guardian relationship operations owned by education-commons."""

from __future__ import annotations

from typing import Any

from ._helpers import (
    load_profile,
    require_teacher_capability,
    require_user_exists,
    save_profile,
    write_commitment,
)


def _caller_has_student_role(user_data: dict[str, Any]) -> bool:
    domain_roles = user_data.get("domain_roles") or {}
    return any(
        role_id == "student" and (
            module_id == "education-commons"
            or str(module_id).startswith("domain/educom/")
        )
        for module_id, role_id in domain_roles.items()
    )


async def assign_guardian(
    operation: str,
    params: dict[str, Any],
    user_data: dict[str, Any],
    ctx: Any,
) -> dict[str, Any]:
    """Assign a guardian to a student.

    Students can self-assign a guardian without passing ``student_id``.
    Teachers and domain authorities must provide the target student.
    """
    guardian_id = str(params.get("guardian_id", "")).strip()
    student_id = str(params.get("student_id", "")).strip()
    if not guardian_id:
        raise ctx.HTTPException(status_code=422, detail="guardian_id required")

    caller_role = user_data["role"]
    caller_domain_roles = user_data.get("domain_roles") or {}
    if _caller_has_student_role(user_data) or (caller_role == "user" and not caller_domain_roles):
        student_id = user_data["sub"]
    elif caller_role == "user":
        await require_teacher_capability(user_data, ctx)
        if not student_id:
            raise ctx.HTTPException(status_code=422, detail="student_id required for teacher callers")
    elif caller_role in ("root", "admin"):
        if not student_id:
            raise ctx.HTTPException(status_code=422, detail="student_id required for domain authorities")
    else:
        raise ctx.HTTPException(status_code=403, detail="Insufficient permissions")

    guardian_rec = await require_user_exists(ctx, guardian_id, "Guardian")
    guardian_id = guardian_rec["user_id"]

    student_rec = await require_user_exists(ctx, student_id, "Student")
    student_id = student_rec["user_id"]

    student_profile = await load_profile(ctx, student_id)
    guardians = list(student_profile.get("assigned_guardians") or [])
    if guardian_id not in guardians:
        guardians.append(guardian_id)
    student_profile["assigned_guardians"] = guardians
    await save_profile(ctx, student_id, student_profile)

    guardian_profile = await load_profile(ctx, guardian_id)
    guardian_state = guardian_profile.setdefault("guardian_state", {})
    children = list(guardian_state.get("assigned_children") or [])
    if student_id not in children:
        children.append(student_id)
    guardian_state["assigned_children"] = children
    await save_profile(ctx, guardian_id, guardian_profile)

    record = write_commitment(
        ctx,
        actor_id=user_data["sub"],
        actor_role=ctx.map_role_to_actor_role(caller_role),
        commitment_type="guardian_assignment",
        subject_id=student_id,
        summary=f"Assigned guardian {guardian_id} to student {student_id}",
        metadata={
            "guardian_id": guardian_id,
            "student_id": student_id,
            "assigned_by": user_data["sub"],
        },
        references=[guardian_id, student_id],
    )
    return {
        "operation": operation,
        "guardian_id": guardian_id,
        "student_id": student_id,
        "status": "assigned",
        "record_id": record["record_id"],
    }
