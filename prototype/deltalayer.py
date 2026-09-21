"""A minimal append-only semantic change layer for project continuity."""
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import sys
from typing import Any


AGENTS_MARKER = "<!-- deltalayer-v0 -->"
DEFAULT_PROJECT = """# Project

## Goal

<!-- Describe the durable project goal here. -->

## Current Architecture

<!-- Keep this view compact and revisable. -->

## Current Stage

<!-- What is true now, not a full history. -->

## Recently Completed

<!-- Durable recent outcomes. -->

## Known Constraints

<!-- Boundaries future agents must preserve. -->

## Open Areas

<!-- Unfinished areas worth considering next. -->
"""

AGENTS_SNIPPET = f"""{AGENTS_MARKER}

## Project Continuity

This project maintains an LLM-native semantic change history.

When starting work:

1. Read `PROJECT.md`.
2. Read the most recent semantic changes.
3. If context is insufficient, continue reading older changes in reverse chronological order.
4. Stop reading history when you judge that you understand enough to safely and correctly perform the current work.
5. Do not scan the full repository merely to reconstruct project history.
6. Use source code, tests, Git, and the actual workspace to verify present implementation when necessary.

While working:

- Maintain a `changes[]` side channel.
- Record durable semantic changes when they occur.
- Do not record reasoning, temporary investigation, ordinary tool activity, or unchanged information.
- `changes: []` is valid when no durable project change occurred.
- Keep historical changes even when a later change supersedes them.
- Before handing control back, check for important durable changes not yet recorded.
- Do not manufacture changes just to create a record.

`PROJECT.md` is a convenient current semantic view, not immutable truth. Reconcile it with recent changes and current reality when needed.
"""


class DeltaError(ValueError):
    """Invalid user input or an invalid stored event."""


@dataclass(frozen=True)
class Event:
    value: dict[str, Any]
    line: int
    timestamp: date | datetime

    @property
    def cursor(self) -> str:
        return format_cursor(self.timestamp, self.line)


@dataclass(frozen=True)
class ReadResult:
    events: list[Event]
    warnings: list[dict[str, Any]]


def parse_timestamp(value: str) -> date | datetime:
    if not isinstance(value, str) or not value.strip():
        raise DeltaError("time must be a non-empty ISO 8601 string")
    text = value.strip().replace("Z", "+00:00")
    try:
        if len(text) == 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text)
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise DeltaError("time must be a valid ISO 8601 date or timestamp") from exc
    if parsed.tzinfo is None:
        raise DeltaError("time must include a timezone offset")
    return parsed


def now_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def format_cursor(timestamp: date | datetime, line: int) -> str:
    return f"{timestamp.isoformat()}#line={line}"


def parse_cursor(value: str) -> tuple[date | datetime, int]:
    if "#line=" not in value:
        return parse_timestamp(value), 0
    timestamp, raw_line = value.rsplit("#line=", 1)
    try:
        line = int(raw_line)
    except ValueError as exc:
        raise DeltaError("cursor line must be an integer") from exc
    if line < 1:
        raise DeltaError("cursor line must be positive")
    return parse_timestamp(timestamp), line


def validate_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeltaError("event must be a JSON object")
    if "time" not in value:
        raise DeltaError("event.time is required")
    parse_timestamp(value["time"])
    source = value.get("source")
    if not isinstance(source, str) or not source.strip():
        raise DeltaError("event.source must be a non-empty string")
    changes = value.get("changes")
    if not isinstance(changes, list) or not all(
        isinstance(item, str) for item in changes
    ):
        raise DeltaError("event.changes must be an array of strings")
    if "conversation_id" in value and value["conversation_id"] is not None:
        if not isinstance(value["conversation_id"], str):
            raise DeltaError("event.conversation_id must be a string")
    return dict(value)


class DeltaStore:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        self.directory = self.root / ".deltalayer"
        self.history_path = self.directory / "changes.jsonl"
        self.project_path = self.root / "PROJECT.md"
        self.agents_path = self.root / "AGENTS.md"

    def init(self) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        created: list[str] = []
        if not self.history_path.exists():
            self.history_path.touch()
            created.append(str(self.history_path))
        if not self.project_path.exists():
            self.project_path.write_text(DEFAULT_PROJECT, encoding="utf-8")
            created.append(str(self.project_path))
        if not self.agents_path.exists():
            self.agents_path.write_text(AGENTS_SNIPPET + "\n", encoding="utf-8")
            created.append(str(self.agents_path))
        else:
            existing = self.agents_path.read_bytes()
            if AGENTS_MARKER.encode("utf-8") not in existing:
                suffix = "" if not existing or existing.endswith(b"\n") else "\n"
                with self.agents_path.open("ab") as stream:
                    stream.write((suffix + "\n" + AGENTS_SNIPPET + "\n").encode("utf-8"))
                created.append(f"appended continuity section to {self.agents_path}")
        return "\n".join(created) if created else "already initialized"

    def append(
        self,
        changes: list[str],
        *,
        source: str,
        conversation_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        event: dict[str, Any] = {
            "time": now_timestamp() if timestamp is None else timestamp,
            "source": source,
            "changes": changes,
        }
        if conversation_id is not None:
            event["conversation_id"] = conversation_id
        event = validate_event(event)
        self.directory.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        with self.history_path.open("a+b") as stream:
            # Preserve a torn final row; separate the next event without repairing history.
            stream.seek(0, os.SEEK_END)
            has_content = stream.tell() > 0
            if has_content:
                stream.seek(-1, os.SEEK_END)
            separator = b"\n" if has_content and stream.read(1) != b"\n" else b""
            stream.write(separator + encoded)
            stream.flush()
            os.fsync(stream.fileno())
        return event

    def _read(self) -> ReadResult:
        if not self.history_path.exists():
            return ReadResult([], [])
        events: list[Event] = []
        warnings: list[dict[str, Any]] = []
        with self.history_path.open("rb") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    value = validate_event(json.loads(line.decode("utf-8")))
                    events.append(
                        Event(value, line_number, parse_timestamp(value["time"]))
                    )
                except (json.JSONDecodeError, UnicodeDecodeError, DeltaError) as exc:
                    warnings.append(
                        {"line": line_number, "error": str(exc), "skipped": True}
                    )
        # Within one append-only file, position is the event order, not wall-clock time.
        events.reverse()
        return ReadResult(events, warnings)

    def recent(self, limit: int = 5) -> ReadResult:
        validate_limit(limit)
        result = self._read()
        return ReadResult(result.events[:limit], result.warnings)

    def older(self, before: str, limit: int = 5) -> ReadResult:
        validate_limit(limit)
        cursor_time, cursor_line = parse_cursor(before)
        result = self._read()
        if cursor_line:
            selected = [event for event in result.events if event.line < cursor_line]
        else:
            if not isinstance(cursor_time, datetime) or any(
                not isinstance(event.timestamp, datetime) for event in result.events
            ):
                raise DeltaError(
                    "date-only values require a full cursor from recent/older"
                )
            selected = [
                event for event in result.events if event.timestamp < cursor_time
            ]
        return ReadResult(selected[:limit], result.warnings)

    def rebuild_context(self, limit: int = 5) -> str:
        result = self.recent(limit)
        project = (
            self.project_path.read_text(encoding="utf-8")
            if self.project_path.exists()
            else "(PROJECT.md is missing.)"
        )
        payload = {
            "project": project,
            "recent_changes": [event_payload(event) for event in result.events],
            "next_before": result.events[-1].cursor if result.events else None,
            "warnings": result.warnings,
            "instruction": "If this context is insufficient, read older changes with the next_before cursor.",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


def validate_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise DeltaError("limit must be an integer between 1 and 1000")


def event_payload(event: Event) -> dict[str, Any]:
    value = dict(event.value)
    value["_line"] = event.line
    value["_cursor"] = event.cursor
    return value


def output_result(result: ReadResult) -> str:
    payload = {
        "events": [event_payload(event) for event in result.events],
        "next_before": result.events[-1].cursor if result.events else None,
        "warnings": result.warnings,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deltalayer")
    parser.add_argument("--root", default=".", help="project directory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    recent = sub.add_parser("recent")
    recent.add_argument("--limit", type=int, default=5)

    older = sub.add_parser("older")
    older.add_argument(
        "--before", required=True,
        help="full cursor from a previous read; ISO time only for fully timestamped histories",
    )
    older.add_argument("--limit", type=int, default=5)

    append = sub.add_parser("append")
    append.add_argument("--source", required=True)
    append.add_argument("--conversation-id")
    append.add_argument("--time")
    append.add_argument(
        "--change",
        action="append",
        dest="changes",
        default=[],
        help="durable semantic change; repeat for multiple changes",
    )

    rebuild = sub.add_parser("rebuild-context")
    rebuild.add_argument("--limit", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        store = DeltaStore(args.root)
        if args.command == "init":
            print(store.init())
        elif args.command == "recent":
            print(output_result(store.recent(args.limit)))
        elif args.command == "older":
            print(output_result(store.older(args.before, args.limit)))
        elif args.command == "append":
            print(
                json.dumps(
                    store.append(
                        args.changes,
                        source=args.source,
                        conversation_id=args.conversation_id,
                        timestamp=args.time,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "rebuild-context":
            print(store.rebuild_context(args.limit))
        return 0
    except (DeltaError, OSError) as exc:
        print(f"deltalayer: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
