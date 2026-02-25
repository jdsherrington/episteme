---
name: episteme
description: Core Episteme retrieval and write orchestration for deterministic git-backed Markdown knowledge vaults. Use only when the user explicitly invokes `Episteme:` or `/episteme` for normal query/update workflows, excluding setup/init, health/audit, and catalog/reindex commands.
---

# Episteme Skill

## Purpose

Episteme is an explicitly invoked workflow for deterministic retrieval and controlled updates in a local, git-backed Markdown vault.

Hard rule: if Episteme is not invoked, it does not exist.

If not invoked:
- do not retrieve notes
- do not reference the vault
- do not propose diffs
- do not mention Episteme
- operate only on current conversation context

## Invocation Triggers

- `Episteme: ...`
- `/episteme ...`
- `Episteme: <query|write>`
- `/episteme <query|write>`

## Routing Source of Truth (Authoritative)

The dispatch matrix below is the canonical routing source for this skill pack.
If any other file disagrees, this matrix wins.

```yaml
dispatch_matrix:
  setup: episteme-setup
  init: episteme-setup
  bootstrap: episteme-setup
  repair: episteme-setup
  health: episteme-health
  audit: episteme-health
  check: episteme-health
  catalog: episteme-catalog
  reindex: episteme-catalog
  graph: episteme-catalog
  rebuild-index: episteme-catalog
  default: episteme
```

Derived prose dispatch (non-authoritative):
- `setup`, `init`, `bootstrap`, `repair` -> `episteme-setup`
- `health`, `audit`, `check` -> `episteme-health`
- `catalog`, `reindex`, `graph`, `rebuild-index` -> `episteme-catalog`
- anything else -> handle in this skill

## Canonical Shared Contract

All tier semantics, gating behavior, and regeneration policy are canonicalized here:
- [Episteme Shared Contract](../_shared/episteme-contract.md)

This skill follows that contract exactly.

## Progressive Disclosure

Keep this file workflow-focused. Load references only when required:

- [Deterministic Indexing](references/deterministic-indexing.md)
  - load for parsing, canonical links, graph/catalog generation, and deterministic file rules
- [Retrieval and Writing](references/retrieval-and-writing.md)
  - load for scoring, excerpt selection, query normalization, write eligibility, and secret handling
- [Note Schema and Synthesis](references/note-schema-and-synthesis.md)
  - load for schema enforcement, stable rules, synthesis thresholds, orphan logic, and apply/commit guardrails

## Runtime and Integration Model

Episteme operates:
- against a local filesystem vault
- in-process in the current agent runtime
- with explicit permission gating for writes and git actions

No external service is required.

## Permissions

Default: `perm=read,propose`

Allowed combinations:
- `perm=read`
- `perm=read,propose`
- `perm=read,propose,apply`
- `perm=read,propose,apply,commit`

Rules:
- no apply without explicit approval
- no commit without explicit approval
- no push without explicit approval and remote availability
- apply writes working tree changes only
- commit executes `git add` and `git commit -m "<message>"`

## Canonical Source of Truth

Notes under `<VAULT_ROOT>/episteme/` are canonical.

Derived caches:
- `episteme/00_INDEX/_GRAPH.tsv`
- `episteme/00_INDEX/_CATALOG.tsv`

Derived artifacts are regenerated whole-vault and graph-first when required.
Detailed format and determinism rules are in [Deterministic Indexing](references/deterministic-indexing.md).

## Conversation Scope

When invoked:
- entire current conversation is eligible for analysis
- persist only validated, high-value outcomes
- do not persist intermediate reasoning unless explicitly marked draft
- prefer final confirmed conclusions
- mark uncertainty explicitly

## Retrieval Policy

When invoked, retrieval precedes reasoning unless user explicitly says not to retrieve.

Default output:
- top-k = 10 notes
- deterministic score, deterministic excerpt, deterministic tie-breakers

Scoring, excerpting, and normalization details live in:
- [Retrieval and Writing](references/retrieval-and-writing.md)

## Write Policy

Episteme may persist:
- study outcomes
- procedure/runbook updates
- ADR/project/postmortem knowledge
- environment facts (non-secret)

Episteme must not persist:
- credentials, tokens, private keys, secrets
- sensitive client or personal private data

Secret handling policy is in:
- [Retrieval and Writing](references/retrieval-and-writing.md)

## Validation and Guardrails

Validation tiers and gating behavior are defined in:
- [Episteme Shared Contract](../_shared/episteme-contract.md)

Operational implications:
- Tier 0 blocks retrieval/index/apply/commit
- Tier 1 follows hybrid scoped blocking
- Tier 2 is warning-only unless escalated

Guardrails for apply/commit and schema/synthesis/orphan checks:
- [Note Schema and Synthesis](references/note-schema-and-synthesis.md)

## Diff-First Workflow

For proposed changes, output in this order:
1. Change Summary
2. Files Affected
3. Unified Diffs
4. Rationale
5. Open Questions

No apply without explicit approval.

## Apply and Commit Preconditions

Before apply/commit:
- Tier 0 clear
- deterministic regeneration succeeds for graph/catalog
- regenerated artifacts included when changed
- no secrets detected
- working tree clean

If any precondition fails:
- abort apply/commit
- report blockers
- propose corrective diffs

## Non-Negotiables

- Episteme is invisible unless invoked.
- Dispatch routing follows the authoritative dispatch matrix.
- Notes are canonical source of truth.
- Graph/catalog are derived deterministic artifacts.
- Retrieval precedes reasoning (unless user opts out).
- Diff-first output is mandatory.
- No apply/commit without explicit permission.
- Canonical links are ID-based only (`[[ID]]`, `[[ID|Alias]]`).
- Shared contract tier semantics are authoritative.
