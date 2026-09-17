#!/usr/bin/env python3
"""Validate links, types, provenance, and Schema v2 coverage."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from kb_schema import (
    LIST_FIELDS,
    METHOD_REQUIRED,
    PAPER_REQUIRED,
    SCHEMA_VERSION,
    SUBPROBLEM_REQUIRED,
    parse_source_ids,
)


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"


@dataclass(frozen=True)
class Finding:
    level: str
    dataset: str
    record: str
    detail: str


def load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def validate_required(
    dataset: str,
    records: list[dict],
    fields: tuple[str, ...],
    identity: str,
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()
    for position, record in enumerate(records, start=1):
        record_id = str(record.get(identity) or f"row-{position}")
        if record_id in seen:
            findings.append(Finding("FAIL", dataset, record_id, "duplicate identity"))
        seen.add(record_id)
        missing = [field for field in fields if field not in record]
        if missing:
            findings.append(
                Finding("FAIL", dataset, record_id, "missing fields: " + ", ".join(missing))
            )
        wrong_lists = [field for field in LIST_FIELDS if field in record and not isinstance(record[field], list)]
        if wrong_lists:
            findings.append(
                Finding("FAIL", dataset, record_id, "non-list fields: " + ", ".join(wrong_lists))
            )
        if record.get("record_version") != SCHEMA_VERSION:
            findings.append(Finding("FAIL", dataset, record_id, "record_version is not 2"))
        if record.get("evidence_level") != "deeply_curated":
            findings.append(Finding("FAIL", dataset, record_id, "invalid evidence_level"))
    return findings


def validate() -> tuple[list[Finding], dict[str, object]]:
    papers_payload = load("papers.json")
    subproblems_payload = load("subproblems.json")
    methods_payload = load("methods.json")
    index_payload = load("paper_index.json")
    datasets = {
        "papers": papers_payload,
        "subproblems": subproblems_payload,
        "methods": methods_payload,
    }
    findings: list[Finding] = []

    for name, payload in datasets.items():
        if payload.get("metadata", {}).get("schema_version") != SCHEMA_VERSION:
            findings.append(Finding("FAIL", name, "metadata", "schema_version is not 2"))
        if payload.get("metadata", {}).get("record_count") != len(payload.get("records", [])):
            findings.append(Finding("FAIL", name, "metadata", "record_count mismatch"))

    papers = papers_payload["records"]
    subproblems = subproblems_payload["records"]
    methods = methods_payload["records"]
    subproblems_by_id = {record["record_id"]: record for record in subproblems}
    methods_by_id = {record["method"]: record for record in methods}
    findings.extend(validate_required("papers", papers, PAPER_REQUIRED, "id"))
    findings.extend(
        validate_required("subproblems", subproblems, SUBPROBLEM_REQUIRED, "record_id")
    )
    findings.extend(validate_required("methods", methods, METHOD_REQUIRED, "method"))

    paper_ids = {record["id"] for record in papers}
    for record in papers:
        if not isinstance(record.get("year"), int):
            findings.append(Finding("FAIL", "papers", record["id"], "year must be an integer"))
    for record in subproblems:
        if record.get("paper_id") not in paper_ids:
            findings.append(
                Finding("FAIL", "subproblems", record["record_id"], "unknown paper_id")
            )
    for record in methods:
        unknown = set(parse_source_ids(record.get("source_paper_ids"))) - paper_ids
        if unknown:
            findings.append(
                Finding("FAIL", "methods", record["method"], "unknown sources: " + ", ".join(sorted(unknown)))
            )

    curated_index_ids = {
        record.get("curated_paper_id")
        for record in index_payload["records"]
        if record.get("distillation_status") == "curated"
    }
    if curated_index_ids != paper_ids:
        missing = sorted(paper_ids - curated_index_ids)
        extra = sorted(curated_index_ids - paper_ids)
        findings.append(
            Finding("FAIL", "paper_index", "curated links", f"missing={missing}; extra={extra}")
        )

    decision_paths = sorted((DATA_DIR / "decision_fields").glob("*.json"))
    decision_batches = [json.loads(path.read_text(encoding="utf-8")) for path in decision_paths]
    decision_ids = {
        batch.get("batch_id")
        for batch in decision_batches
        if isinstance(batch.get("batch_id"), str) and batch.get("batch_id")
    }
    if len(decision_ids) != len(decision_batches):
        findings.append(Finding("FAIL", "decision_fields", "metadata", "missing or duplicate batch_id"))
    for dataset_name, payload in (
        ("subproblems", subproblems_payload),
        ("methods", methods_payload),
    ):
        applied = set(payload.get("metadata", {}).get("decision_field_batches", []))
        if applied != decision_ids:
            findings.append(
                Finding(
                    "FAIL",
                    dataset_name,
                    "decision_field_batches",
                    f"applied={sorted(applied)}; files={sorted(decision_ids)}",
                )
            )

    for batch in decision_batches:
        batch_id = batch.get("batch_id")
        if batch_id not in decision_ids:
            continue
        for item in batch.get("subproblems", []):
            record = subproblems_by_id.get(item.get("record_id"))
            if record is None:
                findings.append(Finding("FAIL", "decision_fields", item.get("record_id", ""), "unknown subproblem"))
                continue
            for field, expected in item.items():
                if field != "record_id" and record.get(field) != expected:
                    findings.append(Finding("FAIL", "decision_fields", item["record_id"], f"drifted field: {field}"))
            if record.get("decision_field_sources") != [batch_id]:
                findings.append(Finding("FAIL", "decision_fields", item["record_id"], "missing batch provenance"))
        for item in batch.get("methods", []):
            record = methods_by_id.get(item.get("method"))
            if record is None:
                findings.append(Finding("FAIL", "decision_fields", item.get("method", ""), "unknown method"))
                continue
            for field, expected in item.items():
                if field != "method" and record.get(field) != expected:
                    findings.append(Finding("FAIL", "decision_fields", item["method"], f"drifted field: {field}"))
            if record.get("decision_field_sources") != [batch_id]:
                findings.append(Finding("FAIL", "decision_fields", item["method"], "missing batch provenance"))

    empty_metrics = sum(not record.get("metric") for record in subproblems)
    empty_constraints = sum(not record.get("constraints") for record in subproblems)
    empty_baselines = sum(not record.get("minimum_baseline") for record in methods)
    for label, count, total in (
        ("subproblem metrics", empty_metrics, len(subproblems)),
        ("subproblem constraints", empty_constraints, len(subproblems)),
        ("method baselines", empty_baselines, len(methods)),
    ):
        if count:
            findings.append(Finding("WARN", "coverage", label, f"empty {count}/{total}"))

    summary = {
        "schema_version": SCHEMA_VERSION,
        "records": {name: len(payload["records"]) for name, payload in datasets.items()},
        "failures": sum(item.level == "FAIL" for item in findings),
        "warnings": sum(item.level == "WARN" for item in findings),
        "coverage_gaps": {
            "empty_subproblem_metrics": empty_metrics,
            "empty_subproblem_constraints": empty_constraints,
            "empty_method_baselines": empty_baselines,
        },
        "decision_field_batches": sorted(decision_ids),
    }
    return findings, summary


def render(findings: list[Finding], summary: dict[str, object]) -> str:
    lines = [
        "| 级别 | 数据集 | 记录 | 详情 |",
        "| --- | --- | --- | --- |",
    ]
    for item in findings:
        lines.append(f"| {item.level} | {item.dataset} | {item.record} | {item.detail} |")
    if not findings:
        lines.append("| PASS | all | - | Schema v2 and cross-reference checks passed |")
    lines.append("")
    lines.append(
        f"汇总：FAIL {summary['failures']}，WARN {summary['warnings']}，"
        f"Schema v{summary['schema_version']}。"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat coverage warnings as failure")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    findings, summary = validate()
    if args.as_json:
        print(json.dumps({"summary": summary, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(render(findings, summary))
    if summary["failures"]:
        return 2
    if args.strict and summary["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
