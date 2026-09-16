#!/usr/bin/env python3
"""Create a safe, reproducible mathematical-modeling competition workspace."""

from __future__ import annotations

import argparse
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets"


def _write_if_missing(path: Path, content: str, created: list[Path]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def _asset(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def initialize_workspace(
    target: Path,
    questions: int = 4,
    title: str = "数学建模竞赛论文",
    merge: bool = False,
) -> list[Path]:
    if not 1 <= questions <= 12:
        raise ValueError("questions must be between 1 and 12")
    target = target.expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise ValueError(f"target is not a directory: {target}")
    if target.exists() and any(target.iterdir()) and not merge:
        raise ValueError("target is not empty; use --merge to add only missing files")

    target.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    directories = [
        target / "题目",
        target / "数据" / "原始",
        target / "数据" / "处理",
        target / "论文" / "figures",
        target / "论文" / "tables",
        target / "参考资料",
        target / "logs",
    ]
    for index in range(1, questions + 1):
        directories.extend(
            [
                target / f"问题{index}" / "代码",
                target / f"问题{index}" / "结果",
            ]
        )
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True)
            created.append(directory)

    status = _asset("status-template.md").replace("{{COMPETITION_TITLE}}", title)
    _write_if_missing(target / "比赛状态.md", status, created)

    note_template = _asset("modeling-note-template.md")
    for index in range(1, questions + 1):
        note = note_template.replace("{{QUESTION_NUMBER}}", str(index))
        _write_if_missing(target / f"问题{index}" / "建模笔记.md", note, created)

    paper = _asset("paper-template.tex").replace("{{COMPETITION_TITLE}}", title)
    _write_if_missing(target / "论文" / "论文.tex", paper, created)

    source_notice = "本目录保存原始赛题。请保留原文件名和内容，不在此处写入派生结果。\n"
    data_notice = "本目录保存原始附件。清洗或转换后的数据写入 ../处理/，并保留生成脚本。\n"
    _write_if_missing(target / "题目" / "README.md", source_notice, created)
    _write_if_missing(target / "数据" / "原始" / "README.md", data_notice, created)
    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a mathematical-modeling competition workspace.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--questions", type=int, default=4)
    parser.add_argument("--title", default="数学建模竞赛论文")
    parser.add_argument("--merge", action="store_true", help="Add only missing files to a non-empty target")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        created = initialize_workspace(args.target, args.questions, args.title, args.merge)
    except ValueError as exc:
        print(f"错误：{exc}")
        return 2
    print(f"已初始化：{args.target.expanduser().resolve()}")
    print(f"新增目录或文件：{len(created)}；已有文件均未覆盖。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
