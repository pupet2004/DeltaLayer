# Example Agent Rules

## Project Continuity

Read `PROJECT.md`, then recent `.deltalayer/changes.jsonl` records. If the
context is insufficient, read older records using the cursor returned by the
reader. Stop when you understand enough to work safely.

Use source code and tests to verify the current implementation. Record only
durable semantic changes. `changes: []` is valid when nothing durable changed.
