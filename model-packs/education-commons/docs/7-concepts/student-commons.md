---
version: 1.0.0
last_updated: 2026-04-28
---

# Student Commons

The **Student Commons** is owned by the `education-commons` pack.
It is the active journaling, reflection, vocabulary-growth, Safe Person,
and guardian-adjacent support surface for education users who are not in a
subject-specific curriculum module.

## Purpose

- Safe journaling and self-expression
- Interest exploration and learning-goal reflection
- Vocabulary growth tracking
- Safe Person wellness support
- Read-only guardian relationship support and family visibility

## Active Ownership

The active Student Commons runtime lives in:
- `model-packs/education-commons/cfg/runtime-config.yaml`
- `model-packs/education-commons/modules/student-commons/domain-physics.json`
- `model-packs/education-commons/controllers/freeform_adapters.py`
- `model-packs/education-commons/controllers/journal_adapters.py`
- `model-packs/education-commons/controllers/ops/safe_person.py`
- `model-packs/education-commons/controllers/api_handlers.py`

## Runtime Surfaces

Active Student Commons surfaces include:

- vocabulary metric ingestion: `/api/education-commons/user/{user_id}/vocabulary-metric`
- vocabulary dashboard: `/api/education-commons/dashboard/vocabulary-growth`
- Safe Person designation: `/api/education-commons/user/{user_id}/safe-person`
- Safe Person acknowledgement: `/api/education-commons/safe-person/acknowledge`
- Safe Person revocation: `/api/education-commons/user/{user_id}/safe-person`

## Legacy Compatibility

The legacy `education` pack still contains `general-education` as a
compatibility module for old `domain/edu/*` references and cutover fixtures,
but it no longer owns the active Student Commons runtime or API surface.
