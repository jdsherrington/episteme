# Episteme Shared Contract (Normative)

This file is the canonical policy contract shared by all Episteme skills.

If any Episteme skill file disagrees with this contract, this contract wins.

## Validation Tiers

### Tier 0 (Fatal)

Tier 0 blocks retrieval, index generation, apply, and commit.

Tier 0 includes:
- Frontmatter delimiter violations.
- YAML/frontmatter parse failure.
- Missing or invalid canonical note `id`.
- Duplicate ids.
- Deterministic note enumeration failure.
- Path traversal/symlink escape in setup context.
- Deterministic regeneration failure for `_GRAPH.tsv` or `_CATALOG.tsv`.

### Tier 1 (Structural)

Tier 1 is structural debt. Index generation and retrieval may continue when Tier 0 is clear.

Tier 1 includes:
- Unresolved/broken wikilinks.
- Orphan stable notes.
- Stable notes with `< 3` keywords.
- Stable + volatile missing `review_due`.
- Stable + volatile with overdue `review_due`.
- Deprecated notes missing supersession linkage.
- Required synthesis notes missing or outdated (threshold-based).

### Tier 2 (Hygiene)

Tier 2 is warning-only unless a workflow explicitly escalates it.

Tier 2 includes:
- Overloaded hubs.
- Old inbox notes.
- Duplicate/near-duplicate heuristics.
- Non-canonical `[[...]]` patterns.
- Unclosed fenced code blocks.

## Tier-1 Gating Model (Hybrid Scoped)

### Core workflows (`episteme`, `episteme-health`, `episteme-catalog`)

Tier 1 can block apply/commit using scoped guardrails:
- New unresolved links introduced by proposed diffs block apply/commit.
- Existing unresolved links in modified notes block apply/commit.
- Existing unresolved links in untouched notes are Tier 1 debt and are reported.
- Orphan/stability/supersession/synthesis violations block apply/commit after regeneration.

### Setup workflow (`episteme-setup`)

Setup allows `apply` with explicit permission to perform repair/bootstrap actions while Tier 1 exists, but Tier 1 blocks `commit`.

## Review Due Semantics

For `status: stable` and `stability: volatile`:
- Missing `review_due` is Tier 1.
- `review_due` in the past is Tier 1.

## Regeneration Semantics

When Tier 0 is clear:
- `_GRAPH.tsv` and `_CATALOG.tsv` are generated from notes only.
- Regeneration is whole-vault and graph-first.
- Generated artifacts are deterministic and included in diffs when changed.
