# Episteme Health Skill

Invoked via:

- `Episteme: health`
- `/episteme health`

## Purpose

Perform a structural audit, enforce entropy control, and propose corrective diffs for the Episteme vault.

Health is **deterministic** and treats **notes as the canonical source of truth**. The index artifacts:

- `episteme/00_INDEX/_GRAPH.tsv`
- `episteme/00_INDEX/_CATALOG.tsv`

are **derived outputs** regenerated deterministically from notes (graph-first) and then used as the canonical reporting surface for the health report.

Health never applies changes automatically.

---

## Source of Truth and Regeneration Rules

1. **Parse notes (canonical).**
2. **Regenerate `_GRAPH.tsv` deterministically.**
3. **Regenerate `_CATALOG.tsv` deterministically (graph-first dependency).**
4. Run all checks using the regenerated artifacts.
5. If existing TSVs differ from regenerated TSVs, the regenerated TSVs are considered canonical for reporting and are included in proposed diffs.

If regeneration fails, Health must report Tier 0 and abort deeper analysis.

---

## Validation Tiers (Aligned With Core Skill)

Health classifies findings using the global validation tiers.

### Tier 0 — Fatal (Blocks Everything)

If any Tier 0 violation exists, health must:

- Abort further structural analysis
- Report errors
- Propose corrective diffs only (no deeper audit sections)

Tier 0 includes:

- Frontmatter delimiter contract violated (frontmatter must start with `---` at byte 0 and end at the next `---` line)
- YAML/frontmatter parse failures
- Duplicate ids
- Missing `id` or invalid id (must match canonical regex)
- Path traversal/symlink escape (setup context)
- Inability to deterministically enumerate notes
- Inability to deterministically regenerate `_GRAPH.tsv` or `_CATALOG.tsv`

**Note:** Non-canonical `[[...]]` patterns are not Tier 0 unless they prevent deterministic parsing; they are Tier 2 hygiene warnings.

### Tier 1 — Structural (Blocks Apply/Commit)

Retrieval and index generation may proceed, but apply/commit must be blocked until resolved under the apply/commit guardrails.

Tier 1 includes:

- Unresolved/broken wikilinks introduced by the proposed change set (or present in modified notes)
- Orphan stable notes (as defined below)
- Stable notes with `< 3` keywords
- Stable + volatile missing `review_due`
- Deprecated notes missing supersession linkage
- Required synthesis notes missing or outdated (threshold rules)

### Tier 2 — Hygiene (Warnings Only)

- Overloaded hub notes
- Inbox notes older than 90 days
- Duplicate / near-duplicate heuristic matches
- Non-canonical `[[...]]` patterns (do not match canonical wikilink grammar)
- Unclosed fenced code blocks (EOF inside fence)

---

## Bootstrap (Deterministic Regeneration)

If either artifact is missing:

- `_GRAPH.tsv`
- `_CATALOG.tsv`

Health MUST:

1. Parse all notes.
2. Regenerate `_GRAPH.tsv` deterministically.
3. Regenerate `_CATALOG.tsv` deterministically (graph-first).
4. Include regenerated files in proposed diff set.
5. Continue audit using regenerated artifacts.

If regeneration fails → Tier 0 abort.

---

## Deterministic Inputs

Health MUST ground all structural checks in the **regenerated** deterministic artifacts:

- `_CATALOG.tsv`
- `_GRAPH.tsv`

If vault content conflicts with on-disk TSV artifacts:

- Regenerate both.
- Use regenerated outputs for all computations and reporting.
- Include TSV updates in the proposed diff set if changed.

---

## Orphan Definition (Deterministic)

A stable note is orphaned if:

- `status: stable`
- `_GRAPH.tsv` reports `links_in_count == 0`
- AND (either):
  - (A) A relevant synthesis note exists for its domain or any of its tags, and the note is not listed under that synthesis note’s `## Members`, OR
  - (B) No relevant synthesis note exists; in that case, a stable note with `links_in_count == 0` is orphaned unconditionally.

Orphans are Tier 1.

---

## Health Report Structure (Mandatory)

If Tier 0 exists: print Tier 0 errors and stop.

Otherwise, Health report MUST include:

1. Structural Violations (Tier 1)
2. Entropy Risks (Tier 2)
3. Suggested Consolidations
4. Required Synthesis Notes
5. Proposed Diff Set (unified diffs)

---

# Structural Violations (Tier 1)

## 1) Broken Wikilinks (Scoped)

Trigger (for health reporting):

- Any outbound link in `_GRAPH.tsv` that does not resolve to an existing id.

Health report MUST include:

- id
- title
- unresolved target ids
- suggested fix (create note OR correct id)

**Note on apply/commit scope:** Existing unresolved links in untouched notes are reported as Tier 1 debt; apply/commit blocking is governed by the apply/commit guardrails (newly introduced or within modified notes).

---

## 2) Orphan Stable Notes

Trigger:

- Orphan definition above evaluates true.

Report:

- id
- title
- domain
- tags
- links_in_count
- recommended fix:
  - add backlinks (preferred)
  - OR add to appropriate synthesis note (if one exists)
  - OR create the appropriate synthesis note if threshold requires it

---

## 3) Stable Notes Missing Keywords

Trigger:

- `status: stable`
- `keywords` length < 3

Report:

- id
- title
- keyword count
- suggested keyword candidates (derived deterministically from title, tags, entities)

Apply/commit blocked until resolved per guardrails.

---

## 4) Volatile Stable Missing or Overdue Review

### Missing `review_due` (Hard Structural)

Trigger:

- `status: stable`
- `stability: volatile`
- `review_due` missing

Report as Tier 1 violation.

### Overdue Review

Trigger:

- `status: stable`
- `stability: volatile`
- `review_due` in the past

Report:

- id
- title
- review_due
- days overdue
- domain
- tags

Overdue status is Tier 1 (blocks apply/commit).

---

## 5) Deprecated Missing Supersession Linkage

Trigger:

- `status: deprecated`

Must have at least one:

- `superseded_by` non-empty
- OR a body section `## Deprecated` containing canonical link(s) to successor

Report:

- id
- title
- missing field/section
- proposed correction

---

## 6) Required Synthesis Missing or Outdated

### Tag Cluster Threshold

If any tag has:

- ≥ 12 stable notes

Require synthesis:

- `episteme/00_INDEX/TAGS/<tag>.md`

### Domain Cluster Threshold

If any domain has:

- ≥ 30 stable notes

Require synthesis:

- `episteme/00_INDEX/DOMAINS/<domain>.md`

### Synthesis Validation

A synthesis note is up to date only if:

1. Contains required sections:
   - `## Members`
   - `## Top Takeaways`
   - `## Conflicts / Open Questions`
   - `## Recommended Reading Order`
2. Under `## Members`, lists one canonical wikilink per line (`- [[ID]]`)
3. Lists every stable note id in that cluster
4. `updated` date ≥ newest member `updated`

Report:

- tag/domain
- stable note count
- synthesis present? (yes/no)
- up to date? (yes/no)
- missing members (if any)

Missing or outdated synthesis → Tier 1.

---

# Entropy Risks (Tier 2)

## 1) Overloaded Hub Notes

Trigger:

- `_GRAPH.tsv` shows `links_out_count > 40`

Report:

- id
- title
- links_out_count
- top outbound ids (max 10)
- suggested refactor plan

---

## 2) Inbox Older Than 90 Days

Trigger:

- `type: inbox`
- `created` older than 90 days

Report:

- id
- title
- created
- age (days)
- suggested action:
  - promote
  - split
  - archive

---

## 3) Duplicate / Near-Duplicate Candidates

Heuristic signals:

- Similar titles
- High overlap in tags, keywords, entities
- Strong mutual backlinks
- Similar summaries

Report as grouped candidates:

- ids
- titles
- suggested action:
  - merge + deprecate
  - supersession
  - clarify via synthesis

Non-blocking unless user requests enforcement.

---

## 4) Non-Canonical Link Patterns

Trigger:

- Any `[[...]]` sequence that does not match canonical wikilink grammar

Report:

- id
- title
- count of non-canonical patterns
- suggested fix: rewrite to canonical `[[ID]]` / `[[ID|Alias]]` or convert to plain text

---

## 5) Unclosed Fenced Code Blocks

Trigger:

- EOF reached while inside a fence opened by ` ``` ` or `~~~` (indentation ≤ 3 spaces)

Report:

- id
- title
- suggested fix: close the fence with matching token

---

# Suggested Consolidations

Health may propose:

- Merge plans (with supersession)
- Hub splits
- Creation of synthesis notes
- Keyword enrichment
- Backlink additions

No destructive edits to `adr` or `postmortem` bodies (amendments only). Frontmatter corrections are permitted.

---

# Required Synthesis Notes

Health MUST list:

- Tag clusters at/above threshold and synthesis status (present/up-to-date)
- Domain clusters at/above threshold and synthesis status (present/up-to-date)
- Missing members for each synthesis note that exists but is incomplete

---

# Proposed Diff Set (Mandatory Format)

If any Tier 1 violations exist, health MUST include unified diffs for:

- Metadata fixes
- Synthesis creation/updates
- Backlink additions
- Keyword additions
- Regenerated `_GRAPH.tsv`
- Regenerated `_CATALOG.tsv` (if changed)

Diff sections must include:

1. Change Summary
2. Files Affected
3. Unified Diffs
4. Rationale
5. Open Questions

No automatic apply.

---

# Regeneration Rules During Health

Health MUST:

1. Parse all notes.
2. Validate ids against canonical regex.
3. Deterministically regenerate `_GRAPH.tsv`.
4. Deterministically regenerate `_CATALOG.tsv` (graph-first).
5. Use regenerated artifacts for all cluster, orphan, and backlink computations.

If regeneration fails → Tier 0 abort.

---

# Commit/Apply Guardrails (Reference)

Health itself never applies changes. For later apply/commit:

- Tier 0 must be clear across the vault
- Whole-vault `_GRAPH.tsv` and `_CATALOG.tsv` regeneration must succeed and be included
- No secrets detected (PEM/token/.env patterns)
- Working tree must be clean
- Tier 1 blocking is scoped by apply/commit guardrails (newly introduced unresolved links and unresolved links in modified notes block; existing debt in untouched notes is reported but does not block unrelated commits)
