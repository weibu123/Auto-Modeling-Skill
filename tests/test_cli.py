from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "auto_model.py"


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_query_returns_ranked_records(self) -> None:
        result = self.run_cli("query", "脉冲星 相对论时延", "--topic", "F", "--limit", "3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("数据集", result.stdout)
        self.assertIn("F", result.stdout)

    def test_query_can_search_index_by_year(self) -> None:
        result = self.run_cli(
            "query",
            "无人机 调度",
            "--dataset",
            "index",
            "--year",
            "2016",
            "--topic",
            "A",
            "--limit",
            "3",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2016 A题", result.stdout)
        self.assertIn("curated", result.stdout)

    def test_query_finds_deeply_curated_2016_paper(self) -> None:
        result = self.run_cli(
            "query",
            "虚拟点 MTSP",
            "--dataset",
            "papers",
            "--year",
            "2016",
            "--topic",
            "A",
            "--limit",
            "3",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A16-05", result.stdout)
        self.assertIn("虚拟点MTSP", result.stdout)

    def test_query_finds_deeply_curated_2016_b_method(self) -> None:
        result = self.run_cli(
            "query",
            "SKAT 基因级关联",
            "--dataset",
            "methods",
            "--limit",
            "3",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKAT/Set-based/VEGAS", result.stdout)
        self.assertIn("methods", result.stdout)

    def test_query_explains_matching_fields_and_evidence_level(self) -> None:
        result = self.run_cli(
            "query",
            "MAF Hardy-Weinberg",
            "--dataset",
            "methods",
            "--limit",
            "2",
            "--explain",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MAF+Hardy-Weinberg", result.stdout)
        self.assertIn("deeply_curated", result.stdout)

    def test_query_surfaces_decision_fields(self) -> None:
        method = self.run_cli(
            "query",
            "局部最优 多初值 精确下界",
            "--dataset",
            "methods",
            "--limit",
            "1",
        )
        self.assertEqual(method.returncode, 0, method.stderr)
        self.assertIn("2-opt/改良圈局部搜索", method.stdout)
        self.assertIn("最低基线", method.stdout)
        self.assertIn("禁用条件", method.stdout)

        subproblem = self.run_cli(
            "query",
            "68个目标 双载荷 4小时同步 续航 2-opt 贪心覆盖",
            "--dataset",
            "subproblems",
            "--limit",
            "1",
        )
        self.assertEqual(subproblem.returncode, 0, subproblem.stderr)
        self.assertIn("A16-01", subproblem.stdout)
        self.assertIn("约束", subproblem.stdout)
        self.assertIn("指标", subproblem.stdout)

    def test_kb_validate_reports_schema_v2(self) -> None:
        result = self.run_cli("kb-validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Schema v2", result.stdout)
        self.assertIn("FAIL 0", result.stdout)

    def test_retrieval_evaluation_passes(self) -> None:
        result = self.run_cli("eval-retrieval")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Recall@k=1.0000", result.stdout)
        self.assertIn("MRR=1.0000", result.stdout)

    def test_decision_promote_check_is_read_only_and_complete(self) -> None:
        subproblems = ROOT / "references" / "data" / "subproblems.json"
        methods = ROOT / "references" / "data" / "methods.json"
        before = (subproblems.read_bytes(), methods.read_bytes())
        result = self.run_cli("decision-promote", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("237", result.stdout)
        self.assertIn("92", result.stdout)
        self.assertEqual(before, (subproblems.read_bytes(), methods.read_bytes()))

    def test_doctor_reports_components(self) -> None:
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Python", result.stdout)
        self.assertIn("LaTeX宏包", result.stdout)

    def test_init_refuses_non_empty_target_without_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "contest"
            target.mkdir()
            (target / "keep.txt").write_text("user data", encoding="utf-8")
            result = self.run_cli("init", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "user data")

    def test_init_and_audit_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "contest"
            init = self.run_cli("init", str(target), "--questions", "3", "--title", "测试赛题")
            self.assertEqual(init.returncode, 0, init.stderr)
            self.assertTrue((target / "问题3" / "建模笔记.md").is_file())
            self.assertIn("测试赛题", (target / "论文" / "论文.tex").read_text(encoding="utf-8"))
            self.assertTrue((target / "论文" / "论文草稿.md").is_file())

            (target / "题目" / "赛题.md").write_text("测试题目", encoding="utf-8")
            audit = self.run_cli("audit", str(target))
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("PASS", audit.stdout)
            self.assertIn("WARN", audit.stdout)
            self.assertIn("论文结构", audit.stdout)
            self.assertIn("正文写作红线", audit.stdout)

    def test_merge_never_overwrites_existing_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "contest"
            first = self.run_cli("init", str(target), "--questions", "2")
            self.assertEqual(first.returncode, 0)
            note = target / "问题1" / "建模笔记.md"
            note.write_text("custom note", encoding="utf-8")
            merged = self.run_cli("init", str(target), "--questions", "3", "--merge")
            self.assertEqual(merged.returncode, 0, merged.stderr)
            self.assertEqual(note.read_text(encoding="utf-8"), "custom note")
            self.assertTrue((target / "问题3" / "建模笔记.md").is_file())

    def test_audit_flags_process_language_in_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "contest"
            init = self.run_cli("init", str(target), "--questions", "1")
            self.assertEqual(init.returncode, 0)
            (target / "题目" / "赛题.md").write_text("测试题目", encoding="utf-8")
            paper = target / "论文" / "论文.tex"
            paper.write_text(
                paper.read_text(encoding="utf-8") + "\n调用了某函数并写入文件 result.csv。\n",
                encoding="utf-8",
            )
            audit = self.run_cli("audit", str(target))
            self.assertEqual(audit.returncode, 0)
            self.assertIn("疑似程序日志或过程元语言", audit.stdout)
            self.assertIn("result.csv", audit.stdout)


if __name__ == "__main__":
    unittest.main()
