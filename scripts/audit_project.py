#!/usr/bin/env python3
"""Read-only audit for a mathematical-modeling competition workspace."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


QUESTION_PATTERN = re.compile(r"^问题(\d+)$")
PLACEHOLDER_PATTERN = re.compile(r"\[待(?:填写|计算|核实)[^\]]*\]|\b(?:TODO|TBD)\b", re.IGNORECASE)


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

    paper_tex = root / "论文" / "论文.tex"
    paper_pdf = root / "论文" / "论文.pdf"
    checks.append(Check("PASS" if paper_tex.is_file() else "FAIL", "LaTeX论文", str(paper_tex)))
    checks.append(Check("PASS" if paper_pdf.is_file() else "WARN", "编译PDF", str(paper_pdf)))

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
