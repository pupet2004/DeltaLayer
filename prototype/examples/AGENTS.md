# Example Agent Rules

## Project Continuity

This project uses conversation-granularity DeltaLayer continuity.

When starting a conversation:

1. Read `PROJECT.md`.
2. Read the most recent `.deltalayer/changes/*.json` Conversation Deltas.
3. If context is insufficient, continue through older Conversation Deltas in reverse chronological order.
4. If needed, continue into legacy `.deltalayer/changes.jsonl`.
5. Stop when you understand enough to work safely.
6. Use source code and tests to verify the current implementation.
7. In a new conversation, always start a new Delta and remember its returned path in this conversation.

Conversation ownership comes from the current conversation's own remembered
Delta path, never from discovering an existing active file.
Reuse that remembered path across tasks in the same conversation. Never adopt,
update, or freeze another conversation's unfinished file. Do not use a global
`.current` pointer. No product-level conversation ID is required.
An older unfrozen `.json` is readable unfinished / active-at-last-write history,
not invalid history; `.frozen.json` indicates a completed handoff.

While working, keep the current Delta as the net durable semantic difference
from conversation start. It may be updated during this conversation. Changes
must be concise and semantic; `changes: []` is valid and must still be
persisted. Do not record transcripts, tool activity, ordinary debugging,
temporary attempts, or full validation reports.

Before final conversation handoff, update the current Delta, explicitly freeze it, and update
`PROJECT.md` when the high-level current view materially changed. Never modify
a frozen Delta or rewrite legacy history.

Freeze is not automatic at every task response. Keep the remembered active
Delta across tasks until final handoff; the prototype cannot detect that boundary.

`started_at` and `updated_at` SHOULD use offset-aware ISO 8601 timestamps whenever available.
For legacy writers, `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available.
Use the actual recording time with an explicit UTC offset or `Z` when available.
Do not invent missing time or timezone information or rewrite old history.
