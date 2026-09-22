# Example Agent Rules

## Project Continuity

This project uses DeltaLayer v0.2.1 conversation-owned continuity.

When starting a conversation:

1. Read `PROJECT.md`.
2. Read the most recent `.deltalayer/changes/*.json` Conversation Deltas.
3. If context is insufficient, continue through older Conversation Deltas in reverse chronological order.
4. If needed, continue into legacy `.deltalayer/changes.jsonl`.
5. Stop when you understand enough to work safely.
6. Use source code and tests to verify the current implementation.
7. In a new conversation, always start a new Delta and remember its returned path in this conversation.

Conversation ownership comes from the current conversation's own remembered
Delta path, never from discovering an existing file. A conversation owns
exactly one Delta during its lifetime and may revise its own changes. Reuse
that remembered path across tasks in the same conversation. Never adopt or
update another conversation's file. Do not use a global `.current` pointer.
No product-level conversation ID is required.

When the conversation no longer uses its Delta, the file is historical by
external fact; this is not a stored lifecycle status. An older `.json` remains
readable history, and `.frozen.json` is only an optional archival filename
retained by the prototype.

While working, keep the current Delta as the net durable semantic difference
from conversation start. It may be updated during this conversation. Changes
must be concise and semantic; `changes: []` is valid and must still be
persisted. Do not record transcripts, tool activity, ordinary debugging,
temporary attempts, or full validation reports.

Each change should, when possible, state both what durable semantic difference
occurred and why a future conversation needs to know it for a project decision,
verification, or boundary. Express that relevance in the change sentence
itself; do not add reason, impact, type, before/after, or other metadata fields.

Before handing control back, update the current Delta with the final net
changes and update `PROJECT.md` when the high-level current view materially
changed. Handoff is a recommendation to future agents, not a storage
lifecycle transition; do not require `freeze`. Never modify another
conversation's file or rewrite legacy history.

The prototype still exposes `freeze` as an optional archival operation for
compatibility. It is not required at every task response or final handoff.

`started_at` and `updated_at` SHOULD use offset-aware ISO 8601 timestamps whenever available.
For legacy writers, `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.
Use the actual recording time with an explicit UTC offset or `Z` when available.
Do not invent missing time or timezone information or rewrite old history.
