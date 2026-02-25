# Episteme Skill

## Purpose

Episteme is an explicitly invoked skill enabling structured retrieval from and controlled updates to a deterministic, git-backed Markdown knowledge base.

**Hard rule:** If Episteme is not invoked, it does not exist.

### Invocation Triggers

- `Episteme: ...`
- `/episteme ...`

If not invoked:

- Do not retrieve notes.
- Do not reference the vault.
- Do not propose diffs.
- Do not mention Episteme.
- Operate only on current conversation context.

---

## Runtime & Integration Model

### Execution Context

Episteme operates:

- Against a **local filesystem vault**
- Within the same agent runtime
- With direct read/write filesystem access (only when explicitly permitted)
- With permission to execute local git commands (only when explicitly permitted)

No external service is required.

### Canonical Source of Truth

**Notes are the canonical source of truth.** The deterministic index artifacts:

- `episteme/00_INDEX/_GRAPH.tsv`
- `episteme/00_INDEX/_CATALOG.tsv`

are **derived caches** regenerated deterministically from notes as needed. Health, retrieval ranking, and safety checks **report** using the regenerated artifacts for consistency and determinism.

### Permissions and Semantics

Default permissions:

- `perm=read,propose`

User may override:

- `perm=read`
- `perm=read,propose`
- `perm=read,propose,apply`
- `perm=read,propose,apply,commit`

Rules:

- No apply without explicit approval.
- No commit without explicit approval.
- Apply writes files to the working tree.
- Commit runs:
  - `git add`
  - `git commit -m "<message>"`

Push:

- Only if a remote exists.
- Only if explicitly permitted.

### Concurrency & Merge Strategy

Vault may be edited from multiple devices.

Rules:

- If working tree is dirty → abort apply.
- If merge conflict detected → abort apply and report.
- No automatic conflict resolution.
- User must resolve externally before reattempt.

---

## Vault Enumeration

### Vault Root

All Episteme content resides under:

- `<VAULT_ROOT>/episteme/`

### Note Discovery (Deterministic)

Notes are all `*.md` files under `<VAULT_ROOT>/episteme/`, excluding:

- `episteme/00_INDEX/_CATALOG.tsv`
- `episteme/00_INDEX/_GRAPH.tsv`
- any file matching `episteme/00_INDEX/_*.tsv`

Discovery order does not matter; all derived artifacts are deterministically sorted by `id`.

---

## Conversation Scope Rule

When invoked:

- Entire current conversation thread becomes eligible for analysis.
- Only validated, high-value conclusions may be persisted.
- Intermediate reasoning must not be persisted unless explicitly marked draft.
- Prefer final confirmed conclusions.
- Explicitly mark uncertainty.

---

## Canonical ID and Wikilinks

### Canonical ID Format

All note ids MUST match:

- `^(C|PR|ADR|PJ|PM|BK|ENV|G|IN)-\d{6}$`

IDs are the canonical identity; filenames may change without changing identity.

### Canonical Wikilink Format

Canonical link format:

```text
[[id]]
```

Optional display alias allowed:

```text
[[id|Human Title]]
```

Rules:

- Links must resolve via `id`.
- Title-only links are forbidden.
- Unresolved links are permitted for retrieval/indexing but block apply/commit (see Validation Tiers).

### Canonical Wikilink Grammar (Deterministic)

A canonical wikilink is recognized only when it matches this exact grammar:

- Starts with `[[`
- Then an `id` matching `^(C|PR|ADR|PJ|PM|BK|ENV|G|IN)-\d{6}$`
- Optionally followed by `|` and a display alias string that contains no `]`
- Ends with `]]`

Whitespace is **not** permitted inside the brackets (e.g. `[[ C-000001 ]]` is not a link).

Any `[[...]]` that does not match the canonical grammar is treated as plain text for extraction purposes and is reported as a Tier 2 hygiene warning (it is not Tier 0 fatal).

---

## Frontmatter Contract (Deterministic)

### Delimiters (Required)

- Frontmatter MUST begin at byte 0 with a line that is exactly `---`
- Frontmatter MUST end at the next line that is exactly `---`
- Content between these delimiter lines is parsed as YAML frontmatter.

If these conditions are not met (missing start delimiter, missing end delimiter, or a different delimiter), the note is a Tier 0 failure.

### YAML Parsing Rules (Deterministic)

To avoid YAML implementation drift:

- All date-like fields (`created`, `updated`, `review_due`) MUST be literal strings matching `^\d{4}-\d{2}-\d{2}$`
- Scalar values are treated as strings (no implicit typing) except for lists and maps, which must parse as YAML sequences/mappings.
- Unknown fields are permitted and ignored for indexing unless explicitly referenced by the schema.

If YAML parsing fails, the note is a Tier 0 failure.

---

## Fenced Code Link Extraction

Default behavior: exclude wikilinks inside fenced code blocks for stability.

Fences recognized:

- triple backticks
- triple tildes

A fence starts at beginning of line with optional indentation ≤ 3 spaces. A fence may include a language label after the fence token (ignored for state).

### Fence State Machine (Deterministic)

- Open fence on a line matching: `^\s{0,3}(```|~~~)`
- Close fence only on a line that starts with the **same fence token** (`closes`; ~~~ closes ~~~) with optional indentation ≤ 3 spaces.
- If EOF occurs while inside an open fence:
  - Treat the remainder of the file as fenced (links excluded)
  - Emit a Tier 2 hygiene warning for “unclosed fence”

Nested fences are not recognized; the first matching closer ends the fenced region.

---

## Episteme Structure Assumptions

Single vault, local-only, git repository.

```text
episteme/
  00_INDEX/
    DOMAINS/
    TAGS/
    _CATALOG.tsv
    _GRAPH.tsv
  01_CONCEPTS/
  02_BOOKS/
  03_PROCEDURES/
  04_DECISIONS/
  05_PROJECTS/
  06_POSTMORTEMS/
  07_ENVIRONMENT/
  08_INBOX/
  09_GLOSSARY/
  99_META/
```

---

## Deterministic Index Artifacts

### Graph File

Required file:

```text
episteme/00_INDEX/_GRAPH.tsv
```

Columns (TSV):

```text
id
links_out_count
links_in_count
links_out_ids (comma-separated)
links_in_ids (comma-separated)
```

Rules:

- Sorted by `id` ascending.
- Deterministically derived from notes.
- Regenerated during:
  - health
  - apply
  - commit

Enables:

- Orphan detection
- Hub detection
- Deterministic backlink validation

### Catalog File

Catalog path:

```text
episteme/00_INDEX/_CATALOG.tsv
```

Columns (TSV):

```text
id
title
type
domain
status
confidence
stability
created
updated
review_due
tags
keywords
entities
links_out_count
links_in_count
```

Sorted by `id` ascending.

Derived only from:

- Frontmatter
- Computed link graph

### Bootstrap Rule

If `_CATALOG.tsv` or `_GRAPH.tsv` is missing:

- Regenerate both deterministically (graph first, then catalog) before any retrieval.
- Do not apply or commit automatically.

---

## Validation Tiers

Validation is tiered to avoid blocking retrieval due to hygiene issues.

### Tier 0 (Fatal: blocks everything)

Blocks retrieval, health, apply, commit, and index generation.

- Frontmatter delimiter contract violated (missing/invalid `---` boundaries)
- YAML/frontmatter parse failure
- Duplicate ids
- Missing `id` field or id fails canonical regex
- Path traversal/symlink escape (setup context)
- Deterministic note enumeration failure

**Note:** Non-canonical `[[...]]` sequences are **not** Tier 0 unless they prevent parsing the file (they are handled as Tier 2 warnings).

### Tier 1 (Structural: blocks apply/commit; retrieval allowed)

Index generation and retrieval proceed, but apply/commit is blocked until fixed.

- Unresolved/broken links introduced by the proposed change set (see “Apply/Commit Guardrails”)
- Orphan stable notes (definition below)
- Stable notes with fewer than 3 keywords
- `status: stable` + `stability: volatile` missing `review_due`
- Deprecated notes missing supersession linkage
- Missing/outdated required synthesis notes (thresholds)

### Tier 2 (Hygiene: warnings only)

- Overloaded hub notes (links_out_count > 40)
- Inbox notes older than 90 days
- Duplicate/near-duplicate candidates (heuristic)
- Non-canonical `[[...]]` patterns (do not match canonical wikilink grammar)
- Unclosed code fence (EOF inside fence)

---

## Retrieval Policy

### Mandatory Retrieval Rule

When invoked:

1. Retrieval MUST occur before reasoning.
2. Retrieved knowledge MUST inform reasoning.
3. Retrieved knowledge overrides generic assumptions unless explicitly outdated.

Exception: User may say “do not retrieve”.

### Retrieval Output Contract (Deterministic)

Default retrieval returns **top-k = 10** notes.

Returned per note:

- `id`
- `title`
- `type`
- `domain`
- `status`
- `confidence`
- `updated`
- `summary` (from frontmatter)
- `score` (computed)
- `why_selected` (deterministic factor contributions)
- `excerpt` (deterministic)

Deterministic excerpt selection:

- Use the first **12 non-empty body lines** after frontmatter end delimiter
- Excluding:
  - headings (lines starting with `#`)
  - fenced code lines and their contents
- If fewer than 12 eligible lines exist, return all eligible lines.

---

## Deterministic Retrieval Scoring

Retrieval scoring MUST be deterministic.

Score = weighted sum:

| Factor                     | Weight |
| -------------------------- | ------ |
| domain match               | +30    |
| tag overlap                | +20    |
| keyword overlap            | +15    |
| entity overlap             | +15    |
| note type match (intent)   | +15    |
| status = stable            | +10    |
| status = draft             | +5     |
| status = deprecated        | -50    |
| confidence = high          | +10    |
| confidence = medium        | +5     |
| review overdue             | +5     |
| wikilink proximity (1-hop) | +5     |
| superseded                 | -40    |

Superseded (deterministic definition):

A note is considered superseded if either:

- `status: deprecated`, OR
- `superseded_by` is non-empty

Tie-breakers:

1. Higher score
2. Newer `updated` date
3. Lexicographic `id`

---

## Query Normalization (Deterministic)

All query matching for domain/tag/keyword/entity overlap uses:

- Lowercasing
- Split on any non-alphanumeric character (treat `-` as a separator)
- Remove empty tokens
- No stemming, lemmatization, or synonym expansion
- Exact token match only against catalog fields (domain, tags, keywords, entities)

---

## Intent-Aware Type Boosting

Query classification:

| Query Pattern                | Preferred Type |
| ---------------------------- | -------------- |
| "how do", "runbook", "steps" | procedure      |
| "why did", "decision"        | adr            |
| "what is", "define"          | concept        |
| "incident", "failure"        | postmortem     |
| "status", "plan"             | project        |

If matched → apply +15 boost.

---

## Write Policy

### Eligible for Persistence

- Study outcomes
- Book summaries
- Technical procedures
- ADRs
- PRDs
- Postmortems
- Environment facts (non-secret)
- Personal runbooks

### Explicitly Forbidden

- Personal life details
- Sensitive client data
- Credentials
- Secrets
- Tokens
- Private keys

---

## Redaction Policy

No auto-redaction.

If suspected secret detected:

- Abort apply/commit
- Report file + line
- Require manual correction

Detection includes:

- PEM blocks
- AWS/GCP/GitHub token patterns
- `.env` key=value patterns

**Note:** “High entropy strings” are reported as Tier 2 warnings only unless a deterministic entropy algorithm and thresholds are explicitly specified.

---

## Note Schema

### Core Frontmatter

All notes should include:

```yaml
id: <stable-id>
title: "<human-readable title>"
type: concept|book|procedure|adr|project|postmortem|env|index|glossary|inbox
domain: <string>
status: draft|stable|deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high|medium|low
tags: []
summary: "1-2 sentence canonical summary"
links: []
sources: []
```

Optional fields:

```yaml
aliases: []
keywords: []
entities: []
stability: volatile|semi|durable
review_due: YYYY-MM-DD
supersedes: []
superseded_by: []
contradicts: []
```

### Schema Enforcement Notes

- Tier 0 requires that frontmatter delimiters are valid, YAML parses, and `id` is present and valid.
- For `type: inbox`, missing non-identity fields are permitted for indexing:
  - Required for inbox at Tier 0: `id` only (plus valid frontmatter/YAML)
  - Missing `title/type/domain/status/created/updated/confidence` for inbox is Tier 1 (blocks apply/commit) but does not block retrieval/index generation.
- For non-inbox notes, missing core fields (`title`, `type`, `domain`, `status`, `created`, `updated`, `confidence`) is Tier 0.

### Stable Requirements

If `status: stable`:

- `keywords` length ≥ 3
- If `stability: volatile` then `review_due` is required

### Volatile Domain Defaults

The following domains default to:

```yaml
stability: volatile
review_due: created + 30 days
```

Domains:

- tooling
- APIs
- frameworks
- AI models
- vendor services

---

## Append-Only Types

Types:

- `adr`
- `postmortem`

Rules:

- Frontmatter may be corrected (metadata fixes are permitted).
- Body content is append-only:
  - No destructive edits to existing body sections.
  - Corrections appended under an "Amendment" section.
- Supersession allowed.
- Historical integrity preserved.

---

## Synthesis Notes

### Thresholds

- Tag cluster: ≥ 12 stable notes with the tag
- Domain cluster: ≥ 30 stable notes with the domain

If threshold met, a synthesis note is required:

- Tag synthesis: `episteme/00_INDEX/TAGS/<tag>.md`
- Domain synthesis: `episteme/00_INDEX/DOMAINS/<domain>.md`

### Required Synthesis Format (Deterministic)

Synthesis notes MUST:

- Have `type: index`
- Contain sections (exact headings):
  - `## Members`
  - `## Top Takeaways`
  - `## Conflicts / Open Questions`
  - `## Recommended Reading Order`

Membership is defined strictly as:

- Under `## Members`, one canonical wikilink per line, e.g. `- [[C-000123]]`
- Only lines in this section count as membership.

### “Up to Date” Definition

A synthesis note is up to date only if:

1. It lists every member stable note id in that cluster (as defined above).
2. It contains the required sections.
3. Its frontmatter `updated` date ≥ newest member note `updated` date.

---

## Orphan Detection (Clarified)

A stable note is orphaned if:

- `status: stable`
- `_GRAPH.tsv` reports `links_in_count == 0`
- AND (either):
  - (A) A relevant synthesis note exists for its domain or any of its tags, and the note is not listed under that synthesis note’s `## Members`, OR
  - (B) No relevant synthesis note exists; in that case, a stable note with `links_in_count == 0` is orphaned unconditionally.

Orphans are Tier 1 (block apply/commit).

---

## Overloaded Hub Detection

If `links_out_count > 40` → Tier 2 warning only.

---

## Inbox Rules

- Inbox older than 90 days → Tier 2 warning
- Promotion requires full frontmatter and policy checks
- Inbox notes cannot become stable without passing all stable checks

---

## Diff-First Workflow

When proposing changes:

1. Change Summary
2. Files Affected
3. Unified Diffs
4. Rationale
5. Open Questions

No apply without approval.

---

## Apply/Commit Guardrails (Scoped Structural Blocking)

Tier 0 issues MUST be clear before apply/commit.

Tier 1 blocking is scoped to prevent global deadlocks:

Apply/commit is blocked if any of the following is true:

1. The proposed diff introduces a new unresolved wikilink target (new broken link), OR
2. The proposed diff modifies a note that already contains unresolved links (and those remain unresolved), OR
3. The proposed diff modifies `_GRAPH.tsv` / `_CATALOG.tsv` inconsistently with deterministic regeneration, OR
4. Any orphan stable notes exist after regeneration, OR
5. Any stable note requirements fail (keywords/review_due), OR
6. Deprecated supersession linkage requirements fail, OR
7. Required synthesis constraints are violated (where thresholds are met), OR
8. Secrets are detected.

Existing unresolved links in untouched notes do not block committing unrelated changes, but must be reported as Tier 1 debt.

---

## Safety Checks Before Apply/Commit

Before apply/commit:

- Tier 0 clear across all notes
- Deterministically regenerate `_GRAPH.tsv` and `_CATALOG.tsv` (whole-vault regeneration)
- Include regenerated artifacts in the diff set if changed
- No secrets detected (PEM/token/.env patterns)
- Working tree must be clean

If any fail:

- Abort apply/commit
- Report
- Propose corrective diff

---

## Non-Negotiables

- Episteme invisible unless invoked.
- Retrieval precedes reasoning.
- Deterministic scoring.
- Diff-first mandatory.
- Notes are canonical source of truth; TSVs are deterministic derived artifacts.
- Graph and catalog are deterministic and graph-first.
- No apply/commit without explicit permission.
- Canonical links are `[[id]]` / `[[id|...]]` only.
- Validation tiers govern behavior:
  - Tier 0 blocks everything
  - Tier 1 blocks apply/commit (scoped per guardrails)
  - Tier 2 warnings only
