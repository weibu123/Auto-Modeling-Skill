#!/usr/bin/env python3
"""Idempotently migrate curated knowledge-base records to Schema v2."""

from __future__ import annotations

import json
from pathlib import Path

from kb_schema import update_metadata, upgrade_method, upgrade_paper, upgrade_subproblem


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"


def load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def save(name: str, payload: dict) -> None:
    (DATA_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def migrate() -> dict[str, int]:
    index = load("paper_index.json")
    index_by_source = {
        Path(record.get("source_pdf") or record.get("team_or_file_id", "")).stem.casefold(): record
        for record in index["records"]
    }

    papers = load("papers.json")
    subproblems = load("subproblems.json")
    methods = load("methods.json")

    papers["records"] = [upgrade_paper(record, index_by_source) for record in papers["records"]]
    subproblems["records"] = [upgrade_subproblem(record) for record in subproblems["records"]]
    methods["records"] = [upgrade_method(record) for record in methods["records"]]

    for payload in (papers, subproblems, methods):
        update_metadata(payload)

    save("papers.json", papers)
    save("subproblems.json", subproblems)
    save("methods.json", methods)
    return {
        "papers": len(papers["records"]),
        "subproblems": len(subproblems["records"]),
        "methods": len(methods["records"]),
    }


if __name__ == "__main__":
    print(json.dumps(migrate(), ensure_ascii=False))
