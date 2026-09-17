#!/usr/bin/env python3
"""Apply reviewed decision-field batches to Schema v2 knowledge records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"
BATCH_DIR = DATA_DIR / "decision_fields"

SUBPROBLEM_FIELDS = {"constraints", "metric", "split_unit", "assumptions", "decision_field_quality"}
METHOD_FIELDS = {
    "minimum_baseline",
    "forbidden_when",
    "recommended_alternatives",
    "computational_complexity",
    "common_misuse",
}
LIST_FIELDS = {
    "constraints",
    "metric",
    "assumptions",
    "forbidden_when",
    "recommended_alternatives",
    "common_misuse",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_text_list(batch_id: str, identity: str, field: str, value: object) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{batch_id}:{identity} {field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{batch_id}:{identity} {field} contains empty/non-text values")


def validate_batch(batch: dict, path: Path) -> None:
    batch_id = batch.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id:
        raise ValueError(f"{path}: missing batch_id")
    if not batch.get("evidence_basis"):
        raise ValueError(f"{batch_id}: missing evidence_basis")

    subproblems = batch.get("subproblems")
    methods = batch.get("methods")
    if not isinstance(subproblems, list) or not isinstance(methods, list):
        raise ValueError(f"{batch_id}: subproblems and methods must be lists")

    sub_ids = [str(item.get("record_id", "")) for item in subproblems]
    method_ids = [str(item.get("method", "")) for item in methods]
    if "" in sub_ids or len(sub_ids) != len(set(sub_ids)):
        raise ValueError(f"{batch_id}: empty or duplicate subproblem identity")
    if "" in method_ids or len(method_ids) != len(set(method_ids)):
        raise ValueError(f"{batch_id}: empty or duplicate method identity")

    for item in subproblems:
        unknown = set(item) - ({"record_id"} | SUBPROBLEM_FIELDS)
        if unknown:
            raise ValueError(f"{batch_id}:{item['record_id']} unknown fields: {sorted(unknown)}")
        for required in ("constraints", "metric"):
            validate_text_list(batch_id, item["record_id"], required, item.get(required))
        for field in set(item) & LIST_FIELDS:
            validate_text_list(batch_id, item["record_id"], field, item[field])

    for item in methods:
        unknown = set(item) - ({"method"} | METHOD_FIELDS)
        if unknown:
            raise ValueError(f"{batch_id}:{item['method']} unknown fields: {sorted(unknown)}")
        if not isinstance(item.get("minimum_baseline"), str) or not item["minimum_baseline"].strip():
            raise ValueError(f"{batch_id}:{item['method']} missing minimum_baseline")
        for required in ("forbidden_when", "recommended_alternatives", "common_misuse"):
            validate_text_list(batch_id, item["method"], required, item.get(required))
        if "computational_complexity" in item and not isinstance(item["computational_complexity"], str):
            raise ValueError(f"{batch_id}:{item['method']} computational_complexity must be text")


def apply_batches(batch_paths: list[Path], *, write: bool = True) -> dict[str, object]:
    sub_path = DATA_DIR / "subproblems.json"
    method_path = DATA_DIR / "methods.json"
    sub_payload = load_json(sub_path)
    method_payload = load_json(method_path)
    sub_by_id = {item["record_id"]: item for item in sub_payload["records"]}
    method_by_id = {item["method"]: item for item in method_payload["records"]}

    batches = []
    seen_subproblems: set[str] = set()
    seen_methods: set[str] = set()
    for path in sorted(batch_paths):
        batch = load_json(path)
        validate_batch(batch, path)
        batch_id = batch["batch_id"]
        batches.append(batch_id)
        for item in batch["subproblems"]:
            record_id = item["record_id"]
            if record_id not in sub_by_id:
                raise ValueError(f"{batch_id}: unknown subproblem {record_id}")
            if record_id in seen_subproblems:
                raise ValueError(f"{record_id} is overridden by multiple decision batches")
            existing_sources = sub_by_id[record_id].get("decision_field_sources", [])
            if existing_sources and existing_sources != [batch_id]:
                raise ValueError(f"{record_id} already belongs to {existing_sources}")
            seen_subproblems.add(record_id)
            sub_by_id[record_id].update({key: value for key, value in item.items() if key != "record_id"})
            sub_by_id[record_id]["decision_field_sources"] = [batch_id]

        for item in batch["methods"]:
            method = item["method"]
            if method not in method_by_id:
                raise ValueError(f"{batch_id}: unknown method {method}")
            if method in seen_methods:
                raise ValueError(f"{method} is overridden by multiple decision batches")
            existing_sources = method_by_id[method].get("decision_field_sources", [])
            if existing_sources and existing_sources != [batch_id]:
                raise ValueError(f"{method} already belongs to {existing_sources}")
            seen_methods.add(method)
            method_by_id[method].update({key: value for key, value in item.items() if key != "method"})
            method_by_id[method]["decision_field_sources"] = [batch_id]

    for payload in (sub_payload, method_payload):
        metadata = payload.setdefault("metadata", {})
        applied = set(metadata.get("decision_field_batches", [])) | set(batches)
        metadata["decision_field_batches"] = sorted(applied)
        metadata["decision_field_batch_count"] = len(applied)

    if write:
        sub_path.write_text(json.dumps(sub_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        method_path.write_text(json.dumps(method_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "batches": batches,
        "subproblems_updated": len(seen_subproblems),
        "methods_updated": len(seen_methods),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batches", nargs="*", type=Path, help="Batch JSON paths; defaults to all reviewed batches")
    parser.add_argument("--check", action="store_true", help="Validate and simulate without writing datasets")
    args = parser.parse_args()
    paths = args.batches or sorted(BATCH_DIR.glob("*.json"))
    if not paths:
        parser.error("no decision-field batches found")
    report = apply_batches([path.resolve() for path in paths], write=not args.check)
    mode = "validated" if args.check else "applied"
    print(
        f"Decision fields {mode}: {len(report['batches'])} batches, "
        f"{report['subproblems_updated']} subproblems, {report['methods_updated']} methods."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
