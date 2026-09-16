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
        self.assertEqual(match.group(1), ROOT.name)

    def test_skill_references_exist(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        missing = [link for link in links if not (ROOT / link).exists()]
        self.assertEqual(missing, [])

    def test_knowledge_base_counts(self) -> None:
        expected = {"papers.json": 44, "subproblems.json": 164, "methods.json": 66}
        for filename, count in expected.items():
            payload = json.loads((ROOT / "references" / "data" / filename).read_text(encoding="utf-8"))
            self.assertEqual(len(payload["records"]), count, filename)

    def test_ui_prompt_uses_current_skill_name(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$auto-modeling-skill", text)
        self.assertNotIn("$huawei-cup-modeling", text)


if __name__ == "__main__":
    unittest.main()
