# Example Project

## Goal

Demonstrate a small project that can be continued by another Agent.

## Current Architecture

- A local source tree is the current implementation.
- Tests define behavior that must remain true.
- `.deltalayer/changes.jsonl` stores durable semantic evolution.

## Current Stage

Prototype continuity loop.

## Recently Completed

- Added an append-only change history.

## Known Constraints

- History is evidence of evolution, not execution authority.
- Current source and tests remain authoritative for present behavior.

## Open Areas

- Test the loop on a real multi-session project.
