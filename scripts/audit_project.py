#!/usr/bin/env python3
"""Read-only audit for a mathematical-modeling competition workspace."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


QUESTION_PATTERN = re.compile(r"^问题(\d+)$")
PLACEHOLDER_PATTERN = re.compile(r"\[待(?:填写|计算|核实|补证据)[^\]]*\]|\b(?:TODO|TBD)\b", re.IGNORECASE)
RAW_FILENAME_PATTERN = re.compile(r"(?<![\w.-])[\w.-]+\.(?:csv|xlsx?|json|npy|pkl)(?![\w.-])", re.IGNORECASE)
PROCESS_LANGUAGE_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"调用.{0,12}函数",
        r"写入(?:了)?文件",
        r"程序报错",
        r"机械校验",
        r"独立复算",
        r"如实报告",
    )
]
STOCK_PHRASES = ("值得指出的是", "值得注意的是", "综上所述", "由此可见")
REQUIRED_LATEX_MARKERS = (
    r"\begin{abstract}",
    r"\section{问题重述}",
    r"\section{问题分析}",
    r"\section{模型假设}",
    r"\section{符号说明}",
    r"\section{模型建立与求解}",
    r"\section{模型评价与推广}",
    r"\section{结论}",
    r"\begin{thebibliography}",
    r"\appendix",
)


@dataclass(frozen=True)
class Check:
    level: str
    item: str
    detail: str


def _visible_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [p for p in path.rglob("*") if p.is_file() and not any(part.startswith(".") for part in p.parts)]


def _count_placeholders(path: Path) -> int:
    total = 0
    for file in _visible_files(path):
        if file.suffix.lower() not in {".md", ".tex"} or file.stat().st_size > 2_000_000:
            continue
        try:
            total += len(PLACEHOLDER_PATTERN.findall(file.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return total


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _latex_without_comments(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def _paper_style_findings(text: str) -> list[str]:
    body = _latex_without_comments(text)
    findings: list[str] = []
    filenames = sorted(set(RAW_FILENAME_PATTERN.findall(body)))
    if filenames:
        findings.append("正文出现原始文件名：" + ", ".join(filenames[:5]))
    process_hits = sorted(
        {match.group(0) for pattern in PROCESS_LANGUAGE_PATTERNS for match in pattern.finditer(body)}
    )
    if process_hits:
        findings.append("疑似程序日志或过程元语言：" + "、".join(process_hits[:5]))
    repeated = [f"{phrase}×{body.count(phrase)}" for phrase in STOCK_PHRASES if body.count(phrase) >= 3]
    if repeated:
        findings.append("模板化连接词重复：" + "、".join(repeated))
    return findings


def audit_workspace(root: Path) -> list[Check]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        return [Check("FAIL", "工作区", f"目录不存在：{root}")]

    checks: list[Check] = []
    prompt_files = [p for p in _visible_files(root / "题目") if p.name.lower() != "readme.md"]
    checks.append(Check("PASS" if prompt_files else "FAIL", "原始题目", f"发现 {len(prompt_files)} 个题目文件"))

    raw_files = [p for p in _visible_files(root / "数据" / "原始") if p.name.lower() != "readme.md"]
    checks.append(Check("PASS" if raw_files else "WARN", "原始附件", f"发现 {len(raw_files)} 个附件文件"))

    question_dirs = sorted(
        [p for p in root.iterdir() if p.is_dir() and QUESTION_PATTERN.match(p.name)],
        key=lambda p: int(QUESTION_PATTERN.match(p.name).group(1)),
    )
    if not question_dirs:
        checks.append(Check("FAIL", "子问题目录", "未找到问题1、问题2等目录"))
    for question_dir in question_dirs:
        note = question_dir / "建模笔记.md"
        code_count = len(_visible_files(question_dir / "代码"))
        result_count = len(_visible_files(question_dir / "结果"))
        checks.append(Check("PASS" if note.is_file() else "FAIL", f"{question_dir.name}笔记", str(note)))
        checks.append(Check("PASS" if code_count else "WARN", f"{question_dir.name}代码", f"发现 {code_count} 个代码或配置文件"))
        checks.append(Check("PASS" if result_count else "WARN", f"{question_dir.name}结果", f"发现 {result_count} 个结果文件"))

    paper_draft = root / "论文" / "论文草稿.md"
    paper_tex = root / "论文" / "论文.tex"
    paper_pdf = root / "论文" / "论文.pdf"
    checks.append(Check("PASS" if paper_draft.is_file() else "WARN", "Markdown论文草稿", str(paper_draft)))
    checks.append(Check("PASS" if paper_tex.is_file() else "FAIL", "LaTeX论文", str(paper_tex)))
    checks.append(Check("PASS" if paper_pdf.is_file() else "WARN", "编译PDF", str(paper_pdf)))

    if paper_tex.is_file():
        paper_text = _read_utf8(paper_tex)
        missing_markers = [marker for marker in REQUIRED_LATEX_MARKERS if marker not in paper_text]
        checks.append(
            Check(
                "PASS" if not missing_markers else "WARN",
                "论文结构",
                "核心章节完整" if not missing_markers else "缺少：" + ", ".join(missing_markers),
            )
        )
        style_findings = _paper_style_findings(paper_text)
        checks.append(
            Check(
                "PASS" if not style_findings else "WARN",
                "正文写作红线",
                "未发现文件名、程序日志式语言或高频模板词" if not style_findings else "；".join(style_findings),
            )
        )

    placeholder_count = _count_placeholders(root)
    checks.append(Check("PASS" if placeholder_count == 0 else "WARN", "未完成占位符", f"发现 {placeholder_count} 处待填写、待计算、TODO 或 TBD"))
    return checks


def render_markdown(checks: list[Check]) -> str:
    lines = ["| 状态 | 检查项 | 详情 |", "| --- | --- | --- |"]
    for check in checks:
        detail = check.detail.replace("|", "/").replace("\n", " ")
        lines.append(f"| {check.level} | {check.item} | {detail} |")
    counts = {level: sum(c.level == level for c in checks) for level in ("PASS", "WARN", "FAIL")}
    lines.append("")
    lines.append(f'汇总：PASS {counts["PASS"]}，WARN {counts["WARN"]}，FAIL {counts["FAIL"]}。')
    return "\n".join(lines)


def exit_code(checks: list[Check], strict: bool = False) -> int:
    if any(check.level == "FAIL" for check in checks):
        return 2
    if strict and any(check.level == "WARN" for check in checks):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a competition workspace without modifying it.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings remain")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checks = audit_workspace(args.target)
    print(render_markdown(checks))
    return exit_code(checks, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
