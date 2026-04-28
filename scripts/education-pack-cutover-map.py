#!/usr/bin/env python3
"""Education model-pack hard-cutover mapping helper.

This helper is intentionally small and dependency-free. It provides the canonical
old-to-new ID mapping for the education decomposition and can transform JSON
records on stdin for dry-run validation.

It does not rewrite ledgers or commitment records. Use it only for active user
records, active assignments, profile/module state documents, and migration tests.
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = REPO_ROOT / "model-packs" / "education-foundation" / "cfg" / "education-cutover-map.json"


def load_cutover_map(path: Path = MAP_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_id(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [replace_id(item, mapping) for item in value]
    if isinstance(value, dict):
        return {mapping.get(str(key), str(key)): replace_id(item, mapping) for key, item in value.items()}
    return value


def transform_record(record: dict[str, Any], cutover_map: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a migrated copy of an active record.

    The transformation rewrites full module IDs, old education domain keys, and
    pack-level aliases. It is safe for nested profile/module-state documents.
    """
    data = deepcopy(record)
    cutover = cutover_map or load_cutover_map()
    mapping: dict[str, str] = {}
    mapping.update(cutover.get("pack_ids") or {})
    mapping.update(cutover.get("module_ids") or {})
    mapping.update(cutover.get("domain_keys") or {})
    return replace_id(data, mapping)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform JSON records using the education hard-cutover ID map.")
    parser.add_argument("--map", type=Path, default=MAP_PATH, help="Path to education-cutover-map.json.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print transformed JSON.")
    args = parser.parse_args()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"stdin must contain a JSON object or array: {exc}") from exc

    cutover = load_cutover_map(args.map)
    if isinstance(payload, list):
        transformed = [transform_record(item, cutover) if isinstance(item, dict) else item for item in payload]
    elif isinstance(payload, dict):
        transformed = transform_record(payload, cutover)
    else:
        raise SystemExit("stdin must contain a JSON object or array")

    json.dump(transformed, sys.stdout, indent=2 if args.pretty else None, sort_keys=args.pretty)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
