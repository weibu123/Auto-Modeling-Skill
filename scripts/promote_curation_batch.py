#!/usr/bin/env python3
"""Validate and merge a reviewed curation batch into the knowledge base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"
DEFAULT_BATCH_DIR = DATA_DIR / "curation_batches"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def record_key(record: dict, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(record.get(field, "")).strip() for field in fields)


def validate_required(records: list[dict], fields: tuple[str, ...], label: str) -> None:
    seen: set[tuple[str, ...]] = set()
    for record in records:
        key = record_key(record, fields)
        if not all(key):
            raise ValueError(f"{label} record has a blank key: {record}")
        if key in seen:
            raise ValueError(f"Duplicate {label} key in batch: {key}")
        seen.add(key)


def upsert_records(
    payload: dict,
    incoming: list[dict],
    key_fields: tuple[str, ...],
) -> tuple[int, int]:
    records = payload["records"]
    positions = {record_key(record, key_fields): index for index, record in enumerate(records)}
    added = 0
    updated = 0
    for record in incoming:
        key = record_key(record, key_fields)
        if key in positions:
            records[positions[key]] = record
            updated += 1
        else:
            positions[key] = len(records)
            records.append(record)
            added += 1
    return added, updated


def add_batch_metadata(payload: dict, batch: dict) -> None:
    metadata = payload.setdefault("metadata", {})
    metadata["record_count"] = len(payload["records"])
    batch_id = batch["batch_id"]
    batches = metadata.setdefault("curation_batches", [])
    if batch_id not in batches:
        batches.append(batch_id)
    sources = metadata.setdefault("curation_batch_sources", {})
    sources[batch_id] = {
        "source_scope": batch.get("source_scope", ""),
        "evidence_note": batch.get("evidence_note", ""),
    }


def merge_method_sources(methods: dict, updates: list[dict]) -> int:
    changed = 0
    by_name: dict[str, dict] = {}
    for record in methods["records"]:
        method = record["method"]
        if method in by_name:
            raise ValueError(f"Method name is not unique: {method}")
        by_name[method] = record

    for update in updates:
        method = update["method"]
        if method not in by_name:
            raise ValueError(f"Method source update target not found: {method}")
        record = by_name[method]
        existing = [
            value.strip()
            for value in record.get("source_paper_ids", "").split(",")
            if value.strip()
        ]
        merged = list(dict.fromkeys([*existing, *update["source_paper_ids"]]))
        rendered = ",".join(merged)
        if rendered != record.get("source_paper_ids", ""):
            record["source_paper_ids"] = rendered
            changed += 1
    return changed


def validate_batch(batch: dict, current_paper_ids: set[str]) -> None:
    papers = batch.get("papers", [])
    subproblems = batch.get("subproblems", [])
    methods = batch.get("new_methods", [])
    validate_required(papers, ("id",), "paper")
    validate_required(subproblems, ("record_id",), "subproblem")
    validate_required(methods, ("method_family", "method"), "method")

    batch_paper_ids = {record["id"] for record in papers}
    valid_paper_ids = current_paper_ids | batch_paper_ids
    for record in subproblems:
        if record.get("paper_id") not in valid_paper_ids:
            raise ValueError(
                f"Subproblem {record['record_id']} references unknown paper "
                f"{record.get('paper_id')!r}"
            )
    for record in methods:
        source_ids = [
            value.strip()
            for value in record.get("source_paper_ids", "").split(",")
            if value.strip()
        ]
        unknown = set(source_ids) - valid_paper_ids
        if unknown:
            raise ValueError(f"Method {record['method']} has unknown sources: {sorted(unknown)}")


def promote(batch_path: Path) -> dict[str, int]:
    batch = load_json(batch_path)
    batch_id = batch.get("batch_id", "").strip()
    if not batch_id:
        raise ValueError("Batch must define batch_id")

    papers = load_json(DATA_DIR / "papers.json")
    subproblems = load_json(DATA_DIR / "subproblems.json")
    methods = load_json(DATA_DIR / "methods.json")
    current_paper_ids = {record["id"] for record in papers["records"]}
    validate_batch(batch, current_paper_ids)

    paper_added, paper_updated = upsert_records(papers, batch["papers"], ("id",))
    sub_added, sub_updated = upsert_records(
        subproblems,
        batch["subproblems"],
        ("record_id",),
    )
    method_added, method_updated = upsert_records(
        methods,
        batch.get("new_methods", []),
        ("method_family", "method"),
    )
    method_sources_updated = merge_method_sources(
        methods,
        batch.get("method_source_updates", []),
    )

    for payload in (papers, subproblems, methods):
        add_batch_metadata(payload, batch)
    for filename, payload in (
        ("papers.json", papers),
        ("subproblems.json", subproblems),
        ("methods.json", methods),
    ):
        (DATA_DIR / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {
        "papers_added": paper_added,
        "papers_updated": paper_updated,
        "subproblems_added": sub_added,
        "subproblems_updated": sub_updated,
        "methods_added": method_added,
        "methods_updated": method_updated,
        "method_sources_updated": method_sources_updated,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "batch",
        type=Path,
        help=f"Batch JSON path (normally below {DEFAULT_BATCH_DIR.relative_to(ROOT)})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    batch_path = args.batch.expanduser().resolve()
    if not batch_path.is_file():
        raise SystemExit(f"Batch not found: {batch_path}")
    summary = promote(batch_path)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
