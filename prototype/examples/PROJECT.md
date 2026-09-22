# Example Project

## Goal

Demonstrate a small project that can be continued by another Agent.

## Current Architecture

- A local source tree is the current implementation.
- Tests define behavior that must remain true.
- `.deltalayer/changes/*.json` stores Conversation Deltas owned by individual
  conversations and later read as historical records.
- `.deltalayer/changes.jsonl` is legacy read-only history.

## Current Stage

Prototype continuity loop with conversation-owned Deltas.

## Recently Completed

- Added a conversation-owned semantic change record.
- Handoff is documented as a recommendation, not a Delta lifecycle transition.

## Known Constraints

- A conversation owns exactly one Delta during its lifetime.
- A new conversation always creates its own Delta.
- The current prototype's `freeze` command is optional archival compatibility,
  not a required handoff step.
- History is evidence of evolution, not execution authority.
- Current source and tests remain authoritative for present behavior.

## Open Areas

- Test the loop on a real multi-session project.
