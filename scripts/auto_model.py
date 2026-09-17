#!/usr/bin/env python3
"""Unified command-line entry point for Auto Modeling Skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from audit_project import audit_workspace, exit_code, render_markdown as render_audit
from apply_decision_fields import BATCH_DIR as DECISION_BATCH_DIR
from apply_decision_fields import apply_batches as apply_decision_batches
from evaluate_retrieval import evaluate as evaluate_retrieval
from evaluate_retrieval import render as render_retrieval_evaluation
from init_project import initialize_workspace
from query_kb import FILES, render_markdown as render_hits, search
from validate_kb import render as render_kb_validation
from validate_kb import validate as validate_kb


LATEX_REQUIREMENTS = [
    "ctexart.cls",
    "geometry.sty",
    "amsmath.sty",
    "booktabs.sty",
    "graphicx.sty",
    "float.sty",
    "siunitx.sty",
    "hyperref.sty",
    "enumitem.sty",
    "xcolor.sty",
]


def doctor_checks() -> list[tuple[str, str, str]]:
    checks: list[tuple[str, str, str]] = []
    python_ok = sys.version_info >= (3, 10)
    checks.append(("PASS" if python_ok else "FAIL", "Python", sys.version.split()[0]))

    xelatex = shutil.which("xelatex")
    checks.append(("PASS" if xelatex else "WARN", "XeLaTeX", xelatex or "未安装"))
    kpsewhich = shutil.which("kpsewhich")
    if not kpsewhich:
        checks.append(("WARN", "LaTeX宏包", "无法运行 kpsewhich 检查宏包"))
        return checks

    missing: list[str] = []
    for requirement in LATEX_REQUIREMENTS:
        result = subprocess.run(
            [kpsewhich, requirement],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            missing.append(requirement)
    checks.append(
        (
            "PASS" if not missing else "WARN",
            "LaTeX宏包",
            "全部可用" if not missing else "缺少：" + ", ".join(missing),
        )
    )
    return checks


def render_doctor(checks: list[tuple[str, str, str]]) -> str:
    lines = ["| 状态 | 组件 | 详情 |", "| --- | --- | --- |"]
    lines.extend(f"| {level} | {item} | {detail} |" for level, item, detail in checks)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto_model.py",
        description="Initialize, query, audit, and diagnose mathematical-modeling competition workspaces.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a standard competition workspace")
    init_parser.add_argument("target", type=Path)
    init_parser.add_argument("--questions", type=int, default=4)
    init_parser.add_argument("--title", default="数学建模竞赛论文")
    init_parser.add_argument("--merge", action="store_true")

    query_parser = subparsers.add_parser("query", help="Search the curated knowledge base")
    query_parser.add_argument("query", help="Task, data, method, constraint, or risk keywords")
    query_parser.add_argument("--dataset", choices=["all", *FILES], default="all")
    query_parser.add_argument("--topic", choices=list("ABCDEF"))
    query_parser.add_argument("--year", type=int)
    query_parser.add_argument("--limit", type=int, default=8)
    query_parser.add_argument("--json", action="store_true", dest="as_json")
    query_parser.add_argument("--explain", action="store_true")

    audit_parser = subparsers.add_parser("audit", help="Audit a workspace without modifying it")
    audit_parser.add_argument("target", type=Path)
    audit_parser.add_argument("--strict", action="store_true")

    doctor_parser = subparsers.add_parser("doctor", help="Check Python and Chinese LaTeX requirements")
    doctor_parser.add_argument("--strict", action="store_true")

    kb_parser = subparsers.add_parser("kb-validate", help="Validate Schema v2 and knowledge links")
    kb_parser.add_argument("--strict", action="store_true")
    kb_parser.add_argument("--json", action="store_true", dest="as_json")

    retrieval_parser = subparsers.add_parser(
        "eval-retrieval",
        help="Measure retrieval Recall@k and mean reciprocal rank",
    )
    retrieval_parser.add_argument("--json", action="store_true", dest="as_json")

    decision_parser = subparsers.add_parser(
        "decision-promote",
        help="Apply reviewed constraints, metrics, baselines, and method guardrails",
    )
    decision_parser.add_argument("batches", nargs="*", type=Path)
    decision_parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        try:
            created = initialize_workspace(args.target, args.questions, args.title, args.merge)
        except ValueError as exc:
            print(f"错误：{exc}")
            return 2
        print(f"已初始化：{args.target.expanduser().resolve()}")
        print(f"新增目录或文件：{len(created)}；已有文件均未覆盖。")
        return 0

    if args.command == "query":
        try:
            hits = search(args.query, args.dataset, args.topic, args.year, args.limit)
        except ValueError as exc:
            print(f"错误：{exc}")
            return 2
        print(
            json.dumps(hits, ensure_ascii=False, indent=2)
            if args.as_json
            else render_hits(hits, args.explain)
        )
        return 0

    if args.command == "audit":
        checks = audit_workspace(args.target)
        print(render_audit(checks))
        return exit_code(checks, args.strict)

    if args.command == "kb-validate":
        findings, summary = validate_kb()
        if args.as_json:
            from dataclasses import asdict

            print(
                json.dumps(
                    {"summary": summary, "findings": [asdict(item) for item in findings]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(render_kb_validation(findings, summary))
        if summary["failures"]:
            return 2
        if args.strict and summary["warnings"]:
            return 1
        return 0

    if args.command == "eval-retrieval":
        report = evaluate_retrieval()
        print(
            json.dumps(report, ensure_ascii=False, indent=2)
            if args.as_json
            else render_retrieval_evaluation(report)
        )
        return 0 if report["passed"] else 1

    if args.command == "decision-promote":
        paths = args.batches or sorted(DECISION_BATCH_DIR.glob("*.json"))
        try:
            report = apply_decision_batches(
                [path.resolve() for path in paths],
                write=not args.check,
            )
        except ValueError as exc:
            print(f"错误：{exc}")
            return 2
        mode = "已校验" if args.check else "已写入"
        print(
            f"决策字段{mode}：{len(report['batches'])} 个批次，"
            f"{report['subproblems_updated']} 个子问题，"
            f"{report['methods_updated']} 个方法。"
        )
        return 0

    checks = doctor_checks()
    print(render_doctor(checks))
    if any(level == "FAIL" for level, _, _ in checks):
        return 2
    if args.strict and any(level == "WARN" for level, _, _ in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
