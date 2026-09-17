from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_retrieval import evaluate  # noqa: E402
from validate_kb import validate  # noqa: E402


class SkillStructureTests(unittest.TestCase):
    def test_skill_name_matches_directory(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), ROOT.name.lower())

    def test_skill_references_exist(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        missing = [link for link in links if not (ROOT / link).exists()]
        self.assertEqual(missing, [])

    def test_knowledge_base_counts(self) -> None:
        expected = {
            "papers.json": 55,
            "subproblems.json": 213,
            "methods.json": 86,
            "paper_index.json": 338,
        }
        for filename, count in expected.items():
            payload = json.loads((ROOT / "references" / "data" / filename).read_text(encoding="utf-8"))
            self.assertEqual(len(payload["records"]), count, filename)

    def test_schema_v2_has_no_integrity_failures(self) -> None:
        findings, summary = validate()
        self.assertEqual(summary["schema_version"], 2)
        self.assertEqual(summary["failures"], 0, findings)
        papers = json.loads(
            (ROOT / "references" / "data" / "papers.json").read_text(encoding="utf-8")
        )["records"]
        self.assertTrue(all(isinstance(record["year"], int) for record in papers))
        self.assertTrue(all(record["record_version"] == 2 for record in papers))

    def test_retrieval_eval_meets_reviewed_threshold(self) -> None:
        report = evaluate()
        self.assertTrue(report["passed"], report["results"])
        self.assertGreaterEqual(report["recall_at_k"], 0.9)
        self.assertGreaterEqual(report["mrr"], 0.75)

    def test_modeling_forward_cases_have_behavioral_rubrics(self) -> None:
        payload = json.loads((ROOT / "evals" / "modeling_cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(payload["cases"]), 6)
        for case in payload["cases"]:
            self.assertTrue(case["prompt"])
            self.assertTrue(case["required_behaviors"])
            self.assertTrue(case["forbidden_behaviors"])

    def test_paper_index_invariants(self) -> None:
        payload = json.loads(
            (ROOT / "references" / "data" / "paper_index.json").read_text(encoding="utf-8")
        )
        records = payload["records"]
        self.assertEqual(len({record["uid"] for record in records}), len(records))
        self.assertEqual(len({record["source_markdown"] for record in records}), len(records))
        self.assertEqual(
            sum(record["distillation_status"] == "curated" for record in records),
            55,
        )
        self.assertTrue(
            all(
                record["curated_paper_id"]
                for record in records
                if record["distillation_status"] == "curated"
            )
        )
        self.assertEqual(payload["metadata"]["manual_override_count"], 2)
        self.assertEqual(payload["metadata"]["quality_flag_counts"].get("missing_title", 0), 0)

    def test_2016_a_curation_batch_is_traceable(self) -> None:
        batch = json.loads(
            (
                ROOT
                / "references"
                / "data"
                / "curation_batches"
                / "2016-A.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(len(batch["papers"]), 5)
        self.assertEqual(len(batch["subproblems"]), 25)
        self.assertEqual(len(batch["new_methods"]), 10)
        paper_ids = {record["id"] for record in batch["papers"]}
        self.assertEqual(len(paper_ids), 5)
        self.assertTrue(
            all(record["paper_id"] in paper_ids for record in batch["subproblems"])
        )

    def test_2016_b_curation_batch_is_traceable(self) -> None:
        batch = json.loads(
            (
                ROOT
                / "references"
                / "data"
                / "curation_batches"
                / "2016-B.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(len(batch["papers"]), 6)
        self.assertEqual(len(batch["subproblems"]), 24)
        self.assertEqual(len(batch["new_methods"]), 10)
        paper_ids = {record["id"] for record in batch["papers"]}
        self.assertEqual(len(paper_ids), 6)
        self.assertTrue(
            all(record["paper_id"] in paper_ids for record in batch["subproblems"])
        )

    def test_2016_decision_batches_are_traceable(self) -> None:
        expected = {"2016-A": (25, 10), "2016-B": (24, 10)}
        for batch_id, counts in expected.items():
            batch = json.loads(
                (
                    ROOT
                    / "references"
                    / "data"
                    / "decision_fields"
                    / f"{batch_id}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(batch["batch_id"], batch_id)
            self.assertTrue(batch["evidence_basis"])
            self.assertEqual(len(batch["subproblems"]), counts[0])
            self.assertEqual(len(batch["methods"]), counts[1])
            self.assertTrue(
                all(item["constraints"] and item["metric"] for item in batch["subproblems"])
            )
            self.assertTrue(
                all(
                    item["minimum_baseline"]
                    and item["forbidden_when"]
                    and item["recommended_alternatives"]
                    and item["common_misuse"]
                    for item in batch["methods"]
                )
            )

    def test_decision_field_coverage_matches_reviewed_batches(self) -> None:
        subproblems = json.loads(
            (ROOT / "references" / "data" / "subproblems.json").read_text(encoding="utf-8")
        )
        methods = json.loads(
            (ROOT / "references" / "data" / "methods.json").read_text(encoding="utf-8")
        )
        expected_batches = sorted(
            path.stem
            for path in (ROOT / "references" / "data" / "decision_fields").glob("*.json")
        )
        self.assertEqual(subproblems["metadata"]["decision_field_batches"], expected_batches)
        self.assertEqual(methods["metadata"]["decision_field_batches"], expected_batches)
        self.assertEqual(sum(not item["metric"] for item in subproblems["records"]), 0)
        self.assertEqual(sum(not item["constraints"] for item in subproblems["records"]), 0)
        self.assertEqual(sum(not item["minimum_baseline"] for item in methods["records"]), 0)
        curated_subproblems = [item for item in subproblems["records"] if item.get("decision_field_sources")]
        curated_methods = [item for item in methods["records"] if item.get("decision_field_sources")]
        self.assertEqual(len(curated_subproblems), 213)
        self.assertEqual(len(curated_methods), 86)

    def test_cross_cutting_method_batch_is_traceable(self) -> None:
        batch = json.loads(
            (
                ROOT
                / "references"
                / "data"
                / "decision_fields"
                / "cross-cutting-methods-v1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(batch["batch_id"], "cross-cutting-methods-v1")
        self.assertEqual(batch["subproblems"], [])
        self.assertEqual(len(batch["methods"]), 15)
        self.assertTrue(
            all(
                item["minimum_baseline"]
                and item["forbidden_when"]
                and item["recommended_alternatives"]
                and item["common_misuse"]
                for item in batch["methods"]
            )
        )

    def test_ui_prompt_uses_current_skill_name(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$auto-modeling-skill", text)
        self.assertNotIn("$huawei-cup-modeling", text)

    def test_writing_resources_are_routed(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/paper-writing.md", skill)
        self.assertIn("references/delivery-checklist.md", skill)
        self.assertTrue((ROOT / "assets" / "paper-draft-template.md").is_file())

    def test_knowledge_maintenance_rules_are_routed(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = ROOT / "references" / "knowledge-base-evidence.md"
        self.assertIn("references/knowledge-base-evidence.md", skill)
        self.assertIn("references/knowledge-base-schema.md", skill)
        self.assertIn("references/evaluation.md", skill)
        self.assertTrue(reference.is_file())


if __name__ == "__main__":
    unittest.main()
