#!/usr/bin/env python3
"""Evaluate knowledge-base retrieval against reviewed top-k expectations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from query_kb import search


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "evals" / "retrieval_cases.json"


def evaluate(path: Path = DEFAULT_CASES) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results: list[dict] = []
    reciprocal_ranks: list[float] = []
    passes = 0
    for case in payload["cases"]:
        hits = search(
            case["query"],
            case.get("dataset", "all"),
            case.get("topic"),
            case.get("year"),
            case.get("k", 5),
        )
        returned = [hit["record_id"] for hit in hits]
        expected = set(case["expected_ids"])
        rank = next(
            (position for position, record_id in enumerate(returned, start=1) if record_id in expected),
            None,
        )
        reciprocal_rank = 1.0 / rank if rank else 0.0
        reciprocal_ranks.append(reciprocal_rank)
        if rank:
            passes += 1
        results.append(
            {
                "id": case["id"],
                "passed": bool(rank),
                "rank": rank,
                "expected_ids": case["expected_ids"],
                "returned_ids": returned,
            }
        )

    case_count = len(results)
    recall = passes / case_count if case_count else 0.0
    mrr = sum(reciprocal_ranks) / case_count if case_count else 0.0
    return {
        "case_count": case_count,
        "recall_at_k": round(recall, 4),
        "mrr": round(mrr, 4),
        "minimum_recall_at_k": payload["minimum_recall_at_k"],
        "minimum_mrr": payload["minimum_mrr"],
        "passed": recall >= payload["minimum_recall_at_k"] and mrr >= payload["minimum_mrr"],
        "results": results,
    }


def render(report: dict) -> str:
    lines = [
        "| 案例 | 通过 | 首个相关位次 | 返回记录 |",
        "| --- | --- | ---: | --- |",
    ]
    for result in report["results"]:
        returned = ", ".join(result["returned_ids"][:5])
        lines.append(
            f'| {result["id"]} | {"PASS" if result["passed"] else "FAIL"} | '
            f'{result["rank"] or "-"} | {returned} |'
        )
    lines.append("")
    lines.append(
        f'Recall@k={report["recall_at_k"]:.4f}，MRR={report["mrr"]:.4f}，'
        f'总体={"PASS" if report["passed"] else "FAIL"}。'
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = evaluate(args.cases)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.as_json else render(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
