# Episteme Catalog & Graph Generator Skill

Purpose: Regenerate deterministic index artifacts for the Episteme vault:

- `episteme/00_INDEX/_GRAPH.tsv` (link graph)
- `episteme/00_INDEX/_CATALOG.tsv` (metadata catalog)

These artifacts are **derived, deterministic outputs**.  
**Notes are the canonical source of truth.**

---

## Invocation / Triggers

Regeneration is triggered during:

- `Episteme: health`
- Any Apply/Commit operations (if Episteme invoked and permissions allow)
- Bootstrap (if either artifact is missing) prior to any retrieval

Regeneration is always **whole-vault**, never partial.

---

## Canonical Source of Truth

All generation logic derives strictly from:

1. Markdown note files under `<VAULT_ROOT>/episteme/`
2. YAML frontmatter in those notes
3. Canonical wikilinks extracted from bodies (excluding fenced code)

Existing `_GRAPH.tsv` and `_CATALOG.tsv` files are ignored during computation and overwritten if regeneration succeeds.

---

## Artifact Paths

- Graph: `episteme/00_INDEX/_GRAPH.tsv`
- Catalog: `episteme/00_INDEX/_CATALOG.tsv`

---

## Canonical ID Rules

All note ids MUST match:

- `^(C|PR|ADR|PJ|PM|BK|ENV|G|IN)-\d{6}$`

IDs are canonical identity; filenames may change.

Duplicate ids → Tier 0 failure.

---

## Deterministic File Discovery

Notes are all `*.md` files under `<VAULT_ROOT>/episteme/`, excluding:

- `episteme/00_INDEX/_CATALOG.tsv`
- `episteme/00_INDEX/_GRAPH.tsv`
- any file matching `episteme/00_INDEX/_*.tsv`

Enumeration must be deterministic and complete.

Failure to enumerate deterministically → Tier 0.

---

## Frontmatter Contract (Required for Parsing)

### Delimiters

Frontmatter MUST:

- Begin at byte 0 with a line exactly `---`
- End at the next line exactly `---`

If missing start or end delimiter → Tier 0.

### YAML Rules (Deterministic)

- Dates (`created`, `updated`, `review_due`) must be literal strings matching `^\d{4}-\d{2}-\d{2}$`
- Scalars treated as strings (no implicit YAML typing)
- Lists parsed as YAML sequences
- Unknown fields allowed and ignored unless referenced

YAML parse failure → Tier 0.

---

## Validation Tiers (Generator Behavior)

### Tier 0 — Fatal (Abort Generation)

If any Tier 0 violation exists, generator MUST abort and write no outputs.

Tier 0 includes:

- Frontmatter delimiter violation
- YAML parse failure
- Missing `id` (all note types)
- Invalid `id` (fails canonical regex)
- Duplicate ids
- Deterministic enumeration failure

Non-canonical `[[...]]` patterns are **not** Tier 0 unless they prevent deterministic parsing.

---

### Tier 1 — Structural (Generate Outputs; Block Apply/Commit Elsewhere)

Generator MUST still produce `_GRAPH.tsv` and `_CATALOG.tsv` if Tier 0 is clear, even if Tier 1 violations exist.

Tier 1 includes:

- Broken/unresolved wikilinks
- Orphan stable notes
- Stable keywords < 3
- Stable + volatile missing `review_due`
- Deprecated missing supersession linkage
- Missing/outdated required synthesis notes

Tier 1 findings are emitted as diagnostics for health/apply workflows.

---

### Tier 2 — Hygiene (Diagnostics Only)

- Overloaded hubs
- Inbox older than 90 days
- Duplicate/near-duplicate heuristics
- Non-canonical `[[...]]` patterns
- Unclosed fenced code blocks

---

## Determinism Rules (Global)

Applies to both TSV files:

- One line per note.
- Sort strictly by `id` ascending.
- Use literal TAB as delimiter.
- Use `\n` (LF) as line ending regardless of platform.
- Escape field values:
  - Replace literal tab with `\\t`
  - Replace newline with `\\n`
  - Replace carriage return with `\\r`
- Derive values solely from:
  - note YAML frontmatter
  - computed canonical wikilinks
- Do not include:
  - absolute paths
  - machine-specific data
  - system timestamps
- Output must be byte-for-byte reproducible given identical vault contents.

---

## Canonical Link Extraction

### Supported Link Forms

Only these body wikilinks are recognized:

- `[[<id>]]`
- `[[<id>|<display>]]`

Where:

- `<id>` matches canonical id regex
- `<display>` contains no `]`
- No whitespace allowed inside brackets

Example valid:

```text
[[C-000123]]
[[C-000123|Human Title]]
```

Invalid patterns (treated as plain text, Tier 2 warning):

```text
[[ C-000123 ]]
[[Some Title]]
[[C-000123|Alias|Extra]]
```

### Link Sources

Outbound links are the union of:

1. `links:` frontmatter entries (if present)
2. Canonical body wikilinks

Duplicates are de-duplicated per note.

---

## Fenced Code Exclusion

Links inside fenced code blocks are excluded.

Fence recognition rules:

- Fence opens on line matching `^\s{0,3}(```|~~~)`
- Fence closes only with matching fence token
- EOF inside fence:
  - Treat remainder as fenced
  - Emit Tier 2 warning

Nested fences are not recognized.

---

# Graph File: `_GRAPH.tsv`

### Columns (TSV)

```text
id
links_out_count
links_in_count
links_out_ids
links_in_ids
```

### Computation Steps

1. Parse all notes.
2. Collect canonical `id` set.
3. For each note:
   - Compute outbound id set (deduplicated).
4. Build inbound sets by inverting outbound edges.
5. For each id:
   - `links_out_count = len(outbound_set)`
   - `links_in_count = len(inbound_set)`
   - `links_out_ids = ",".join(sorted(outbound_set))`
   - `links_in_ids = ",".join(sorted(inbound_set))`

### Broken Links

Outbound ids that do not resolve:

- Included in `links_out_ids`
- Counted in `links_out_count`
- Flagged as Tier 1 diagnostic

Generation proceeds.

---

# Catalog File: `_CATALOG.tsv`

### Columns (TSV)

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

### Field Formatting

- `tags`, `keywords`, `entities`:
  - Comma-separated
  - Lexicographically sorted
- Missing optional fields → empty string
- Dates emitted exactly as stored

### Required Fields by Type

#### For All Notes (Tier 0):

- `id`

#### For Non-Inbox Notes (Tier 0):

- `title`
- `type`
- `domain`
- `status`
- `created`
- `updated`
- `confidence`

Missing any of the above → Tier 0.

#### For Inbox Notes:

- Only `id` required for Tier 0
- Missing other core fields → Tier 1 diagnostic
- Inbox notes remain indexable

---

## Stable Policy Diagnostics (Tier 1)

If `status: stable`:

- `keywords` length must be ≥ 3
- If `stability: volatile` then `review_due` required

---

## Synthesis Membership Awareness

Generator parses synthesis notes for orphan diagnostics.

Synthesis notes:

- Tag: `episteme/00_INDEX/TAGS/<tag>.md`
- Domain: `episteme/00_INDEX/DOMAINS/<domain>.md`

Membership defined strictly as:

- Under heading `## Members`
- Lines formatted exactly:
  - `- [[ID]]`

Only those lines count.

---

## Orphan Detection Logic (Generator-Level)

A stable note is orphan-risk if:

- `links_in_count == 0`
- AND orphan definition (as defined in core skill) evaluates true

Generator reports orphan diagnostics; Health enforces blocking.

---

## Output Guarantees

On success (Tier 0 clear), generator outputs:

1. `_GRAPH.tsv`
2. `_CATALOG.tsv`

Both:

- Whole-vault regenerated
- Deterministically sorted
- LF line endings
- Escaped fields

If content differs from on-disk versions, differences must be included in any apply/commit diff set.

---

## Failure Behavior

If Tier 0 failure:

- Do not write partial TSV outputs.
- Report:
  - parsing failures
  - invalid/missing ids
  - duplicate ids
  - enumeration failures

If Tier 1 or Tier 2 findings:

- Still generate outputs
- Emit diagnostics for health/apply workflows

---

## Deterministic Guarantees

Given identical vault contents:

- Note enumeration order irrelevant
- Sorting strictly by id
- All lists lexicographically sorted
- Escaping consistent
- LF line endings enforced

Resulting `_GRAPH.tsv` and `_CATALOG.tsv` must be byte-for-byte identical across runs and platforms.
