# Experiments And Evidence Boundaries

Date: 2026-09-21. Current H5 status: **`PARTIALLY_SUPPORTED`**.

This repository publishes a deliberately limited evidence subset. It does not publish the original session transcripts, source checkout, raw session ids, real fixtures, credentials, or business data.

## Public Materials

- [`public-deltas.jsonl`](experiments/public-deltas.jsonl): 48 anonymized, semantically redacted records.
- [`public-corpus-metrics.json`](experiments/public-corpus-metrics.json): public corpus metrics and separately labeled source-corpus measurements.
- [`public-provenance.json`](experiments/public-provenance.json): anonymous ids, timestamps, source labels and hashes of public records.
- [`phase4-summary.json`](experiments/phase4-summary.json): curated continuation summary.
- [`h5-summary.json`](experiments/h5-summary.json): curated open-ended continuation summary.

The public corpus is a derivative. Product names, framework names, paths, raw task ids and domain-specific names have been generalized. Its byte count therefore cannot reproduce the original corpus byte-for-byte.

## What Was Measured

The private source experiment selected 48 real, successful development tasks and reconstructed one semantic delta per task after the fact. This was not online automatic writing, not a random sample and not a complete session export.

The source-corpus measurements were:

| Material | Characters |
| --- | ---: |
| Concatenated final task messages | 40,555 |
| Compact Delta JSON with metadata | 10,398 |
| Change strings only | 4,585 |
| Exact tokens | `null`, not measured |

The public derivative currently contains 48 records, 9,214 JSONL characters and 13,132 UTF-8 bytes. Its own measurements are in `public-corpus-metrics.json`.

The 4,585-character figure is approximately 11.3% of the source final-message characters. It is not a complete session compression ratio and is not a claim about total token savings. The source history also contained repeated transport/context text, which was deliberately excluded from promotional ratios.

The reconstruction was author-assisted and therefore has hindsight bias: knowing what later mattered may make it easier to write a concise change than it would have been online.

## Continuation Runs

### Phase 4

Three agents continued the same bounded atomic-provenance task under three inputs:

- source-only;
- an existing project summary followed by source inspection;
- recent semantic changes followed by source inspection.

All three completed the focused task and added tests. The task named its implementation boundary, so it was a weak test of long-range continuity. Focused test counts were not directly comparable, and broad suite results were limited by incomplete fixtures and dependencies. See [`phase4-summary.json`](experiments/phase4-summary.json).

### H5

H5 asked agents to identify and implement a real, moderate next task within an existing tool/runtime project without naming the file or function. The three groups converged on strict argument-contract validation at a native tool boundary.

The recorded project-map timing lower bounds were approximately 104 seconds for source-only, 89 seconds for the summary condition, and 103 seconds for the Delta condition. These are incomplete checkpoint measurements, not precise end-to-end timings and not a speed ranking.

The Delta condition read eight task records: three recent records and five older records. It then needed current source and Git metadata. The newer runtime direction was not fully covered by the historical Delta input.

Observed:

- no user re-explanation was needed;
- no group reintroduced the deprecated direction;
- all groups completed focused implementation and tests;
- no reliable reduction in total source archaeology was measured;
- no token savings were measured.

Therefore:

> **H5 = `PARTIALLY_SUPPORTED`**

The evidence supports Delta as a low-cost project-map entry point. It does not establish a significant reduction in total continuation cost, source-code archaeology or tokens, and it does not show superiority over a high-quality handoff.

## Failures We Keep

An earlier understanding run showed that a model could read “not started” as “next step”. This is a real semantic failure, not a detail to hide. It motivates explicit negative language such as “not authorized”, “not started” and “unknown”.

The first Phase 4 attempt did not produce a verifiable completion and is not counted as success. The later rerun did. Retaining that distinction is part of the evidence boundary.

## Native Dogfood — AI Game Workbench

The [2026-09-21 case study](docs/native-dogfood-workbench-20260921.md) documents a real Audit -> Repair -> Validation -> Release preparation relay. The operator confirms that each stage used a fresh Codex conversation, without inherited chat context or the user restating project history. Repository-local `AGENTS.md`, `PROJECT.md`, and recent semantic changes supplied continuity; source, tests, Git, and workspace checks still verified current reality.

This is distinct from the earlier QCT 48-task retrospective reconstruction and its Phase 4/H5 runs. That corpus has hindsight bias. Here the [six preserved records](evidence/workbench-20260921/changes.jsonl) were generated natively online during real work, not backfilled for publication. The [evidence bundle](evidence/workbench-20260921/README.md) contains confirmed prompts, unchanged JSONL, a path-redacted final view, and the final rules snapshot. The rules were clarified during the day; the final snapshot is not proof that all stages used identical instructions.

Recorded outcomes include Storage 321/321, a default suite of 1,251 passed / 0 failed / 6 skipped, separately enabled provider acceptance, and 11 local distribution checks. The final view explicitly distinguishes a dirty working-tree candidate from a committed release. Test results are historical records, not reruns by this publication task. Fresh-conversation isolation, recent-first reading and active removal of stale view claims are operator-confirmed observations; raw sessions and tool-read transcripts are not included.

The observed handoff was usable across several fresh conversations. This is one project, primarily one agent family, one day and a small native history, with no long-horizon degradation or broad multi-agent concurrency evidence. It does not establish general reliability, token savings or comparative cost reduction. **H5 remains `PARTIALLY_SUPPORTED`**, unchanged by this case.

## Native Dogfood Case 2 — Qicetai

The [2026-09-21 Qicetai case](docs/native-dogfood-qicetai-20260921.md) concerns **temporal semantic evolution under unstable external dependencies**, rather than the **cross-conversation continuation** observed in Workbench Case 1. Its [nine native online records](evidence/qicetai-20260921/changes.jsonl) preserve search availability, synthetic-DNS page rejection, temporary network recovery, upstream search timeouts, renewed DNS rejection, and a later URL-safety-boundary fix.

The final view records 183 passing tests (85 original, 98 new security cases) and a fresh-process DeepSeek search -> page -> answer pass under Fake-IP. These are historical reports, not product tests rerun for this archive. Earlier failures remain valid observations of their time; neither this case nor its current view rewrites them into successes. The [evidence bundle](evidence/qicetai-20260921/README.md) redacts one local install path and preserves commit ids, counts and event order.

This corpus is distinct from the QCT retrospective 48 deltas and the Phase 4/H5 continuation experiments. It is one project, one day, primarily one agent environment and a small history, with unstable external dependencies, no long-horizon degradation measurement and no broad concurrent-writer evidence. It does not establish universal temporal reasoning, general reliability or token savings.

The last two records contain date-only `time` values. Native file order preserved their sequence, but at archival time the prototype reader warned and skipped them because it required timezone offsets. This finding motivated the writing guideline: `time` SHOULD use an offset-aware ISO 8601 timestamp whenever available. A subsequent compatibility fix accepts date-only values without inventing times and uses single-file append order for cursor pagination. Read-only verification now retrieves all nine original records without warnings or loss. The case and evidence snapshots retain the original finding unchanged; this repair is not new evidence of agent reliability. **H5 remains `PARTIALLY_SUPPORTED`.**

## Next Falsification Step

The next experiment should use a complete, identical test environment; generate changes online; compare source-only, high-quality handoff, Delta-only and Delta plus current view; use tasks spanning at least two architectural transitions; and record writing, reading, source inspection, rework, correctness and total cost. Unmeasured values should remain `null`.
