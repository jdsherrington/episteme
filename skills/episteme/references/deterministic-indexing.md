# Deterministic Indexing Reference

Load this reference when implementing or auditing deterministic parsing, link extraction, and graph/catalog generation behavior.

## Vault Discovery

- Vault content is all `*.md` under `<VAULT_ROOT>/episteme/`.
- Exclude `episteme/00_INDEX/_*.tsv` from note discovery.
- Discovery must be deterministic and complete.

## Canonical IDs

- Canonical id regex: `^(C|PR|ADR|PJ|PM|BK|ENV|G|IN)-\d{6}$`
- IDs are canonical identity; filenames are not identity.
- Duplicate ids are Tier 0.

## Frontmatter Contract

- Frontmatter starts at byte 0 with `---`.
- Frontmatter ends at next line that is exactly `---`.
- YAML parse failure is Tier 0.
- `created`, `updated`, `review_due` are literal `YYYY-MM-DD` strings.

## Canonical Wikilinks

Only these count as canonical links:
- `[[ID]]`
- `[[ID|Display Alias]]`

Rules:
- `ID` must match canonical regex.
- No whitespace inside brackets.
- Non-canonical `[[...]]` patterns are Tier 2 hygiene warnings.

## Fenced Code Exclusion

- Exclude links inside fenced code blocks.
- Supported fence tokens: triple backticks and triple tildes.
- Fence opens on `^\s{0,3}(```|~~~)` and closes with matching token.
- EOF while fenced: treat remainder as fenced and emit Tier 2 warning.

## `_GRAPH.tsv`

Path: `episteme/00_INDEX/_GRAPH.tsv`

Columns:
1. `id`
2. `links_out_count`
3. `links_in_count`
4. `links_out_ids`
5. `links_in_ids`

Generation:
- Build outbound links from canonical body wikilinks union frontmatter `links`.
- Deduplicate per note.
- Invert for inbound sets.
- Sort rows by `id`.
- Sort id lists lexicographically.
- Unresolved targets remain in outbound lists and are Tier 1 diagnostics.

## `_CATALOG.tsv`

Path: `episteme/00_INDEX/_CATALOG.tsv`

Columns:
1. `id`
2. `title`
3. `type`
4. `domain`
5. `status`
6. `confidence`
7. `stability`
8. `created`
9. `updated`
10. `review_due`
11. `tags`
12. `keywords`
13. `entities`
14. `links_out_count`
15. `links_in_count`

Formatting:
- `tags`, `keywords`, `entities` are comma-separated, sorted values.
- Missing optional fields emit empty string.

## Determinism Rules

- Whole-vault regeneration only.
- Graph first, catalog second.
- Rows sorted by id.
- LF line endings.
- TSV escaping:
  - TAB -> `\\t`
  - newline -> `\\n`
  - carriage return -> `\\r`
- No machine-specific data or runtime timestamps.
