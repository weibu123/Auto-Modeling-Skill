#!/usr/bin/env python3
"""Hybrid lexical/BM25 search for the modeling knowledge base."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"
FILES = {
    "papers": DATA_DIR / "papers.json",
    "subproblems": DATA_DIR / "subproblems.json",
    "methods": DATA_DIR / "methods.json",
    "index": DATA_DIR / "paper_index.json",
}

FIELD_WEIGHTS = {
    "title": 5,
    "variant_label": 4,
    "task": 5,
    "objective": 5,
    "method": 5,
    "model": 4,
    "models": 4,
    "type": 4,
    "problem_archetypes": 4,
    "pipeline": 3,
    "processing": 3,
    "data": 2,
    "data_structure": 3,
    "input": 2,
    "strength": 2,
    "risk": 3,
    "failure_modes": 3,
    "validation": 2,
    "validation_design": 2,
    "constraints": 4,
    "metric": 3,
    "assumptions": 2,
    "minimum_baseline": 4,
    "forbidden_when": 4,
    "recommended_alternatives": 3,
    "common_misuse": 4,
    "computational_complexity": 2,
    "abstract": 4,
    "keywords": 4,
    "content_excerpt": 2,
    "team_or_file_id": 1,
}


def normalize(text: object) -> str:
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def tokenize(text: object) -> list[str]:
    """Tokenize Latin terms and Chinese runs without external dependencies."""
    tokens: list[str] = []
    for chunk in re.findall(r"[a-z0-9_.+\-]+|[一-鿿]+", normalize(text)):
        if re.fullmatch(r"[一-鿿]+", chunk):
            if len(chunk) <= 12:
                tokens.append(chunk)
            if len(chunk) == 1:
                tokens.append(chunk)
            else:
                tokens.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
        else:
            tokens.append(chunk)
    return tokens


def query_terms(query: str) -> list[str]:
    base = [part for part in re.split(r"[\s,，;；/|]+", normalize(query)) if part]
    terms: list[str] = []
    for item in base:
        terms.append(item)
        if re.search(r"[一-鿿]", item) and len(item) >= 4:
            terms.extend(item[index : index + 2] for index in range(len(item) - 1))
    return list(dict.fromkeys(terms))


def load_records(dataset: str) -> list[dict]:
    payload = json.loads(FILES[dataset].read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"Invalid knowledge-base file: {FILES[dataset]}")
    return records


def searchable_fields(record: dict) -> dict[str, str]:
    return {
        key: normalize(value)
        for key, value in record.items()
        if value not in (None, "", []) and key not in {"sha256", "text_characters"}
    }


def weighted_document_tokens(record: dict) -> list[str]:
    result: list[str] = []
    for field, text in searchable_fields(record).items():
        repetitions = max(1, FIELD_WEIGHTS.get(field, 1) // 2)
        result.extend(tokenize(text) * repetitions)
    return result


def exact_score(record: dict, terms: Iterable[str]) -> int:
    score = 0
    for key, text in searchable_fields(record).items():
        weight = FIELD_WEIGHTS.get(key, 1)
        for term in terms:
            if term and term in text:
                score += weight * (3 if len(term) >= 4 else 1)
    return score


def bm25_scores(records: list[dict], query_tokens: list[str]) -> list[float]:
    if not records:
        return []
    documents = [weighted_document_tokens(record) for record in records]
    counters = [Counter(document) for document in documents]
    lengths = [len(document) for document in documents]
    average_length = sum(lengths) / len(lengths) if lengths else 1.0
    document_frequency = {
        term: sum(term in counter for counter in counters)
        for term in set(query_tokens)
    }
    k1, b = 1.5, 0.75
    scores: list[float] = []
    for counter, length in zip(counters, lengths):
        score = 0.0
        for term in query_tokens:
            frequency = counter.get(term, 0)
            if not frequency:
                continue
            df = document_frequency[term]
            inverse_document_frequency = math.log(
                1 + (len(records) - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + k1 * (
                1 - b + b * length / max(average_length, 1.0)
            )
            score += inverse_document_frequency * frequency * (k1 + 1) / denominator
        scores.append(score)
    return scores


def matched_fields(record: dict, terms: list[str], query_tokens: list[str]) -> list[str]:
    matched: list[str] = []
    token_set = set(query_tokens)
    for field, text in searchable_fields(record).items():
        if any(term in text for term in terms) or token_set.intersection(tokenize(text)):
            matched.append(field)
    return sorted(matched, key=lambda field: (-FIELD_WEIGHTS.get(field, 1), field))


def record_id(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return str(record.get("id", ""))
    if dataset == "subproblems":
        return str(record.get("record_id", ""))
    if dataset == "methods":
        return str(record.get("method", ""))
    return str(record.get("uid", ""))


def record_label(dataset: str, record: dict) -> str:
    if dataset == "papers":
        variant = record.get("variant_label", "")
        suffix = f" [{variant}]" if variant else ""
        return f'{record.get("id", "")} {record.get("title", "")}{suffix}'
    if dataset == "index":
        return (
            f'{record.get("year", "")} {record.get("topic", "")}题 '
            f'{record.get("title", "")} [{record.get("team_or_file_id", "")}]'
        )
    if dataset == "subproblems":
        return f'{record.get("paper_id", "")}-问题{record.get("question", "")} {record.get("task", "")}'
    return f'{record.get("method_family", "")} / {record.get("method", "")}'


def compact_list(value: object, limit: int = 2) -> str:
    if not isinstance(value, list):
        return normalize(value)
    items = [normalize(item) for item in value if normalize(item)]
    suffix = "；…" if len(items) > limit else ""
    return "；".join(items[:limit]) + suffix


def record_summary(dataset: str, record: dict) -> str:
    if dataset == "papers":
        return f'{record.get("pipeline", "")}；风险：{record.get("risk", "")}'
    if dataset == "index":
        flags = ",".join(record.get("quality_flags") or []) or "无"
        keywords = record.get("keywords") or "未提取"
        return (
            f'状态：{record.get("distillation_status", "indexed")}；'
            f'关键词：{keywords}；质量标记：{flags}'
        )
    if dataset == "subproblems":
        constraints = compact_list(record.get("constraints")) or "待补"
        metrics = compact_list(record.get("metric")) or "待补"
        return (
            f'{record.get("model", "")}；约束：{constraints}；指标：{metrics}；'
            f'验证：{record.get("validation", "")}；风险：{record.get("risk", "")}'
        )
    baseline = record.get("minimum_baseline") or "待补"
    forbidden = compact_list(record.get("forbidden_when")) or "待补"
    return (
        f'{record.get("applicable_task", "")}；最低基线：{baseline}；'
        f'禁用条件：{forbidden}；条件/风险：{record.get("risk", "")}'
    )


def search(
    query: str,
    dataset: str = "all",
    topic: str | None = None,
    year: int | None = None,
    limit: int = 8,
) -> list[dict]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if dataset not in {"all", *FILES}:
        raise ValueError(f"unknown dataset: {dataset}")
    if topic and topic.upper() not in set("ABCDEF"):
        raise ValueError("topic must be A-F")
    if year is not None and not 2000 <= year <= 2100:
        raise ValueError("year must be between 2000 and 2100")
    if limit < 1:
        raise ValueError("limit must be positive")

    selected_datasets = list(FILES) if dataset == "all" else [dataset]
    terms = query_terms(query)
    tokens = list(dict.fromkeys(tokenize(query)))
    hits: list[dict] = []
    for dataset_name in selected_datasets:
        candidates: list[dict] = []
        for record in load_records(dataset_name):
            if dataset == "all" and dataset_name == "index":
                if record.get("distillation_status") == "curated":
                    continue
            if topic:
                record_topic = normalize(record.get("topic") or record.get("paper_id", "")[:1])
                if record_topic[:1] != topic.lower():
                    continue
            if year is not None and record.get("year") != year:
                continue
            candidates.append(record)

        for record, bm25_score in zip(candidates, bm25_scores(candidates, tokens)):
            phrase_score = exact_score(record, terms)
            score = phrase_score + 5.0 * bm25_score
            if score <= 0:
                continue
            fields = matched_fields(record, terms, tokens)
            hits.append(
                {
                    "dataset": dataset_name,
                    "score": round(score, 3),
                    "record_id": record_id(dataset_name, record),
                    "matched_fields": fields,
                    "evidence_level": (
                        record.get("evidence_level")
                        or record.get("distillation_status")
                        or "curated"
                    ),
                    "record": record,
                }
            )

    hits.sort(key=lambda item: (-item["score"], record_label(item["dataset"], item["record"])))
    return hits[:limit]


def render_markdown(hits: list[dict], explain: bool = False) -> str:
    headers = ["数据集", "分数", "记录", "方法链与风险"]
    if explain:
        headers.append("匹配证据")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---:" if name == "分数" else "---" for name in headers) + " |",
    ]
    for hit in hits:
        dataset, record = hit["dataset"], hit["record"]
        left = record_label(dataset, record).replace("|", "/").replace("\n", " ")
        right = record_summary(dataset, record).replace("|", "/").replace("\n", " ")
        row = [dataset, str(hit["score"]), left, right]
        if explain:
            fields = ", ".join(hit["matched_fields"][:8]) or "token overlap"
            row.append(f'字段：{fields}；证据层：{hit["evidence_level"]}')
        lines.append("| " + " | ".join(row) + " |")
    if not hits:
        empty = ["-", "-", "未找到匹配记录", "请调整任务、数据、约束或风险关键词"]
        if explain:
            empty.append("-")
        lines.append("| " + " | ".join(empty) + " |")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the paper, subproblem, and method records.")
    parser.add_argument("--query", required=True, help="Task, data, method, constraint, or risk keywords")
    parser.add_argument("--dataset", choices=["all", *FILES], default="all")
    parser.add_argument("--topic", choices=list("ABCDEF"), help="Optional competition topic letter")
    parser.add_argument("--year", type=int, help="Optional competition year")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--explain", action="store_true", help="Show matched fields and evidence level")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    hits = search(args.query, args.dataset, args.topic, args.year, args.limit)
    if args.as_json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(hits, args.explain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
