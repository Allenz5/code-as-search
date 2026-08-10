"""Working-memory tests. No model, no network."""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import memory  # noqa: E402

META = {"objective": "Who backed Acme?", "credits": 3, "budget": 200}


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.path = Path(self._tmp.name) / "memory.jsonl"
        self.addCleanup(self._tmp.cleanup)

    def lines(self):
        return memory.read_records(self.path)

    # --- ids -------------------------------------------------------------

    def test_ids_are_assigned_per_type_and_increment(self):
        ids = memory.append(
            self.path,
            [
                {"t": "question", "text": "Who led the Series B?"},
                {"t": "question", "text": "When did it close?"},
                {"t": "note", "text": "sources disagree on size"},
            ],
        )
        self.assertEqual(ids, ["q1", "q2", "n1"])
        ids = memory.append(self.path, [{"t": "question", "text": "third"}])
        self.assertEqual(ids, ["q3"])

    def test_new_question_defaults_to_open(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        self.assertEqual(memory.fold(self.lines())["question"]["q1"]["status"], "open")

    def test_finding_can_reference_a_question_created_in_the_same_batch(self):
        ids = memory.append(
            self.path,
            [
                {"t": "question", "text": "Who led it?"},
                {"t": "finding", "q": "q1", "text": "Northwind led", "url": "https://a"},
            ],
        )
        self.assertEqual(ids, ["q1", "f1"])

    # --- append-only updates ---------------------------------------------

    def test_update_merges_and_does_not_rewrite_history(self):
        memory.append(self.path, [{"t": "question", "text": "Who led the Series B?"}])
        memory.append(self.path, [{"t": "question", "id": "q1", "status": "resolved", "answer": "Northwind"}])

        self.assertEqual(len(self.lines()), 2, "update must append, not rewrite")
        q = memory.fold(self.lines())["question"]["q1"]
        self.assertEqual(q["text"], "Who led the Series B?")  # survived the update
        self.assertEqual(q["status"], "resolved")
        self.assertEqual(q["answer"], "Northwind")

    def test_fold_is_order_dependent_last_write_wins(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        memory.append(self.path, [{"t": "question", "id": "q1", "status": "resolved", "answer": "first"}])
        memory.append(self.path, [{"t": "question", "id": "q1", "answer": "second"}])
        self.assertEqual(memory.fold(self.lines())["question"]["q1"]["answer"], "second")

    def test_none_values_do_not_erase_existing_fields(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        memory.append(self.path, [{"t": "question", "id": "q1", "text": None, "status": "resolved"}])
        self.assertEqual(memory.fold(self.lines())["question"]["q1"]["text"], "x")

    # --- validation -------------------------------------------------------

    def test_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            memory.append(self.path, [{"t": "hypothesis", "text": "x"}])

    def test_rejects_finding_without_url(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        with self.assertRaises(ValueError):
            memory.append(self.path, [{"t": "finding", "q": "q1", "text": "y"}])

    def test_rejects_finding_against_unknown_question(self):
        with self.assertRaises(ValueError):
            memory.append(self.path, [{"t": "finding", "q": "q9", "text": "y", "url": "https://a"}])

    def test_rejects_update_to_unknown_id(self):
        with self.assertRaises(ValueError):
            memory.append(self.path, [{"t": "question", "id": "q7", "status": "resolved"}])

    def test_rejects_bad_status(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        with self.assertRaises(ValueError):
            memory.append(self.path, [{"t": "question", "id": "q1", "status": "blocked"}])

    def test_a_bad_record_writes_nothing_from_its_batch(self):
        memory.append(self.path, [{"t": "question", "text": "x"}])
        before = len(self.lines())
        with self.assertRaises(ValueError):
            memory.append(
                self.path,
                [
                    {"t": "question", "text": "good"},
                    {"t": "finding", "q": "nope", "text": "y", "url": "https://a"},
                ],
            )
        self.assertEqual(len(self.lines()), before, "partial batch must not reach disk")

    # --- rendering --------------------------------------------------------

    def _populated(self):
        memory.append(
            self.path,
            [
                {"t": "question", "text": "Who led the Series B?"},
                {"t": "finding", "q": "q1", "text": "Northwind led the $40M round", "url": "https://tc"},
                {"t": "finding", "q": "q1", "text": "SEC filing lists Northwind", "url": "https://sec"},
                {"t": "question", "id": "q1", "status": "resolved", "answer": "Northwind Capital"},
                {"t": "question", "text": "Was Northwind in the Series A?"},
                {"t": "note", "text": "TechCrunch and SEC disagree on size."},
            ],
        )

    def test_render_groups_by_status_with_findings_nested(self):
        self._populated()
        out = memory.render(META, self.lines())
        self.assertIn("# Objective\nWho backed Acme?", out)
        self.assertIn("3/200 credits used", out)

        open_part, resolved_part = out.split("## Resolved")
        self.assertIn("[q2] Was Northwind in the Series A?", open_part)
        self.assertNotIn("[q1]", open_part)

        self.assertIn("[q1] Who led the Series B? → Northwind Capital", resolved_part)
        self.assertIn("  - [f1] Northwind led the $40M round — https://tc", resolved_part)
        self.assertIn("- [n1] TechCrunch and SEC disagree on size.", resolved_part)

    def test_render_one_question_returns_only_that_question(self):
        self._populated()
        out = memory.render(META, self.lines(), question_id="q1")
        self.assertIn("[q1]", out)
        self.assertIn("[f2]", out)
        self.assertNotIn("q2", out)
        self.assertNotIn("# Objective", out)

    def test_render_empty_memory_says_none(self):
        out = memory.render(META, [])
        self.assertIn("## Open\n_none_", out)

    def test_render_unknown_question_raises(self):
        with self.assertRaises(ValueError):
            memory.render(META, [], question_id="q1")

    # --- durability -------------------------------------------------------

    def test_log_is_valid_jsonl_one_record_per_line(self):
        self._populated()
        for line in self.path.read_text().splitlines():
            self.assertIn("t", json.loads(line))

    def test_survives_a_truncated_trailing_line(self):
        self._populated()
        good = len(self.lines())
        with self.path.open("a") as fh:
            fh.write('{"t": "question", "id": "q9"')  # a crash mid-write
        self.assertEqual(len(self.lines()), good, "torn last line should be dropped")
        self.assertIn("[q1]", memory.render(META, self.lines()))

    def test_appending_after_a_torn_line_still_works(self):
        self._populated()
        with self.path.open("a") as fh:
            fh.write('{"t": "question", "id": "q9"\n')
        memory.append(self.path, [{"t": "question", "text": "recovered"}])
        self.assertIn("recovered", memory.render(META, self.lines()))

    def test_corruption_mid_file_is_not_hidden(self):
        self._populated()
        with self.path.open("a") as fh:
            fh.write('{"t": "question"\n{"t": "note", "id": "n2", "text": "after"}\n')
        with self.assertRaises(json.JSONDecodeError):
            self.lines()


if __name__ == "__main__":
    unittest.main(verbosity=2)
