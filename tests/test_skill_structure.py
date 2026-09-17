from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        self.assertTrue(reference.is_file())


if __name__ == "__main__":
    unittest.main()
