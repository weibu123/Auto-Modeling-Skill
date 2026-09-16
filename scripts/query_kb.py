#!/usr/bin/env python3
"""Search the bundled mathematical-modeling knowledge base."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"
FILES = {
    "papers": DATA_DIR / "papers.json",
    "subproblems": DATA_DIR / "subproblems.json",
    "methods": DATA_DIR / "methods.json",
}


def normalize(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def query_terms(query: str) -> list[str]:
    base = [x for x in re.split(r"[\s,，;；/|]+", normalize(query)) if x]
    terms: list[str] = []
    for item in base:
        terms.append(item)
        if re.search(r"[\u4e00-\u9fff]", item) and len(item) >= 4:
            terms.extend(item[i : i + 2] for i in range(len(item) - 1))
    return list(dict.fromkeys(terms))


def load_records(dataset: str) -> list[dict]:
    payload = json.loads(FILES[dataset].read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"Invalid knowledge-base file: {FILES[dataset]}")
    return records


def score_record(record: dict, terms: Iterable[str]) -> int:
    weights = {
        "title": 5,
        "task": 5,
        "method": 5,
        "model": 4,
        "type": 4,
        "pipeline": 3,
        "processing": 3,
        "data": 2,
        "input": 2,
        "strength": 2,
        "risk": 2,
        "validation": 2,
    }
    score = 0
    for key, value in record.items():
        text = normalize(value)
        weight = weights.get(key, 1)
        for term in terms:
            if term and term in text:
                score += weight * (3 if len(term) >= 4 else 1)
    return score


def record_label(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return f'{record.get("id", "")} {record.get("title", "")}'
    if dataset == "subproblems":
        return f'{record.get("paper_id", "")}-问题{record.get("question", "")} {record.get("task", "")}'
    return f'{record.get("method_family", "")} / {record.get("method", "")}'


def record_summary(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return f'{record.get("pipeline", "")}；风险：{record.get("risk", "")}'
    if dataset == "subproblems":
        return (
            f'{record.get("model", "")}；验证：{record.get("validation", "")}；'
            f'风险：{record.get("risk", "")}'
        )
    return f'{record.get("applicable_task", "")}；条件/风险：{record.get("risk", "")}'


def search(
    query: str,
    dataset: str = "all",
    topic: str | None = None,
    limit: int = 8,
) -> list[dict]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if dataset not in {"all", *FILES}:
        raise ValueError(f"unknown dataset: {dataset}")
    if topic and topic.upper() not in set("ABCDEF"):
        raise ValueError("topic must be A-F")
    if limit < 1:
        raise ValueError("limit must be positive")

    datasets = list(FILES) if dataset == "all" else [dataset]
    terms = query_terms(query)
    hits: list[dict] = []
    for dataset_name in datasets:
        for record in load_records(dataset_name):
            if topic:
                record_topic = normalize(record.get("topic") or record.get("paper_id", "")[:1])
                if record_topic[:1] != topic.lower():
                    continue
            score = score_record(record, terms)
            if score:
                hits.append({"dataset": dataset_name, "score": score, "record": record})

    hits.sort(key=lambda x: (-x["score"], record_label(x["dataset"], x["record"])))
    return hits[:limit]


def render_markdown(hits: list[dict]) -> str:
    lines = [
        "| 数据集 | 分数 | 记录 | 方法链与风险 |",
        "| --- | ---: | --- | --- |",
    ]
    for hit in hits:
        dataset, record = hit["dataset"], hit["record"]
        left = record_label(dataset, record).replace("|", "/").replace("\n", " ")
        right = record_summary(dataset, record).replace("|", "/").replace("\n", " ")
        lines.append(f'| {dataset} | {hit["score"]} | {left} | {right} |')
    if not hits:
        lines.append("| - | - | 未找到匹配记录 | 请调整任务、数据、约束或风险关键词 |")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the bundled paper, subproblem, and method records.")
    parser.add_argument("--query", required=True, help="Task, data, method, constraint, or risk keywords")
    parser.add_argument("--dataset", choices=["all", *FILES], default="all")
    parser.add_argument("--topic", choices=list("ABCDEF"), help="Optional competition topic letter")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    hits = search(args.query, args.dataset, args.topic, args.limit)
    if args.as_json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
