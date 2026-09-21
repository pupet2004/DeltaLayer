# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from deltalayer import DeltaError, DeltaStore, AGENTS_MARKER


class DeltaLayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = DeltaStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_append_single_multiple_empty_and_unicode(self):
        self.store.init()
        first = self.store.append(
            ["新增 native runtime 严格工具参数校验"],
            source="codex",
            timestamp="2026-09-21T16:00:00+08:00",
        )
        second = self.store.append(
            [],
            source="human",
            conversation_id="review-1",
            timestamp="2026-09-21T16:00:00+08:00",
        )
        self.assertEqual(first["changes"], ["新增 native runtime 严格工具参数校验"])
        self.assertEqual(second["changes"], [])
        self.assertEqual(len(self.store.history_path.read_text(encoding="utf-8").splitlines()), 2)

    def test_retrieval_order_and_same_timestamp_cursor(self):
        self.store.init()
        for source in ("first", "second", "third"):
            self.store.append(
                [source],
                source="test",
                timestamp="2026-09-21T16:00:00+08:00",
            )
        first = self.store.recent(2)
        self.assertEqual([item.value["changes"] for item in first.events], [["third"], ["second"]])
        older = self.store.older(first.events[-1].cursor, 2)
        self.assertEqual([item.value["changes"] for item in older.events], [["first"]])

    def test_empty_file_and_malformed_line_are_safe(self):
        self.store.init()
        self.assertEqual(self.store.recent().events, [])
        with self.store.history_path.open("a", encoding="utf-8") as stream:
            stream.write("{not json}\n")
            stream.write(json.dumps({"time": "2026-09-21T16:00:00+08:00"}) + "\n")
        result = self.store.recent()
        self.assertEqual(result.events, [])
        self.assertEqual([warning["line"] for warning in result.warnings], [1, 2])

    def test_invalid_append_is_rejected_without_modifying_old_records(self):
        self.store.init()
        self.store.append(["stable"], source="test", timestamp="2026-09-21T16:00:00+08:00")
        before = self.store.history_path.read_bytes()
        with self.assertRaises(DeltaError):
            self.store.append(["bad", 3], source="test")
        self.assertEqual(self.store.history_path.read_bytes(), before)

    def test_init_preserves_existing_project_and_agents(self):
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "PROJECT.md").write_text("keep project\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("# Existing rules\n", encoding="utf-8")
        self.store.init()
        self.assertEqual((self.root / "PROJECT.md").read_text(encoding="utf-8"), "keep project\n")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(agents.startswith("# Existing rules"))
        self.assertIn(AGENTS_MARKER, agents)
        self.store.init()
        self.assertEqual(agents, (self.root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_cursor_and_limit_validation(self):
        self.store.init()
        with self.assertRaises(DeltaError):
            self.store.recent(0)
        with self.assertRaises(DeltaError):
            self.store.older("2026-09-21T16:00:00", 5)
        with self.assertRaises(DeltaError):
            self.store.append(["x"], source="")

    def test_invalid_inputs_preserve_history_bytes(self):
        self.store.append(["stable"], source="test")
        before = self.store.history_path.read_bytes()
        for changes, source, timestamp in [
            ("not an array", "test", None),
            ({"change": "not an array"}, "test", None),
            (None, "test", None),
            ([], " ", None),
            ([], 42, None),
            ([], "test", ""),
            ([], "test", "2026-09-21T16:00:00"),
            ([], "test", "not a time"),
        ]:
            with self.subTest(changes=changes, source=source, timestamp=timestamp):
                with self.assertRaises(DeltaError):
                    self.store.append(changes, source=source, timestamp=timestamp)
                self.assertEqual(self.store.history_path.read_bytes(), before)

    def test_successful_append_preserves_prefix_and_generates_time(self):
        event = self.store.append(["first"], source="test")
        self.assertIsNotNone(datetime.fromisoformat(event["time"]).tzinfo)
        before = self.store.history_path.read_bytes()
        self.store.append([], source="test")
        self.assertTrue(self.store.history_path.read_bytes().startswith(before))

    def test_append_separates_unterminated_valid_or_malformed_tail(self):
        self.store.init()
        for tail in [b'{"unfinished":', b'\xff', json.dumps({
            "time": "2026-09-21T00:00:00Z", "source": "test", "changes": []
        }).encode("utf-8")]:
            with self.subTest(tail=tail):
                self.store.history_path.write_bytes(tail)
                self.store.append(["new"], source="test", timestamp="2026-09-22T00:00:00Z")
                self.assertTrue(self.store.history_path.read_bytes().startswith(tail + b"\n"))
                result = self.store.recent()
                self.assertEqual(result.events[0].value["changes"], ["new"])
                self.assertEqual(len(result.warnings), 0 if tail.endswith(b"}") else 1)

    def test_init_preserves_existing_bytes(self):
        agents = b"# Existing\r\nDo not rewrite.\r\n"
        project = b"# User view\r\n"
        self.store.agents_path.write_bytes(agents)
        self.store.project_path.write_bytes(project)
        self.store.append(["existing"], source="test")
        history = self.store.history_path.read_bytes()
        self.store.init()
        self.assertTrue(self.store.agents_path.read_bytes().startswith(agents))
        self.assertEqual(self.store.project_path.read_bytes(), project)
        self.assertEqual(self.store.history_path.read_bytes(), history)
        initialized = self.store.agents_path.read_bytes()
        self.store.init()
        self.assertEqual(self.store.agents_path.read_bytes(), initialized)

    def test_time_order_offsets_and_exclusive_time_boundary(self):
        for stamp, change in [
            ("2026-09-21T11:00:00+08:00", "newest"),
            ("2026-09-21T00:00:00Z", "oldest"),
            ("2026-09-21T10:00:00+08:00", "middle"),
        ]:
            self.store.append([change], source="test", timestamp=stamp)
        self.assertEqual(
            [e.value["changes"][0] for e in self.store.recent().events],
            ["newest", "middle", "oldest"],
        )
        self.assertEqual(
            [e.value["changes"][0] for e in self.store.older("2026-09-21T02:00:00Z").events],
            ["oldest"],
        )

    def test_many_records_paginate_without_loss(self):
        self.store.init()
        # A fixture avoids thousands of fsync calls; append durability is tested separately.
        with self.store.history_path.open("w", encoding="utf-8") as stream:
            for number in range(2500):
                stream.write(json.dumps({
                    "time": "2026-09-21T00:00:00Z", "source": "test",
                    "changes": [str(number)],
                }) + "\n")
        seen = []
        page = self.store.recent(137)
        while page.events:
            seen.extend(int(e.value["changes"][0]) for e in page.events)
            page = self.store.older(page.events[-1].cursor, 137)
        self.assertEqual(seen, list(reversed(range(2500))))

    def test_rebuild_context_does_not_rewrite_view(self):
        self.assertIn("missing", json.loads(self.store.rebuild_context())["project"])
        self.store.init()
        self.store.append(["durable"], source="test")
        before = self.store.project_path.read_bytes()
        context = json.loads(self.store.rebuild_context(1))
        self.assertEqual(context["recent_changes"][0]["changes"], ["durable"])
        self.assertTrue(context["next_before"])
        self.assertEqual(self.store.project_path.read_bytes(), before)

    def test_cli_empty_changes_and_error_exit(self):
        command = [sys.executable, str(Path(__file__).with_name("deltalayer.py")),
                   "--root", str(self.root)]
        result = subprocess.run(command + ["append", "--source", "test"],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["changes"], [])
        result = subprocess.run(command + ["recent", "--limit", "0"],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2)
        self.assertIn("limit", result.stderr)


if __name__ == "__main__":
    unittest.main()
