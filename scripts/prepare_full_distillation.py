#!/usr/bin/env python3
"""Prepare traceable evidence packets and a resumable full-corpus manifest.

This command does not promote papers to the deeply curated layer. It reduces each
source Markdown file to a compact review packet with line-numbered evidence so a
maintainer can review the complete paper without repeatedly loading the full text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "references" / "data"
DEFAULT_INDEX = DATA_DIR / "paper_index.json"
DEFAULT_MARKDOWN_ROOT = ROOT.parent / "Paper-Markdown"
DEFAULT_OUTPUT = ROOT / "build" / "distillation_packets"
DEFAULT_MANIFEST = DATA_DIR / "full_distillation_manifest.json"

HEADING_RE = re.compile(
    r"^(?:第?[一二三四五六七八九十百]+[、.．章节部分]|"
    r"(?:\d+(?:\.\d+){0,3})[、.．]?\s*|"
    r"(?:摘要|关键词|问题(?:重述|分析)|模型(?:建立|求解|检验|评价)|"
    r"结果(?:分析)?|灵敏度分析|误差分析|优缺点|结论|参考文献))"
)
PROBLEM_RE = re.compile(r"(?=针对(?:第)?问题\s*[一二三四五六七八九十\d]+)")
METHOD_RE = re.compile(
    r"(?:AHP|TOPSIS|PCA|SVM|SVR|XGBoost|LightGBM|随机森林|神经网络|深度学习|"
    r"遗传算法|粒子群|蚁群算法|模拟退火|蒙特卡罗|动态规划|线性规划|非线性规划|"
    r"整数规划|多目标优化|时间序列|ARIMA|灰色预测|聚类|主成分分析|熵权法|"
    r"层次分析法|回归|马尔可夫|排队论|图论|最短路|旅行商|TSP|微分方程|"
    r"有限元|元胞自动机|博弈论|模糊综合评价|因子分析|贝叶斯|卡尔曼滤波)",
    re.IGNORECASE,
)

CATEGORY_PATTERNS = {
    "model_and_solution": re.compile(
        r"模型(?:建立|构建|求解)|算法(?:设计|流程)|目标函数|约束条件|规划模型|"
        r"回归模型|预测模型|评价模型|分类模型"
    ),
    "validation": re.compile(
        r"模型(?:检验|验证)|结果验证|灵敏度|敏感性|稳健性|鲁棒性|误差分析|"
        r"对比实验|消融|交叉验证|拟合优度"
    ),
    "results": re.compile(r"结果(?:分析)?|求解结果|实验结果|计算结果|结论"),
    "limitations": re.compile(
        r"模型(?:评价|优点|缺点|不足|改进)|优缺点|局限|不足之处|误差来源|推广"
    ),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def source_lines(text: str) -> list[tuple[int, str]]:
    return [
        (number, value)
        for number, raw in enumerate(text.splitlines(), start=1)
        if (value := compact(raw))
    ]


def headings(lines: list[tuple[int, str]], limit: int = 80) -> list[dict]:
    found: list[dict] = []
    for number, line in lines:
        candidate = line.lstrip("# ").strip()
        if len(candidate) <= 100 and HEADING_RE.match(candidate):
            found.append({"line": number, "text": candidate})
        if len(found) >= limit:
            break
    return found


def matched_windows(
    lines: list[tuple[int, str]], pattern: re.Pattern[str], max_windows: int = 8
) -> list[dict]:
    matches = [index for index, (_, line) in enumerate(lines) if pattern.search(line)]
    windows: list[dict] = []
    occupied: set[int] = set()
    for index in matches:
        if index in occupied:
            continue
        start = max(0, index - 1)
        end = min(len(lines), index + 4)
        occupied.update(range(start, end))
        snippet = compact(" ".join(line for _, line in lines[start:end]))[:1800]
        windows.append(
            {
                "line_start": lines[start][0],
                "line_end": lines[end - 1][0],
                "text": snippet,
            }
        )
        if len(windows) >= max_windows:
            break
    return windows


def abstract_problem_map(abstract: str) -> list[str]:
    parts = [compact(part) for part in PROBLEM_RE.split(abstract) if compact(part)]
    return [part[:2200] for part in parts if part.startswith("针对")]


def method_mentions(text: str) -> list[str]:
    found = [match.group(0) for match in METHOD_RE.finditer(text)]
    return list(dict.fromkeys(value.upper() if value.isascii() else value for value in found))


def build_packet(record: dict, markdown_root: Path) -> dict:
    path = markdown_root / Path(record["source_markdown"])
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = source_lines(text)
    evidence = {
        category: matched_windows(lines, pattern)
        for category, pattern in CATEGORY_PATTERNS.items()
    }
    abstract = record.get("abstract", "")
    return {
        "uid": record["uid"],
        "year": record.get("year"),
        "topic": record.get("topic", ""),
        "team_or_file_id": record.get("team_or_file_id", ""),
        "title": record.get("title", ""),
        "source_markdown": record["source_markdown"],
        "source_sha256": record.get("sha256", ""),
        "quality_flags": record.get("quality_flags", []),
        "abstract": abstract,
        "keywords": record.get("keywords", ""),
        "problem_map_candidates": abstract_problem_map(abstract),
        "method_mentions": method_mentions(abstract + " " + record.get("keywords", "")),
        "section_headings": headings(lines),
        "evidence_windows": evidence,
        "review_notice": (
            "自动生成的证据包只缩小人工/模型复核范围；其中的方法、结果、风险和"
            "章节命中均未自动晋级为 deeply_curated。"
        ),
    }


def render_packet(packet: dict) -> str:
    lines = [
        f"# {packet['title']}",
        "",
        f"- UID: `{packet['uid']}`",
        f"- 年份/题号: {packet['year']} / {packet['topic']}",
        f"- 文件: `{packet['team_or_file_id']}`",
        f"- 源 Markdown: `{packet['source_markdown']}`",
        f"- 源 SHA-256: `{packet['source_sha256']}`",
        f"- 转换质量标记: {', '.join(packet['quality_flags']) or '无'}",
        "",
        "> " + packet["review_notice"],
        "",
        "## 摘要",
        "",
        packet["abstract"] or "（未提取到摘要）",
        "",
        "## 子问题候选",
        "",
    ]
    candidates = packet["problem_map_candidates"]
    lines.extend(
        [f"{index}. {value}" for index, value in enumerate(candidates, start=1)]
        or ["（未从摘要识别到‘针对问题…’段落，需查看正文。）"]
    )
    lines.extend(["", "## 方法词候选", ""])
    lines.append("、".join(packet["method_mentions"]) or "（无规则命中）")
    lines.extend(["", "## 章节定位", ""])
    lines.extend(
        f"- L{item['line']}: {item['text']}" for item in packet["section_headings"]
    )
    for category, windows in packet["evidence_windows"].items():
        lines.extend(["", f"## 证据窗口：{category}", ""])
        if not windows:
            lines.append("（无规则命中，需人工浏览正文。）")
            continue
        for window in windows:
            lines.extend(
                [
                    f"### L{window['line_start']}–L{window['line_end']}",
                    "",
                    window["text"],
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def review_state(record: dict) -> str:
    if record.get("distillation_status") == "curated":
        return "deeply_curated"
    flags = set(record.get("quality_flags", []))
    if flags & {"missing_abstract", "short_document"}:
        return "needs_source_repair"
    if flags:
        return "ready_with_quality_flags"
    return "ready_for_deep_review"


def manifest_payload(index: dict) -> dict:
    entries = []
    for record in index["records"]:
        batch_id = f"{record.get('year')}-{record.get('topic')}"
        state = review_state(record)
        entries.append(
            {
                "uid": record["uid"],
                "batch_id": batch_id,
                "year": record.get("year"),
                "topic": record.get("topic", ""),
                "team_or_file_id": record.get("team_or_file_id", ""),
                "title": record.get("title", ""),
                "source_markdown": record["source_markdown"],
                "source_sha256": record.get("sha256", ""),
                "quality_flags": record.get("quality_flags", []),
                "review_state": state,
                "curated_paper_id": record.get("curated_paper_id", ""),
                "curation_batch": batch_id if state == "deeply_curated" else "",
            }
        )

    state_counts = Counter(entry["review_state"] for entry in entries)
    batch_counts: dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        batch_counts[entry["batch_id"]][entry["review_state"]] += 1
    batches = []
    for batch_id in sorted(batch_counts):
        counts = batch_counts[batch_id]
        total = sum(counts.values())
        batches.append(
            {
                "batch_id": batch_id,
                "total": total,
                "deeply_curated": counts["deeply_curated"],
                "remaining": total - counts["deeply_curated"],
                "ready_for_deep_review": counts["ready_for_deep_review"],
                "ready_with_quality_flags": counts["ready_with_quality_flags"],
                "needs_source_repair": counts["needs_source_repair"],
            }
        )
    return {
        "metadata": {
            "schema_version": 1,
            "record_count": len(entries),
            "state_counts": dict(sorted(state_counts.items())),
            "completion_definition": (
                "只有逐篇核验摘要、问题分析、模型建立、求解、检验、评价和结论，"
                "并通过批次晋级与知识库校验后，才能标记 deeply_curated。"
            ),
            "packet_notice": (
                "build/distillation_packets 是可再生审阅材料，不属于已核验知识。"
            ),
        },
        "batches": batches,
        "records": entries,
    }


def safe_packet_name(record: dict) -> str:
    stem = re.sub(r"[^0-9A-Za-z_-]+", "-", record.get("team_or_file_id", "")).strip("-")
    suffix = hashlib.sha1(record["uid"].encode("utf-8")).hexdigest()[:8]
    return f"{record.get('year')}-{record.get('topic')}-{stem or suffix}.md"


def prepare(
    index_path: Path,
    markdown_root: Path,
    output_dir: Path,
    manifest_path: Path,
    batch: str | None = None,
    limit: int | None = None,
) -> dict:
    index = load_json(index_path)
    manifest = manifest_payload(index)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    selected = [
        record
        for record in index["records"]
        if record.get("distillation_status") != "curated"
        and (batch is None or f"{record.get('year')}-{record.get('topic')}" == batch)
    ]
    if limit is not None:
        selected = selected[:limit]
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for record in selected:
        source = markdown_root / Path(record["source_markdown"])
        if not source.is_file():
            raise FileNotFoundError(f"Source Markdown not found: {source}")
        packet = build_packet(record, markdown_root)
        (output_dir / safe_packet_name(record)).write_text(
            render_packet(packet), encoding="utf-8"
        )
        written += 1
    return {
        "manifest_records": len(manifest["records"]),
        "packets_written": written,
        "state_counts": manifest["metadata"]["state_counts"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--markdown-root", type=Path, default=DEFAULT_MARKDOWN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--batch", help="Only write packets for one YEAR-TOPIC batch, e.g. 2016-C")
    parser.add_argument("--limit", type=int, help="Limit packet generation after filtering")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    report = prepare(
        args.index.expanduser().resolve(),
        args.markdown_root.expanduser().resolve(),
        args.output_dir.expanduser().resolve(),
        args.manifest.expanduser().resolve(),
        args.batch,
        args.limit,
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
