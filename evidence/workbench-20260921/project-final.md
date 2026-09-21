# Project

## Goal

AI Game Workbench is a Windows-first workspace for long-running AI projects.
Preserve accepted project state across replaceable agents, providers, and
sessions through explicit review and acceptance.

## Current Architecture

- .NET 10 solution: `Workbench.App` (Avalonia desktop UI), `Workbench.Core`,
  `Workbench.Project`, `Workbench.Runtime`, and `Workbench.Storage` (SQLite).
- Agent completion and evidence lead to review and an explicit Authority
  Decision; agent output alone must not mutate accepted project state.
- Codex and OpenCode are execution providers; Godot is the first tested adapter.
- Repository continuity uses `AGENTS.md`, this rebuildable view, and
  `.deltalayer/changes.jsonl`. This protocol does not replace or bypass the
  application's Claim/Handoff/Authority acceptance chain.

## Current Stage

Regression repair and local candidate packaging are complete. The candidate
is still a dirty working-tree build; do not publish it as a committed release.

The 2026-09-21 audit was rerun against the current working tree. The current
baseline is:

- Remove -> reopen -> reconfirm is repaired and covered by App regression tests.
- Migration 032 now advances `user_version` to 32 and is covered by historical
  schema recovery tests.
- Historical migration fixtures now remain compatible with the current
  ProjectRepository contract.
- Default workspace/navigation fixtures now establish governed Project World
  state before entering the workspace.
- Real Codex Worker acceptance and OpenCode/DeepSeek B1 provider gates pass when
  explicitly enabled.
- Local candidate `alpha-rc.20260921-local.1` has a ZIP, source/artifact
  manifests, and 11 passing distribution checks. A reviewed source commit
  and clean-source rebuild remain pending.

## Recently Completed

- Existing source baseline `e4be5fe` clarifies project intake and preserves
  project history through catalog visibility/setup state and Migration 032.
- Current full solution result: 1,251 passed, 0 failed, 6 skipped.
- Current App result: 704 passed, 0 failed, 5 skipped.
- Current Storage result: 321 passed, 0 failed, 0 skipped.
- Release solution build: 0 warnings, 0 errors after replacing blocking task
  operations in the completed-history test with async/await.
- Live Codex three-round Worker acceptance and OpenCode/DeepSeek B1
  Claim/Handoff/Authority acceptance passed earlier on 2026-09-21; they were
  not rerun against the local candidate package.
- Worker handoff parsing now accepts provider camel-case property names.
- Windows publish now fails closed on build failure, invalid paths, existing
  outputs, and source drift; generated manifests record source and ZIP hashes.
- Distribution smoke verifies install/startup/uninstall in isolated paths;
  uninstall rejects running applications and preserves unrelated shortcuts.
- Native DeltaLayer bootstrap enabled in this actual repository on 2026-09-21.
  No older changes were backfilled.

## Known Constraints

- Canonical workspace: `<WORKBENCH_REPO>`.
  The Desktop/workbench copy is not this task's target.
- Windows x64 is the documented distribution target. Live-provider tests are
  opt-in; historical Alpha passes do not certify the current working tree.
- Source, tests, Git, and the actual workspace remain authoritative. Release
  and validation indexes now distinguish historical Alpha gates from the
  current dirty local candidate.
- Live-provider gates depend on local credentials and executables and remain
  opt-in.
- Current package checks do not certify clean-machine onboarding, signing,
  upgrades, full packaged UI acceptance, or graceful exit/restart.

## Open Areas

- Review and commit intended source changes without unrelated local media or
  generated files; rebuild a uniquely versioned candidate from that commit.
- Repeat required release gates against the selected source/package and
  complete clean-machine/provider onboarding before a public release decision.
- Observe native continuity in subsequent tasks; record actual new changes
  without reconstructing the entire repository history.
