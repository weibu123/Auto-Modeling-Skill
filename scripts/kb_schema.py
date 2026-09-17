#!/usr/bin/env python3
"""Shared Schema v2 helpers for the distilled knowledge base."""

from __future__ import annotations

import re
from pathlib import Path


SCHEMA_VERSION = 2

PAPER_REQUIRED = (
    "id",
    "topic",
    "year",
    "title",
    "type",
    "data",
    "pipeline",
    "validation",
    "reported_result",
    "strength",
    "risk",
    "evidence",
    "source_file",
    "problem_archetypes",
    "data_structure",
    "models",
    "validation_design",
    "failure_modes",
    "evidence_locations",
    "evidence_level",
    "record_version",
)

SUBPROBLEM_REQUIRED = (
    "record_id",
    "paper_id",
    "question",
    "task",
    "input",
    "processing",
    "model",
    "output",
    "validation",
    "risk",
    "objective",
    "constraints",
    "metric",
    "split_unit",
    "assumptions",
    "failure_modes",
    "upstream_dependencies",
    "downstream_outputs",
    "implementation_artifacts",
    "evidence_level",
    "record_version",
)

METHOD_REQUIRED = (
    "method_family",
    "method",
    "applicable_task",
    "required_data",
    "core_idea",
    "advantage",
    "risk",
    "source_paper_ids",
    "must_check",
    "minimum_baseline",
    "forbidden_when",
    "recommended_alternatives",
    "computational_complexity",
    "common_misuse",
    "evidence_level",
    "record_version",
)

LIST_FIELDS = {
    "problem_archetypes",
    "data_structure",
    "models",
    "validation_design",
    "failure_modes",
    "evidence_locations",
    "constraints",
    "metric",
    "assumptions",
    "upstream_dependencies",
    "downstream_outputs",
    "implementation_artifacts",
    "must_check",
    "forbidden_when",
    "recommended_alternatives",
    "common_misuse",
    "decision_field_sources",
}


def split_segments(value: object) -> list[str]:
    """Split reviewed prose into coarse, traceable structured segments."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return []
    parts = [part.strip(" .。") for part in re.split(r"[;；]", text)]
    return list(dict.fromkeys(part for part in parts if part))


def paper_source_key(record: dict) -> str:
    return Path(str(record.get("source_file", ""))).stem.casefold()


def parse_source_ids(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def normalize_source_ids(value: object) -> tuple[list[str], list[str]]:
    """Expand compact ID ranges and separate non-traceable legacy notes."""
    normalized: list[str] = []
    notes: list[str] = []
    for source in parse_source_ids(value):
        range_match = re.fullmatch(r"([A-Z])(\d+)-([A-Z]?)(\d+)", source)
        if range_match:
            start_prefix, start_number, end_prefix, end_number = range_match.groups()
            end_prefix = end_prefix or start_prefix
            if start_prefix == end_prefix and int(start_number) <= int(end_number):
                width = max(len(start_number), len(end_number))
                normalized.extend(
                    f"{start_prefix}{number:0{width}d}"
                    for number in range(int(start_number), int(end_number) + 1)
                )
                continue
        if re.fullmatch(r"[A-Z][A-Za-z0-9-]*\d+", source):
            normalized.append(source)
        else:
            notes.append(source)
    return list(dict.fromkeys(normalized)), list(dict.fromkeys(notes))


def upgrade_paper(record: dict, index_by_source: dict[str, dict]) -> dict:
    upgraded = dict(record)
    index_record = index_by_source.get(paper_source_key(record), {})
    year = upgraded.get("year") or index_record.get("year")
    if year is not None:
        upgraded["year"] = int(year)
    upgraded.setdefault("variant_label", upgraded.get("type", ""))
    upgraded.setdefault("problem_archetypes", split_segments(upgraded.get("type")))
    upgraded.setdefault("data_structure", [upgraded["data"]] if upgraded.get("data") else [])
    upgraded.setdefault("models", split_segments(upgraded.get("pipeline")))
    upgraded.setdefault("validation_design", split_segments(upgraded.get("validation")))
    upgraded.setdefault("failure_modes", split_segments(upgraded.get("risk")))
    upgraded.setdefault("evidence_locations", split_segments(upgraded.get("evidence")))
    upgraded["evidence_level"] = "deeply_curated"
    upgraded["record_version"] = SCHEMA_VERSION
    return upgraded


def upgrade_subproblem(record: dict) -> dict:
    upgraded = dict(record)
    upgraded.setdefault("objective", upgraded.get("task", ""))
    upgraded.setdefault("constraints", [])
    upgraded.setdefault("metric", [])
    upgraded.setdefault("split_unit", "")
    upgraded.setdefault("assumptions", [])
    upgraded.setdefault("failure_modes", split_segments(upgraded.get("risk")))
    upgraded.setdefault("upstream_dependencies", [])
    upgraded.setdefault(
        "downstream_outputs",
        [upgraded["output"]] if upgraded.get("output") else [],
    )
    upgraded.setdefault("implementation_artifacts", [])
    upgraded["evidence_level"] = "deeply_curated"
    upgraded["record_version"] = SCHEMA_VERSION
    return upgraded


def upgrade_method(record: dict) -> dict:
    upgraded = dict(record)
    sources, notes = normalize_source_ids(upgraded.get("source_paper_ids"))
    upgraded["source_paper_ids"] = ",".join(sources)
    if notes:
        upgraded["source_note"] = "Legacy non-specific provenance: " + ", ".join(notes)
    upgraded.setdefault("must_check", split_segments(upgraded.get("risk")))
    upgraded.setdefault("minimum_baseline", "")
    upgraded.setdefault("forbidden_when", [])
    upgraded.setdefault("recommended_alternatives", [])
    upgraded.setdefault("computational_complexity", "")
    upgraded.setdefault("common_misuse", [])
    upgraded["evidence_level"] = "deeply_curated"
    upgraded["record_version"] = SCHEMA_VERSION
    return upgraded


def update_metadata(payload: dict) -> None:
    metadata = payload.setdefault("metadata", {})
    metadata["schema_version"] = SCHEMA_VERSION
    metadata["record_count"] = len(payload.get("records", []))
