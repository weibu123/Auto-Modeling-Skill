#!/usr/bin/env python3
"""Build a traceable paper index from MarkItDown Markdown files.

The index is deliberately separate from the deeply curated paper, subproblem,
and method datasets. Automatic extraction makes papers discoverable; it does
not promote their claims to curated evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MARKDOWN_ROOT = ROOT.parent / "Paper-Markdown"
DEFAULT_OUTPUT = ROOT / "references" / "data" / "paper_index.json"
CURATED_PAPERS = ROOT / "references" / "data" / "papers.json"
OVERRIDES = ROOT / "references" / "data" / "paper_index_overrides.json"

YEAR_RE = re.compile(r"20\d{2}")
TOPIC_PATH_RE = re.compile(r"(?:^|/)([A-F])(?:题|/)", re.IGNORECASE)
ABSTRACT_RE = re.compile(r"摘\s*要\s*[:：]?", re.IGNORECASE)
KEYWORDS_RE = re.compile(r"关\s*键\s*[词字]\s*[:：]?", re.IGNORECASE)
TITLE_RE = re.compile(r"^(?:论文)?题\s*目\s*[:：]?\s*(.+)$", re.IGNORECASE)
TEAM_ID_RE = re.compile(r"^[A-F]?[K]?\d+(?:_\d+_)?$", re.IGNORECASE)


def clean_line(line: str) -> str:
    line = line.replace("\u3000", " ").replace("|", " ")
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", line)
    line = re.sub(r"<[^>]+>", " ", line)
    return re.sub(r"\s+", " ", line).strip(" -\t")


def cleaned_lines(text: str) -> list[str]:
    return [value for line in text.splitlines() if (value := clean_line(line))]


def infer_year(relative_path: str) -> int | None:
    match = YEAR_RE.search(relative_path)
    return int(match.group()) if match else None


def infer_topic(relative_path: str, stem: str) -> str:
    normalized = relative_path.replace("\\", "/")
    match = TOPIC_PATH_RE.search(normalized)
    if match:
        return match.group(1).upper()
    match = re.match(r"^([A-F])", stem, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def usable_title_candidate(line: str) -> bool:
    if not 4 <= len(line) <= 120:
        return False
    blocked = (
        "数学建模竞赛",
        "参赛密码",
        "参赛队号",
        "队员姓名",
        "学校",
        "摘 要",
        "摘要",
        "关键词",
        "关键字",
        "目录",
        "组委会",
    )
    return not any(token in line for token in blocked) and not line.isdigit()


def extract_title(
    lines: list[str], stem: str, curated_title: str | None
) -> tuple[str, str]:
    if curated_title:
        return curated_title, "curated"

    for index, line in enumerate(lines[:160]):
        match = TITLE_RE.match(line)
        if not match:
            continue
        title = match.group(1).strip()
        title = ABSTRACT_RE.split(title, maxsplit=1)[0].strip()
        if usable_title_candidate(title):
            return title, "markdown-label"
        for following in lines[index + 1 : index + 4]:
            if usable_title_candidate(following):
                return following, "markdown-after-label"

    abstract_index = next(
        (index for index, line in enumerate(lines[:160]) if ABSTRACT_RE.search(line)),
        None,
    )
    if abstract_index is not None:
        for candidate in reversed(lines[max(0, abstract_index - 10) : abstract_index]):
            if usable_title_candidate(candidate):
                return candidate, "markdown-before-abstract"

    filename_title = re.sub(r"^[A-F]题[-_—\s]*", "", stem, flags=re.IGNORECASE)
    if not TEAM_ID_RE.fullmatch(stem) and usable_title_candidate(filename_title):
        return filename_title, "filename"
    return "待人工确认", "missing"


def extract_abstract(lines: list[str]) -> tuple[str, str]:
    start_index: int | None = None
    initial = ""
    for index, line in enumerate(lines[:220]):
        match = ABSTRACT_RE.search(line)
        if match:
            start_index = index
            initial = line[match.end() :].strip()
            break
    if start_index is None:
        return "", "missing"

    parts: list[str] = [initial] if initial else []
    for line in lines[start_index + 1 :]:
        if KEYWORDS_RE.search(line) or re.fullmatch(r"目\s*录", line):
            break
        if len("".join(parts)) >= 9000:
            break
        parts.append(line)
    abstract = re.sub(r"\s+", " ", " ".join(parts)).strip()
    return abstract, "markdown"


def extract_keywords(lines: list[str]) -> str:
    for index, line in enumerate(lines[:260]):
        match = KEYWORDS_RE.search(line)
        if not match:
            continue
        parts = [line[match.end() :].strip()]
        for following in lines[index + 1 : index + 3]:
            if re.fullmatch(r"目\s*录", following) or re.match(r"^\d+[.、\s]", following):
                break
            parts.append(following)
        return re.sub(r"\s+", " ", " ".join(parts)).strip(" ;；，,")
    return ""


def excerpt_without_front_matter(lines: list[str], limit: int = 2500) -> str:
    useful = [line for line in lines if usable_title_candidate(line)]
    return re.sub(r"\s+", " ", " ".join(useful[:80])).strip()[:limit]


def load_curated() -> dict[str, dict]:
    payload = json.loads(CURATED_PAPERS.read_text(encoding="utf-8"))
    return {
        Path(record.get("source_file", "")).stem.casefold(): record
        for record in payload["records"]
    }


def load_overrides() -> dict[str, dict]:
    if not OVERRIDES.exists():
        return {}
    payload = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    return payload.get("overrides", {})


def build_record(
    path: Path,
    markdown_root: Path,
    curated: dict[str, dict],
    overrides: dict[str, dict],
) -> dict:
    relative = path.relative_to(markdown_root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = cleaned_lines(text)
    curated_record = curated.get(path.stem.casefold())
    title, title_source = extract_title(
        lines,
        path.stem,
        curated_record.get("title") if curated_record else None,
    )
    abstract, abstract_source = extract_abstract(lines)
    keywords = extract_keywords(lines)
    override = overrides.get(relative, overrides.get(path.stem, {}))
    if override.get("title"):
        title = override["title"]
        title_source = override.get("title_source", "manual_override")
    if override.get("abstract"):
        abstract = override["abstract"]
        abstract_source = override.get("abstract_source", "manual_override")
    if override.get("keywords"):
        keywords = override["keywords"]
    year = infer_year(relative)
    topic = infer_topic(relative, path.stem)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    uid_seed = hashlib.sha1(relative.encode("utf-8")).hexdigest()[:10]

    flags: list[str] = []
    if title == "待人工确认":
        flags.append("missing_title")
    if not abstract:
        flags.append("missing_abstract")
    elif len(abstract) < 200:
        flags.append("short_abstract")
    if "(cid:" in text:
        flags.append("cid_tokens")
    if "�" in text:
        flags.append("replacement_characters")
    if len(text) < 5000:
        flags.append("short_document")

    return {
        "uid": f"HC-{year or 'unknown'}-{topic or 'X'}-{uid_seed}",
        "year": year,
        "topic": topic,
        "team_or_file_id": path.stem,
        "title": title,
        "title_source": title_source,
        "abstract": abstract,
        "abstract_source": abstract_source,
        "keywords": keywords,
        "content_excerpt": abstract[:4000] if abstract else excerpt_without_front_matter(lines),
        "distillation_status": "curated" if curated_record else "indexed",
        "curated_paper_id": curated_record.get("id", "") if curated_record else "",
        "quality_flags": flags,
        "override_note": override.get("note", ""),
        "text_characters": len(text),
        "source_markdown": relative,
        "source_pdf": str(Path(relative).with_suffix(".pdf")).replace("\\", "/"),
        "sha256": digest,
    }


def build_index(markdown_root: Path) -> dict:
    curated = load_curated()
    overrides = load_overrides()
    paths = sorted(markdown_root.rglob("*.md"), key=lambda item: item.as_posix())
    records = [build_record(path, markdown_root, curated, overrides) for path in paths]
    status_counts = Counter(record["distillation_status"] for record in records)
    flag_counts = Counter(flag for record in records for flag in record["quality_flags"])
    return {
        "metadata": {
            "source": "MarkItDown Markdown corpus",
            "source_root": markdown_root.name,
            "record_count": len(records),
            "curated_count": status_counts["curated"],
            "indexed_count": status_counts["indexed"],
            "manual_override_count": sum(bool(record["override_note"]) for record in records),
            "quality_flag_counts": dict(sorted(flag_counts.items())),
            "evidence_level": (
                "自动提取的标题、摘要和关键词仅用于发现；只有 distillation_status=curated "
                "的记录经过论文级人工/模型结构化蒸馏。"
            ),
        },
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown-root", type=Path, default=DEFAULT_MARKDOWN_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown_root = args.markdown_root.expanduser().resolve()
    if not markdown_root.is_dir():
        raise SystemExit(f"Markdown root not found: {markdown_root}")
    payload = build_index(markdown_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    metadata = payload["metadata"]
    print(
        f"Indexed {metadata['record_count']} papers: "
        f"{metadata['curated_count']} curated, {metadata['indexed_count']} awaiting distillation."
    )
    print(f"Quality flags: {metadata['quality_flag_counts']}")
    print(f"Wrote: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
