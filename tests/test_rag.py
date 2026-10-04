from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skill"
SCRIPT_DIR = SKILL_ROOT / "scripts"
INDEX_PATH = SKILL_ROOT / "references" / "rag-index.json"

sys.path.insert(0, str(SCRIPT_DIR))

from retrieve_rag import retrieve  # noqa: E402


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "build_rag_index.py")],
            check=True,
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
        )
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    def test_all_source_records_are_indexed_and_hashes_match(self) -> None:
        self.assertEqual(self.index["source_count"], 12)
        self.assertGreater(self.index["chunk_count"], 0)
        for source in self.index["sources"]:
            path = SKILL_ROOT / source["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, source["sha256"], source["source_id"])

    def test_project_expansion_query_returns_primary_direct_evidence(self) -> None:
        results = retrieve(
            "overhiring rapid expansion high performing team regression "
            "flat headcount quality focus execution"
        )
        self.assertLessEqual(len(results), 4)
        self.assertIn("AW_008", {result["source_id"] for result in results})
        self.assertEqual(results[0]["statement_type"], "direct_statement")

    def test_unrelated_query_returns_no_results(self) -> None:
        results = retrieve("marine biology coral reef salinity field sampling")
        self.assertEqual(results, [])

    def test_results_preserve_provenance(self) -> None:
        results = retrieve("accountability challenge metrics failure diagnosis outcomes")
        self.assertTrue(results)
        required = {"source_id", "chunk_id", "statement_type", "source_status", "source_url"}
        self.assertTrue(required.issubset(results[0]))


if __name__ == "__main__":
    unittest.main()
