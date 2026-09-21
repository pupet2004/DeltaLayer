"""A minimal conversation-granularity semantic change layer for project continuity."""
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


AGENTS_MARKER = "<!-- deltalayer-conversation-v0.2 -->"
LEGACY_FILENAME = "changes.jsonl"
FROZEN_SUFFIX = ".frozen.json"

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

This project uses conversation-granularity DeltaLayer continuity.

When starting a conversation:

1. Read `PROJECT.md`.
2. Read the most recent `.deltalayer/changes/*.json` Conversation Deltas.
3. If context is insufficient, continue through older Conversation Deltas in reverse chronological order.
4. If needed, continue into the legacy `.deltalayer/changes.jsonl` history.
5. Stop when you judge that you understand enough to work safely.
6. Verify present reality with source, tests, Git, and the actual workspace as needed.
7. In a new conversation, always start a new Delta and remember its returned path in this conversation.

Conversation ownership comes from the current conversation's own remembered
Delta path, never from discovering an existing active file.
Reuse that remembered path across tasks in the same conversation. Never adopt,
update, or freeze another conversation's unfinished file. Do not use a global
`.current` pointer. No product-level conversation ID is required.
An older unfrozen `.json` is readable unfinished / active-at-last-write history,
not invalid history; `.frozen.json` indicates a completed handoff.

While working:

- Keep the current Conversation Delta as the net durable semantic difference from conversation start.
- It may be updated during this conversation; rewrite only its own active file.
- `changes: []` is valid and must still be persisted.
- Prefer one to four concise semantic changes, but do not treat that as a schema limit.
- Do not record transcripts, tool activity, ordinary debugging, temporary attempts, or full validation reports.
- `started_at` and `updated_at` SHOULD use offset-aware ISO 8601 timestamps whenever available.
- Do not invent missing times or timezones or rewrite old history.

Before final conversation handoff:

1. Update the current Conversation Delta with its final net changes.
2. Freeze that file.
3. Update `PROJECT.md` when the high-level current view materially changed.
4. Never modify a frozen Conversation Delta or rewrite legacy history.

Freeze is explicit, not automatic at every task response. If the conversation
continues across tasks, keep updating its remembered active Delta until final
handoff. The prototype cannot detect when the product conversation ends.

`PROJECT.md` is a rebuildable current view.
`.deltalayer/changes/*.json` includes active and frozen Conversation Delta history.
`.deltalayer/changes.jsonl` is legacy read-only history.
Source, tests, Git, and the actual workspace remain authoritative for present reality.
"""

Timestamp = date | datetime


class DeltaError(ValueError):
    """Invalid user input or invalid stored continuity data."""


@dataclass(frozen=True)
class HistoryItem:
    value: dict[str, Any]
    kind: str
    path: Path
    line: int | None
    timestamp: Timestamp
    updated_at: Timestamp | None = None
    frozen: bool = False

    @property
    def cursor(self) -> str:
        if self.kind == "conversation":
            return f"conversation:{self.path.name}"
        return format_cursor(self.timestamp, self.line or 0)


@dataclass(frozen=True)
class ReadResult:
    events: list[HistoryItem]
    warnings: list[dict[str, Any]]


def parse_timestamp(value: str) -> Timestamp:
    if not isinstance(value, str) or not value.strip():
        raise DeltaError("time must be a non-empty ISO 8601 date or timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        if len(text) == 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text)
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise DeltaError("time must be a valid ISO 8601 date or timestamp") from exc
    if parsed.tzinfo is None:
        raise DeltaError("timestamp must include a timezone offset")
    return parsed


def now_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def format_cursor(timestamp: Timestamp, line: int) -> str:
    return f"{timestamp.isoformat()}#line={line}"


def parse_cursor(value: str) -> tuple[Timestamp, int]:
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


def validate_changes(changes: Any) -> list[str]:
    if not isinstance(changes, list) or not all(
        isinstance(item, str) for item in changes
    ):
        raise DeltaError("changes must be an array of strings")
    return list(changes)


def validate_source(source: Any) -> str:
    if not isinstance(source, str) or not source.strip():
        raise DeltaError("source must be a non-empty string")
    return source


def validate_legacy_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeltaError("legacy event must be a JSON object")
    if "time" not in value:
        raise DeltaError("legacy event.time is required")
    parse_timestamp(value["time"])
    validate_source(value.get("source"))
    validate_changes(value.get("changes"))
    if "conversation_id" in value and value["conversation_id"] is not None:
        if not isinstance(value["conversation_id"], str):
            raise DeltaError("legacy conversation_id must be a string")
    return dict(value)


def validate_conversation_delta(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeltaError("conversation delta must be a JSON object")
    if "started_at" not in value or "updated_at" not in value:
        raise DeltaError("conversation delta requires started_at and updated_at")
    parse_timestamp(value["started_at"])
    parse_timestamp(value["updated_at"])
    validate_source(value.get("source"))
    validate_changes(value.get("changes"))
    if "conversation_id" in value and value["conversation_id"] is not None:
        if not isinstance(value["conversation_id"], str):
            raise DeltaError("conversation_id must be a string")
    return dict(value)


def validate_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise DeltaError("limit must be an integer between 1 and 1000")


def _timestamp_sort_key(value: Timestamp) -> tuple[int, float | int]:
    if type(value) is datetime:
        return (2, value.timestamp())
    return (1, value.toordinal())


def _safe_filename_component(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return result or "source"


def _timestamp_slug(value: Timestamp) -> str:
    return value.isoformat().replace(":", "-").replace("+", "p")


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")


class DeltaStore:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        self.directory = self.root / ".deltalayer"
        self.legacy_path = self.directory / LEGACY_FILENAME
        self.history_path = self.legacy_path
        self.conversation_dir = self.directory / "changes"
        self.project_path = self.root / "PROJECT.md"
        self.agents_path = self.root / "AGENTS.md"

    def init(self) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.conversation_dir.mkdir(parents=True, exist_ok=True)
        created: list[str] = []
        if not self.legacy_path.exists():
            self.legacy_path.touch()
            created.append(str(self.legacy_path))
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

    def _conversation_path(self, reference: str | Path) -> Path:
        candidate = Path(reference)
        if not candidate.is_absolute():
            direct = self.root / candidate
            candidate = direct if direct.exists() else self.conversation_dir / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.conversation_dir.resolve())
        except ValueError as exc:
            raise DeltaError("conversation path must be inside .deltalayer/changes") from exc
        if not resolved.is_file():
            raise DeltaError(f"conversation delta does not exist: {reference}")
        return resolved

    def _new_conversation_path(self, started_at: Timestamp, source: str) -> Path:
        stem = f"{_timestamp_slug(started_at)}--{_safe_filename_component(source)}"
        for number in range(10000):
            suffix = "" if number == 0 else f"--{number}"
            active = self.conversation_dir / f"{stem}{suffix}.json"
            frozen = self.conversation_dir / f"{stem}{suffix}{FROZEN_SUFFIX}"
            if not active.exists() and not frozen.exists():
                return active
        raise DeltaError("could not allocate a collision-safe conversation filename")

    def _write_new(self, path: Path, value: dict[str, Any]) -> None:
        try:
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as exc:
            raise DeltaError(f"conversation delta already exists: {path.name}") from exc
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())

    def _replace_atomic(self, path: Path, value: dict[str, Any]) -> None:
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = stream.name
                stream.write(_json_bytes(value))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def _conversation_value(self, path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return validate_conversation_delta(value)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DeltaError) as exc:
            raise DeltaError(str(exc)) from exc

    def start(
        self,
        changes: list[str] | None = None,
        *,
        source: str,
        conversation_id: str | None = None,
        started_at: str | None = None,
    ) -> dict[str, Any]:
        self.init()
        source = validate_source(source)
        changes = validate_changes([] if changes is None else changes)
        started_value = parse_timestamp(started_at or now_timestamp())
        started_text = started_value.isoformat()
        value: dict[str, Any] = {
            "started_at": started_text,
            "updated_at": started_text,
            "source": source,
            "changes": changes,
        }
        if conversation_id is not None:
            if not isinstance(conversation_id, str):
                raise DeltaError("conversation_id must be a string")
            value["conversation_id"] = conversation_id
        path = self._new_conversation_path(started_value, source)
        self._write_new(path, value)
        return self._payload(
            HistoryItem(
                value=value,
                kind="conversation",
                path=path,
                line=None,
                timestamp=started_value,
                updated_at=started_value,
            )
        )

    def update(
        self,
        reference: str | Path,
        changes: list[str],
        *,
        updated_at: str | None = None,
    ) -> dict[str, Any]:
        path = self._conversation_path(reference)
        if path.name.endswith(FROZEN_SUFFIX):
            raise DeltaError("frozen conversation delta cannot be updated")
        value = self._conversation_value(path)
        value["changes"] = validate_changes(changes)
        value["updated_at"] = parse_timestamp(updated_at or now_timestamp()).isoformat()
        validate_conversation_delta(value)
        self._replace_atomic(path, value)
        return self._payload(self._item_from_conversation(path, value))

    def show(self, reference: str | Path) -> dict[str, Any]:
        path = self._conversation_path(reference)
        value = self._conversation_value(path)
        return self._payload(self._item_from_conversation(path, value))

    def freeze(self, reference: str | Path) -> dict[str, Any]:
        path = self._conversation_path(reference)
        if path.name.endswith(FROZEN_SUFFIX):
            return self.show(path)
        value = self._conversation_value(path)
        frozen_path = path.with_name(path.stem + FROZEN_SUFFIX)
        if frozen_path.exists():
            raise DeltaError(f"frozen conversation delta already exists: {frozen_path.name}")
        os.replace(path, frozen_path)
        return self._payload(self._item_from_conversation(frozen_path, value))

    def _item_from_conversation(
        self, path: Path, value: dict[str, Any]
    ) -> HistoryItem:
        return HistoryItem(
            value=value,
            kind="conversation",
            path=path,
            line=None,
            timestamp=parse_timestamp(value["started_at"]),
            updated_at=parse_timestamp(value["updated_at"]),
            frozen=path.name.endswith(FROZEN_SUFFIX),
        )

    def _read_conversations(self) -> tuple[list[HistoryItem], list[dict[str, Any]]]:
        items: list[HistoryItem] = []
        warnings: list[dict[str, Any]] = []
        if not self.conversation_dir.exists():
            return items, warnings
        for path in sorted(self.conversation_dir.glob("*.json")):
            try:
                value = self._conversation_value(path)
                items.append(self._item_from_conversation(path, value))
            except DeltaError as exc:
                warnings.append(
                    {
                        "path": str(path.relative_to(self.root)),
                        "error": str(exc),
                        "skipped": True,
                    }
                )
        items.sort(
            key=lambda item: (
                _timestamp_sort_key(item.updated_at or item.timestamp),
                _timestamp_sort_key(item.timestamp),
                item.path.name,
            ),
            reverse=True,
        )
        return items, warnings

    def _read_legacy(self) -> tuple[list[HistoryItem], list[dict[str, Any]]]:
        items: list[HistoryItem] = []
        warnings: list[dict[str, Any]] = []
        if not self.legacy_path.exists():
            return items, warnings
        try:
            stream = self.legacy_path.open("rb")
        except OSError as exc:
            return [], [{"path": str(self.legacy_path), "error": str(exc), "skipped": True}]
        with stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    value = validate_legacy_event(json.loads(line.decode("utf-8")))
                    items.append(
                        HistoryItem(
                            value=value,
                            kind="legacy",
                            path=self.legacy_path,
                            line=line_number,
                            timestamp=parse_timestamp(value["time"]),
                        )
                    )
                except (json.JSONDecodeError, UnicodeDecodeError, DeltaError) as exc:
                    warnings.append(
                        {"line": line_number, "error": str(exc), "skipped": True}
                    )
        items.sort(key=lambda item: item.line or 0, reverse=True)
        return items, warnings

    def _read_all(self) -> ReadResult:
        conversations, conversation_warnings = self._read_conversations()
        legacy, legacy_warnings = self._read_legacy()
        return ReadResult(
            conversations + legacy,
            conversation_warnings + legacy_warnings,
        )

    def recent(self, limit: int = 5) -> ReadResult:
        validate_limit(limit)
        result = self._read_all()
        return ReadResult(result.events[:limit], result.warnings)

    def older(self, before: str, limit: int = 5) -> ReadResult:
        validate_limit(limit)
        result = self._read_all()
        if before.startswith("conversation:") or before.startswith("legacy:"):
            cursor = before
        else:
            timestamp, line = parse_cursor(before)
            if line:
                cursor = format_cursor(timestamp, line)
            else:
                if type(timestamp) is not datetime or any(
                    event.kind == "legacy" and type(event.timestamp) is not datetime
                    for event in result.events
                ):
                    raise DeltaError(
                        "date-only values require a full cursor from recent/older"
                    )
                selected = [
                    event
                    for event in result.events
                    if event.kind == "legacy"
                    and type(event.timestamp) is datetime
                    and event.timestamp < timestamp
                ]
                return ReadResult(selected[:limit], result.warnings)

        matching_index = next(
            (index for index, event in enumerate(result.events) if event.cursor == cursor),
            None,
        )
        if matching_index is None and cursor.startswith("legacy:"):
            try:
                line = int(cursor.split(":", 1)[1])
            except ValueError as exc:
                raise DeltaError("legacy cursor line must be an integer") from exc
            selected = [
                event
                for event in result.events
                if event.kind == "legacy" and (event.line or 0) < line
            ]
            return ReadResult(selected[:limit], result.warnings)
        if matching_index is None:
            raise DeltaError("cursor does not identify a readable history item")
        return ReadResult(
            result.events[matching_index + 1 : matching_index + 1 + limit],
            result.warnings,
        )

    def rebuild_context(self, limit: int = 5) -> str:
        result = self.recent(limit)
        project = (
            self.project_path.read_text(encoding="utf-8")
            if self.project_path.exists()
            else "(PROJECT.md is missing.)"
        )
        semantic = [
            self._payload(event)
            for event in result.events
            if event.value.get("changes")
        ]
        empty = [
            self._payload(event)
            for event in result.events
            if event.kind == "conversation" and not event.value.get("changes")
        ]
        legacy = [
            self._payload(event)
            for event in result.events
            if event.kind == "legacy"
        ]
        payload = {
            "project": project,
            "recent_deltas": [
                item for item in semantic if item.get("_kind") == "conversation"
            ],
            "legacy_fallback": legacy,
            "recent_changes": semantic,
            "empty_conversations": empty,
            "next_before": result.events[-1].cursor if result.events else None,
            "warnings": result.warnings,
            "instruction": "If this context is insufficient, read older Conversation Deltas with next_before; continue into legacy history when needed.",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _payload(self, event: HistoryItem) -> dict[str, Any]:
        value = dict(event.value)
        value["_kind"] = event.kind
        value["_cursor"] = event.cursor
        value["_path"] = str(event.path.relative_to(self.root))
        if event.line is not None:
            value["_line"] = event.line
        if event.kind == "conversation":
            value["_frozen"] = event.frozen
        return value


def output_result(result: ReadResult, store: DeltaStore) -> str:
    return json.dumps(
        {
            "events": [store._payload(event) for event in result.events],
            "next_before": result.events[-1].cursor if result.events else None,
            "warnings": result.warnings,
        },
        ensure_ascii=False,
        indent=2,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deltalayer")
    parser.add_argument("--root", default=".", help="project directory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    start = sub.add_parser("start")
    start.add_argument("--source", required=True)
    start.add_argument("--conversation-id")
    start.add_argument("--started-at")
    start.add_argument("--change", action="append", dest="changes", default=[])

    update = sub.add_parser("update")
    update.add_argument("--conversation", required=True)
    update.add_argument("--updated-at")
    update.add_argument("--change", action="append", dest="changes", default=[])

    for command in ("show", "current", "freeze"):
        view = sub.add_parser(command)
        view.add_argument("--conversation", required=True)

    recent = sub.add_parser("recent")
    recent.add_argument("--limit", type=int, default=5)

    older = sub.add_parser("older")
    older.add_argument("--before", required=True)
    older.add_argument("--limit", type=int, default=5)

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
        elif args.command == "start":
            print(
                json.dumps(
                    store.start(
                        args.changes,
                        source=args.source,
                        conversation_id=args.conversation_id,
                        started_at=args.started_at,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "update":
            print(
                json.dumps(
                    store.update(
                        args.conversation,
                        args.changes,
                        updated_at=args.updated_at,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command in ("show", "current"):
            print(
                json.dumps(
                    store.show(args.conversation),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "freeze":
            print(
                json.dumps(
                    store.freeze(args.conversation),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "recent":
            print(output_result(store.recent(args.limit), store))
        elif args.command == "older":
            print(output_result(store.older(args.before, args.limit), store))
        elif args.command == "rebuild-context":
            print(store.rebuild_context(args.limit))
        return 0
    except (DeltaError, OSError) as exc:
        print(f"deltalayer: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
