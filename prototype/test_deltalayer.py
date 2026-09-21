# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from deltalayer import AGENTS_MARKER, DeltaError, DeltaStore


class ConversationDeltaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = DeltaStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def start(self, number: int, *, source: str = "codex", changes=None):
        return self.store.start(
            [] if changes is None else changes,
            source=source,
            started_at=f"2026-09-21T00:{number:02d}:00+08:00",
        )

    def test_init_creates_conversation_directory_and_preserves_legacy_slot(self):
        self.store.init()
        self.assertTrue(self.store.conversation_dir.is_dir())
        self.assertTrue(self.store.legacy_path.is_file())
        self.assertTrue(self.store.project_path.is_file())
        self.assertIn(AGENTS_MARKER, self.store.agents_path.read_text(encoding="utf-8"))
        self.store.init()
        self.assertEqual(list(self.store.conversation_dir.glob("*.json")), [])

    def test_start_creates_one_persisted_empty_delta(self):
        result = self.start(1)
        path = self.root / result["_path"]
        self.assertTrue(path.is_file())
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["changes"], [])
        self.assertEqual(set(value), {"started_at", "updated_at", "source", "changes"})
        self.assertEqual(len(list(self.store.conversation_dir.glob("*.json"))), 1)
        self.assertEqual(self.store.recent(1).events[0].value["changes"], [])

    def test_same_conversation_update_reuses_one_file(self):
        result = self.start(1, changes=["initial"])
        path = self.root / result["_path"]
        self.store.update(path, ["final"], updated_at="2026-09-21T00:02:00+08:00")
        self.store.update(path, ["final", "boundary"], updated_at="2026-09-21T00:03:00+08:00")
        self.assertEqual(len(list(self.store.conversation_dir.glob("*.json"))), 1)
        shown = self.store.show(result["_path"])
        self.assertEqual(shown["changes"], ["final", "boundary"])
        self.assertEqual(shown["updated_at"], "2026-09-21T00:03:00+08:00")

    def test_current_delta_can_remove_intermediate_temporary_item(self):
        result = self.start(1, changes=["temporary attempt", "durable decision"])
        self.store.update(result["_path"], ["durable decision"])
        self.store.update(result["_path"], [])
        self.assertEqual(self.store.show(result["_path"])["changes"], [])

    def test_freeze_rejects_update_and_new_conversation_does_not_touch_old_bytes(self):
        result = self.start(1, changes=["durable"])
        frozen = self.store.freeze(result["_path"])
        frozen_path = self.root / frozen["_path"]
        before = frozen_path.read_bytes()
        with self.assertRaisesRegex(DeltaError, "frozen"):
            self.store.update(frozen["_path"], ["rewritten"])
        newer = self.start(2, changes=["new conversation"])
        self.assertNotEqual(frozen["_path"], newer["_path"])
        self.assertEqual(frozen_path.read_bytes(), before)
        self.assertTrue(frozen["_frozen"])

    def test_same_started_at_collision_does_not_overwrite(self):
        first = self.store.start(
            ["first"], source="codex", started_at="2026-09-21T01:00:00+08:00"
        )
        second = self.store.start(
            ["second"], source="codex", started_at="2026-09-21T01:00:00+08:00"
        )
        self.assertNotEqual(first["_path"], second["_path"])
        self.assertEqual(len(list(self.store.conversation_dir.glob("*.json"))), 2)
        self.assertEqual(self.store.show(first["_path"])["changes"], ["first"])
        self.assertEqual(self.store.show(second["_path"])["changes"], ["second"])

    def test_new_conversation_does_not_adopt_interrupted_active_delta(self):
        first = self.start(1, changes=["A initial"])
        self.store.update(
            first["_path"], ["A durable"], updated_at="2026-09-21T00:02:00+08:00"
        )
        first_path = self.root / first["_path"]
        before = first_path.read_bytes()
        fresh_store = DeltaStore(self.root)
        second = fresh_store.start(
            source="codex", started_at="2026-09-22T00:00:00+08:00"
        )
        fresh_store.update(
            second["_path"], ["B durable"], updated_at="2026-09-22T00:01:00+08:00"
        )
        self.assertNotEqual(first["_path"], second["_path"])
        self.assertEqual(first_path.read_bytes(), before)
        self.assertEqual(len(list(fresh_store.conversation_dir.glob("*.json"))), 2)
        page = fresh_store.recent(2)
        self.assertEqual(
            [item.value["changes"] for item in page.events], [["B durable"], ["A durable"]]
        )
        self.assertFalse(fresh_store.show(first["_path"])["_frozen"])
        self.assertFalse(page.events[1].frozen)

    def test_recent_reads_newest_conversation_deltas_first(self):
        self.store.start(
            ["old"], source="codex", started_at="2026-09-21T01:00:00+08:00"
        )
        self.store.start(
            ["new"], source="codex", started_at="2026-09-21T03:00:00+08:00"
        )
        self.store.start(
            ["middle"], source="codex", started_at="2026-09-21T02:00:00+08:00"
        )
        result = self.store.recent(3)
        self.assertEqual(
            [item.value["changes"] for item in result.events],
            [["new"], ["middle"], ["old"]],
        )
        self.assertTrue(all(item.kind == "conversation" for item in result.events))

    def test_empty_conversation_is_visible_but_semantically_skipped(self):
        self.start(1)
        context = json.loads(self.store.rebuild_context(1))
        self.assertEqual(context["recent_changes"], [])
        self.assertEqual(len(context["empty_conversations"]), 1)
        self.assertTrue((self.root / context["empty_conversations"][0]["_path"]).exists())

    def test_older_paginates_conversation_files(self):
        for number in range(1, 6):
            self.start(number, changes=[str(number)])
        seen = []
        page = self.store.recent(2)
        while page.events:
            seen.extend(item.value["changes"][0] for item in page.events)
            page = self.store.older(page.events[-1].cursor, 2)
        self.assertEqual(seen, ["5", "4", "3", "2", "1"])

    def test_legacy_history_is_fallback_and_read_only(self):
        self.store.init()
        legacy = (
            b'{"time":"2026-09-20T00:00:00+08:00","source":"legacy",'
            b'"changes":["old"]}\n'
            b'{"time":"2026-09-21","source":"legacy","changes":[]}\n'
        )
        self.store.legacy_path.write_bytes(legacy)
        before = self.store.legacy_path.read_bytes()
        result = self.store.recent(5)
        self.assertEqual([item.kind for item in result.events], ["legacy", "legacy"])
        self.assertEqual(result.events[0].value["time"], "2026-09-21")
        self.store.start(["new"], source="codex", started_at="2026-09-22T00:00:00+08:00")
        self.assertEqual(self.store.legacy_path.read_bytes(), before)

    def test_mixed_conversation_and_legacy_history(self):
        self.store.init()
        self.store.legacy_path.write_text(
            '{"time":"2026-09-21T00:00:00+08:00","source":"legacy","changes":["old"]}\n',
            encoding="utf-8",
        )
        self.start(1, changes=["conversation"])
        result = self.store.recent(2)
        self.assertEqual([item.kind for item in result.events], ["conversation", "legacy"])
        self.assertEqual(
            [item.value["changes"] for item in result.events],
            [["conversation"], ["old"]],
        )

    def test_rebuild_context_contains_project_recent_deltas_and_legacy_fallback(self):
        self.store.init()
        self.store.project_path.write_text("# Current view\n", encoding="utf-8")
        self.store.legacy_path.write_text(
            '{"time":"2026-09-20T00:00:00+08:00","source":"legacy","changes":["old"]}\n',
            encoding="utf-8",
        )
        self.start(1, changes=["new"])
        context = json.loads(self.store.rebuild_context(2))
        self.assertEqual(context["project"], "# Current view\n")
        self.assertEqual(context["recent_deltas"][0]["changes"], ["new"])
        self.assertEqual(context["legacy_fallback"][0]["changes"], ["old"])
        self.assertTrue(context["next_before"])

    def test_malformed_conversation_is_isolated(self):
        self.store.init()
        bad = self.store.conversation_dir / "bad.json"
        bad.write_text("{not json}", encoding="utf-8")
        good = self.start(1, changes=["good"])
        result = self.store.recent(5)
        self.assertEqual([item.value["changes"] for item in result.events], [["good"]])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("bad.json", result.warnings[0]["path"])
        self.assertEqual(self.store.show(good["_path"])["changes"], ["good"])

    def test_malformed_legacy_line_is_isolated(self):
        self.store.init()
        self.store.legacy_path.write_bytes(
            b"{bad}\n"
            b'{"time":"2026-09-21","source":"legacy","changes":["good"]}\n'
        )
        result = self.store.recent(5)
        self.assertEqual([item.value["changes"] for item in result.events], [["good"]])
        self.assertEqual([warning["line"] for warning in result.warnings], [1])

    def test_date_only_conversation_retains_original_precision(self):
        result = self.store.start(
            ["date-only"], source="human", started_at="2026-09-21"
        )
        shown = self.store.show(result["_path"])
        self.assertEqual(shown["started_at"], "2026-09-21")
        self.assertEqual(shown["updated_at"], "2026-09-21")
        self.assertTrue(shown["_cursor"].startswith("conversation:"))

    def test_2500_conversation_files_remain_pageable(self):
        self.store.init()
        base = datetime(2026, 9, 1, tzinfo=timezone.utc)
        for number in range(2500):
            started = (base + timedelta(seconds=number)).isoformat()
            path = self.store.conversation_dir / f"{number:04d}.json"
            value = {
                "started_at": started,
                "updated_at": started,
                "source": "fixture",
                "changes": [str(number)],
            }
            path.write_bytes((json.dumps(value, separators=(",", ":")) + "\n").encode())
        seen = []
        page = self.store.recent(137)
        while page.events:
            self.assertEqual(page.warnings, [])
            seen.extend(int(item.value["changes"][0]) for item in page.events)
            page = self.store.older(page.events[-1].cursor, 137)
        self.assertEqual(seen, list(reversed(range(2500))))

    def test_cli_start_update_current_freeze_and_recent(self):
        command = [
            sys.executable,
            str(Path(__file__).with_name("deltalayer.py")),
            "--root",
            str(self.root),
        ]
        result = subprocess.run(command + ["init"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            command
            + [
                "start",
                "--source",
                "codex",
                "--started-at",
                "2026-09-21T01:00:00+08:00",
                "--change",
                "initial",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        started = json.loads(result.stdout)
        result = subprocess.run(
            command
            + [
                "update",
                "--conversation",
                started["_path"],
                "--updated-at",
                "2026-09-21T01:01:00+08:00",
                "--change",
                "final",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            command + ["current", "--conversation", started["_path"]],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(json.loads(result.stdout)["changes"], ["final"])
        result = subprocess.run(
            command + ["freeze", "--conversation", started["_path"]],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        frozen = json.loads(result.stdout)
        self.assertTrue(frozen["_frozen"])
        result = subprocess.run(
            command + ["update", "--conversation", frozen["_path"], "--change", "bad"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        result = subprocess.run(
            command + ["recent", "--limit", "1"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(json.loads(result.stdout)["events"][0]["changes"], ["final"])

    def test_legacy_time_cursor_remains_compatible(self):
        self.store.init()
        self.store.legacy_path.write_text(
            "\n".join(
                [
                    '{"time":"2026-09-21T00:00:00+08:00","source":"legacy","changes":["a"]}',
                    '{"time":"2026-09-21T01:00:00+08:00","source":"legacy","changes":["b"]}',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        page = self.store.recent(1)
        self.assertEqual(page.events[0].value["changes"], ["b"])
        older = self.store.older("2026-09-21T01:00:00+08:00", 1)
        self.assertEqual(older.events[0].value["changes"], ["a"])

    def test_mixed_precision_legacy_pagination_preserves_append_order(self):
        self.store.init()
        legacy = (
            b'{"time":"2026-09-22T01:00:00+08:00","source":"legacy","changes":["a"]}\n'
            b'{"time":"2026-09-21","source":"legacy","changes":["b"]}\n'
            b'{bad}\n'
            b'{"time":"2026-09-21","source":"legacy","changes":["c"]}\n'
            b'{"time":"2026-09-20T00:00:00Z","source":"legacy","changes":["d"]}\n'
        )
        self.store.legacy_path.write_bytes(legacy)
        self.start(1, changes=["native"])
        page = self.store.recent(2)
        seen = []
        while page.events:
            self.assertEqual([warning["line"] for warning in page.warnings], [3])
            seen.extend(item.value["changes"][0] for item in page.events)
            page = self.store.older(page.events[-1].cursor, 2)
        self.assertEqual(seen, ["native", "d", "c", "b", "a"])
        self.assertEqual(self.store.legacy_path.read_bytes(), legacy)
        for before in ("2026-09-23T00:00:00+08:00", "2026-09-21"):
            with self.assertRaisesRegex(DeltaError, "full cursor"):
                self.store.older(before)


if __name__ == "__main__":
    unittest.main()
