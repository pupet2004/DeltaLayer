# Agent Instructions

<!-- deltalayer-conversation-v0.2.1 -->

## Project Continuity

This project uses DeltaLayer v0.2.1 for conversation-owned continuity.

### Before starting work

1. Read `PROJECT.md` first when the project provides one.
2. Read recent `.deltalayer/changes/*.json` Conversation Deltas.
3. If context is insufficient, continue through older Deltas, then legacy
   `.deltalayer/changes.jsonl`.
4. Stop when you understand enough to work safely.
5. Verify current reality with source, tests, Git, and the workspace as needed.
6. A new conversation always starts a new Delta and remembers its returned path.

### Conversation ownership

A Conversation Delta is a semantic change record owned by one conversation.
A conversation owns exactly one Delta during its lifetime.

Ownership comes from the current conversation's remembered Delta path, never
from discovering an existing file. Never adopt or update another conversation's
file. Do not use a global `.current` pointer or manufacture a product
conversation ID.

An older `.json` remains readable history. `.frozen.json` is only an optional
archival filename retained by the prototype; it is not a required lifecycle
state.

### While working

Maintain only the current conversation's net durable semantic difference:

```json
{"started_at":"<ISO-8601>","updated_at":"<ISO-8601>","source":"codex","changes":[]}
```

`started_at` and `updated_at` SHOULD use offset-aware ISO 8601 timestamps
when available. Do not invent missing times or timezones or alter legacy
records.

Each change should, when possible, state both:

1. what durable semantic difference occurred;
2. why a future conversation needs to know it for a project decision,
   verification, or boundary.

Express that relevance in the change sentence itself. Do not add `reason`,
`impact`, `type`, `before`, `after`, or other metadata fields.

Do not record transcripts, tool activity, ordinary debugging, temporary
attempts, unchanged facts, ordinary TODOs, or full validation reports.
`changes: []` is valid and must still be persisted.

### Before handing control back

1. Update the current Delta with the final net changes.
2. Update `PROJECT.md` when the high-level current view materially changed.
3. Handoff is a recommendation to future agents, not a storage lifecycle
   transition. `freeze` is not required.
4. Never rewrite old change history or modify another conversation's file.

### Files and authority

`PROJECT.md` is the rebuildable current view.
`.deltalayer/changes/*.json` stores conversation-owned semantic changes.
`.deltalayer/changes.jsonl` is read-only legacy history.
Source, tests, Git, and the actual workspace remain authoritative for present
implementation.

### Local prototype

Use the local DeltaLayer prototype's `start` once per new conversation and
remember the returned `_path`. Use `update --conversation <remembered-path>`
for subsequent tasks. The prototype may expose `freeze` as optional archival
compatibility; do not treat it as a protocol requirement.
