#!/usr/bin/env python3
"""Search the curated Huawei Cup modeling knowledge base without dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


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
    return payload["records"]


def score_record(record: dict, terms: list[str]) -> int:
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


def label(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return f'{record.get("id", "")} {record.get("title", "")}'
    if dataset == "subproblems":
        return f'{record.get("paper_id", "")}-问题{record.get("question", "")} {record.get("task", "")}'
    return f'{record.get("method_family", "")} / {record.get("method", "")}'


def summary(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return f'{record.get("pipeline", "")}；风险：{record.get("risk", "")}'
    if dataset == "subproblems":
        return f'{record.get("model", "")}；验证：{record.get("validation", "")}；风险：{record.get("risk", "")}'
    return f'{record.get("applicable_task", "")}；条件/风险：{record.get("risk", "")}'


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Huawei Cup paper, subproblem, and method records.")
    parser.add_argument("--query", required=True, help="Keywords describing the task, data, method, or risk")
    parser.add_argument("--dataset", choices=["all", *FILES], default="all")
    parser.add_argument("--topic", help="Optional topic letter A-F")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    datasets = list(FILES) if args.dataset == "all" else [args.dataset]
    terms = query_terms(args.query)
    hits: list[dict] = []
    for dataset in datasets:
        for record in load_records(dataset):
            if args.topic:
                topic = normalize(record.get("topic") or record.get("paper_id", "")[:1])
                if topic[:1] != args.topic.lower()[:1]:
                    continue
            score = score_record(record, terms)
            if score:
                hits.append({"dataset": dataset, "score": score, "record": record})

    hits.sort(key=lambda x: (-x["score"], label(x["dataset"], x["record"])))
    hits = hits[: max(1, args.limit)]
    if args.as_json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return

    print("| 数据集 | 分数 | 记录 | 方法链与风险 |")
    print("| --- | ---: | --- | --- |")
    for hit in hits:
        dataset, record = hit["dataset"], hit["record"]
        left = label(dataset, record).replace("|", "/")
        right = summary(dataset, record).replace("|", "/")
        print(f'| {dataset} | {hit["score"]} | {left} | {right} |')


if __name__ == "__main__":
    main()
