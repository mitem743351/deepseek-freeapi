# ADR-0004: SQLite Message Graph, Structured Parts, and FTS5

- **Status:** Proposed
- **Date:** 2026-08-16

## Context

The legacy database stores linear conversations and opaque message text, with optional reasoning in one column and `%LIKE%` search. Edit, regenerate, compare, citations, tools, attachments, and scalable search require a richer durable model.

## Decision

Continue using SQLite, managed by Rust with explicit numbered migrations.

Represent conversation history as stable messages connected by `parent_message_id` and grouped into explicit branches. Store ordered structured message parts. Store runs and generation metadata separately. Use FTS5 as a derived search index over titles and selected text parts.

Provide an idempotent read-only importer for the legacy two-table database.

## Consequences

Positive:

- branching/edit/regenerate preserve history
- structured rendering and querying
- local, transactional, cross-platform persistence
- scalable full-text search
- existing user data can be migrated

Costs:

- more tables and repository logic
- graph traversal and branch-head invariants
- FTS synchronization/rebuild requirements
- careful legacy ordering reconstruction

## Alternatives considered

### Keep linear messages with a branch index

Rejected because editing/regeneration becomes destructive or duplicates whole histories.

### Store each message as opaque JSON

Rejected because it weakens querying, migrations, integrity, and FTS.

### Move to an external database

Rejected because a local desktop application benefits from embedded SQLite and does not need operational database infrastructure.
