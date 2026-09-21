# Project Instructions

## Project Continuity

This project uses DeltaLayer for native cross-task continuity. Apply this
protocol automatically; the user should not need to initialize it manually.

### DeltaLayer Bootstrap

Before starting work, check for `PROJECT.md` and `.deltalayer/changes.jsonl`
in this repository root. Create missing directories and files as needed,
without overwriting existing content.

- Both exist: follow the normal reading rules below.
- History exists, view missing: read the most recent changes, then older
  entries only as needed. Rebuild a concise `PROJECT.md` from that history,
  checking current facts against reliable project material when necessary.
  Rebuilding the view must not modify history.
- View exists, history missing: preserve `PROJECT.md`, create `.deltalayer/`
  and an empty `changes.jsonl`, and record only new semantic changes from now on.
- Both missing: create an empty `.deltalayer/changes.jsonl` and a minimal
  `PROJECT.md` from reliable current material such as README, current Git
  status, and a small amount of source code when needed. Do not fabricate or
  backfill historical changes. Begin native recording with the current task.

### Before Starting Work

1. Read `PROJECT.md` first.
2. Read the most recent entries in `.deltalayer/changes.jsonl`.
3. If context is insufficient, continue reading older changes in reverse
   chronological order.
4. Stop when you understand enough to safely and correctly perform the task.
   Do not read all history merely for completeness.
5. Do not scan the full repository to reconstruct project history or treat
   source code as a history database. Read source, tests, Git, and the actual
   workspace as needed to verify current reality or implement the task.

### While Working

Maintain a `changes[]` side channel for durable semantic changes, including:

- capabilities added, removed, or changed;
- bugs fixed;
- architecture or implementation direction changed;
- decisions made, replaced, or invalidated;
- important facts established or old assumptions invalidated;
- project stage or direction changed.

Successive transitions such as A -> B -> C may each be recorded when they
actually happen. Do not record reasoning, file reads, ordinary tool activity,
temporary investigation, or attempts with no lasting effect.

An empty `changes: []` is valid but must not be persisted.

### PROJECT.md Maintenance

`PROJECT.md` represents the current rebuildable view of the project, not an
append-only historical record.

When durable new facts invalidate, supersede, resolve, or materially change
statements already present in `PROJECT.md`:

- revise or remove stale statements;
- update affected Current Stage, Recently Completed, Known Constraints, and
  Open Areas when appropriate;
- do not retain obsolete current-state claims merely to preserve history;
- preserve historical evolution in `.deltalayer/changes.jsonl` instead of
  keeping stale text in `PROJECT.md`;
- never rewrite old entries in `changes.jsonl`.

Before changing a current-state claim because of uncertainty or conflict,
verify present reality using source, tests, Git, or the actual workspace as
needed.

Before handing control back, if the task produced durable semantic changes,
perform a lightweight consistency check of `PROJECT.md` so its current-state
sections do not contradict newly established facts.

Keep `PROJECT.md` concise: summarize current project state rather than
accumulating task logs or duplicating the entire change history.

- `PROJECT.md` = current project view.
- `.deltalayer/changes.jsonl` = append-only semantic evolution history.
- Source, tests, Git, and workspace = authoritative present reality.

Use semantic judgment about what is stale, what matters, and what needs
updating. This maintenance rule is not an additional governance mechanism.

### Before Handing Control Back

1. Check that all meaningful changes from this work have been recorded.
2. Append non-empty changes to `.deltalayer/changes.jsonl`, using one UTF-8 JSON
   object per line: `{"time":"<ISO-8601 timestamp with timezone>","source":"agent","changes":["<durable semantic change>"]}`.
   Use the actual recording time, not a fabricated historical timestamp.
3. Update `PROJECT.md` when the high-level current project state materially
   changes. Keep it concise, with Goal, Current Architecture, Current Stage,
   Recently Completed, Known Constraints, and Open Areas.
4. Never rewrite, truncate, or delete old change history.

`PROJECT.md` is a rebuildable current view, not immutable truth.
`.deltalayer/changes.jsonl` is the append-only semantic evolution history.
Neither replaces current source code, tests, Git, or the actual workspace as
the authority for present implementation. Distinguish reported findings and
historical validation from checks actually performed in the current task.
