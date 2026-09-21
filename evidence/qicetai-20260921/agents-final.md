# Agent Instructions

## Project Continuity

This project uses DeltaLayer for cross-task continuity.

### Before starting work

1. Read `PROJECT.md` first.
2. Read the most recent entries in `.deltalayer/changes.jsonl`.
3. If the current context is insufficient, continue reading older changes in reverse chronological order.
4. Stop when you judge that you understand enough to safely and correctly perform the current task.
5. Do not scan the full repository merely to reconstruct project history. Read source code when needed to verify or implement the current task.

### While working

Maintain a `changes[]` side channel.

Record a change whenever the project undergoes a durable semantic change, such as:

- capability added, removed, or changed;
- bug fixed;
- architecture or implementation direction changed;
- decision made, replaced, or invalidated;
- important fact established;
- project stage or direction changed.

Do not record reasoning, ordinary investigation, tool activity, or temporary work with no lasting effect.

If nothing durable changed, `changes: []` is valid and should not be persisted.

### Before handing control back

1. Check whether all meaningful changes from this work have been recorded.
2. Append non-empty changes to `.deltalayer/changes.jsonl`.
3. Update `PROJECT.md` when the current high-level project state has materially changed.
4. Never rewrite old change history.

`PROJECT.md` is a rebuildable current view.

`.deltalayer/changes.jsonl` is the append-only semantic evolution history.

Current source code, tests, Git, and the actual workspace remain authoritative for the present implementation.
