# Episteme Initialize Skill

## Purpose

Initialize or repair a deterministic, git-backed Episteme vault in the user’s home directory.

Setup creates or repairs:

- Standard directory structure
- Deterministic ID counters
- Seed baseline notes
- Deterministic `_GRAPH.tsv` + `_CATALOG.tsv` bootstrap (graph-first)
- Optional git initialization and initial commit (explicit permission only)

**Hard rule:** Setup runs only when explicitly invoked.

---

## Invocation

Triggered via:

- `Episteme: setup`
- `/episteme setup`

Optional flags:

- `adopt=true` (adopt existing git repo)
- `perm=read`
- `perm=read,propose`
- `perm=read,propose,apply`
- `perm=read,propose,apply,commit`

Default:

- `perm=read,propose`

---

## Canonical Source of Truth

- Markdown notes under `<VAULT_ROOT>/episteme/` are canonical.
- `_GRAPH.tsv` and `_CATALOG.tsv` are deterministic derived artifacts.
- Setup always regenerates graph first, then catalog.

---

## Permission Model (Unified)

Allowed permission combinations:

- `perm=read`
- `perm=read,propose`
- `perm=read,propose,apply`
- `perm=read,propose,apply,commit`

Rules:

- No filesystem mutation without `apply`.
- No commit without `commit`.
- Setup never writes outside the resolved vault root.
- Tier 0 validation must pass before apply/commit.

---

## Target Path Resolution (Deterministic)

Vault root:

- macOS / Linux: `~/.episteme`
- Windows: `%USERPROFILE%\.episteme`

All Episteme content MUST reside under:

```text
<VAULT_ROOT>/episteme/
```

### Safety Constraints

- Never write outside `<VAULT_ROOT>`.
- Resolve symlinks before writing.
- If resolved path escapes user home directory → Tier 0 abort.
- No path traversal (`..`) may escape vault root.

---

## Canonical ID Rules

All ids MUST match:

- `^(C|PR|ADR|PJ|PM|BK|ENV|G|IN)-\d{6}$`

IDs are canonical identity and never reused.

---

## Idempotency Rules

Setup must be safe to run multiple times.

### Case 1 — Vault Does Not Exist

- Create `<VAULT_ROOT>`
- Create directory structure
- Initialize git repository
- Create ID counter store
- Seed baseline notes
- Generate `_GRAPH.tsv`
- Generate `_CATALOG.tsv`

### Case 2 — Vault Exists and Is Valid Episteme Vault

- Do NOT overwrite existing notes
- Detect missing required directories/files
- Propose minimal repairs only
- Regenerate `_GRAPH.tsv` and `_CATALOG.tsv`

### Case 3 — Folder Exists but Not a Git Repo

- Refuse
- Report structural conflict
- No mutation

### Case 4 — Git Repo Exists but Not Episteme Layout

Requires explicit:

- `adopt=true`

With `adopt=true`:

- Only create `episteme/` subtree
- Do not modify unrelated repository files
- Still require `apply` to mutate

---

## Directory Layout

Create or ensure:

```text
.episteme/
  episteme/
    00_INDEX/
      DOMAINS/
      TAGS/
      _CATALOG.tsv
      _GRAPH.tsv
      ROOT.md
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
      POLICY.md
      ID_SCHEMA.md
      ID_COUNTERS.json
      VAULT.md
  .git/
```

Directory creation must be idempotent.

---

## ID Counter Store

Path:

```text
episteme/99_META/ID_COUNTERS.json
```

Initial content:

```json
{
  "C": 1,
  "PR": 1,
  "ADR": 1,
  "PJ": 1,
  "PM": 1,
  "BK": 1,
  "ENV": 1,
  "G": 1,
  "IN": 1
}
```

Rules:

- Allocate ID before note creation.
- Increment counter atomically.
- Never reset existing counters.
- Never reuse IDs.

---

## Seed Baseline Notes

Setup creates minimal stable seed notes:

1. `00_INDEX/ROOT.md`
2. `00_INDEX/DOMAINS/README.md`
3. `00_INDEX/TAGS/README.md`
4. `99_META/POLICY.md`
5. `99_META/ID_SCHEMA.md`
6. `99_META/VAULT.md`

### Seed Requirements

All seed notes MUST:

- Have valid canonical `id`
- Match required frontmatter contract
- `status: stable`
- Include ≥ 3 keywords
- Link to at least one other seed note
- Avoid secrets or machine-specific absolute paths
- Use literal date strings (`YYYY-MM-DD`)

### Required Linking Topology

`ROOT.md` links to:

- DOMAINS README
- TAGS README
- POLICY
- ID_SCHEMA
- VAULT

Each of those notes must link back to `ROOT.md`.

This guarantees no orphan stable notes at initialization.

---

## VAULT.md Rules

Must contain frontmatter fields:

- `id`
- `title`
- `type: index`
- `domain: meta`
- `status: stable`
- `created`
- `updated`
- `confidence`
- `keywords` (≥ 3)

Body must include:

- Platform (`windows|macos|linux`)
- Canonical vault root representation:
  - `~/.episteme` (macOS/Linux)
  - `%USERPROFILE%\.episteme` (Windows)

No absolute machine-specific paths allowed.

---

## Graph + Catalog Bootstrap (Graph-First)

Required order:

1. Parse all notes.
2. Validate Tier 0 conditions.
3. Generate `_GRAPH.tsv`.
4. Generate `_CATALOG.tsv`.

If Tier 0 fails → abort.

Tier 1 violations may exist but must be reported.

Outputs must:

- Be whole-vault regenerated
- Use LF (`\n`) line endings
- Be deterministically sorted
- Escape fields per generator rules

---

## Validation Tiers During Setup

### Tier 0 (Abort Setup)

- Frontmatter delimiter violations
- YAML parse failures
- Invalid/missing ids
- Duplicate ids
- Path escape attempts
- Deterministic enumeration failure

### Tier 1 (Block Commit; Allow Apply Only If Explicit)

- Broken links
- Orphan stable notes
- Stable keyword violations
- Missing review_due for volatile stable
- Deprecated missing supersession linkage
- Required synthesis missing (thresholds met)

Setup must not commit if Tier 1 exists.

---

## Git Initialization

With `perm=read,propose,apply`:

- Run `git init` inside `<VAULT_ROOT>` if not already initialized.
- Do not modify global git configuration.
- Do not enforce branch naming.
- Ensure LF line endings for TSV files.
- Do not install hooks.

With `perm=read,propose,apply,commit`:

- Create initial commit:

```text
episteme: initialize vault
```

Abort commit if:

- Working tree not clean
- Tier 0 or Tier 1 violations exist
- Graph/catalog regeneration fails
- Secrets detected

---

## Secret Detection

Before apply or commit:

Scan for:

- PEM blocks
- AWS/GCP/GitHub token patterns
- `.env` key=value patterns

High-entropy string detection is **not** blocking by default unless a deterministic entropy algorithm is specified.

If secrets detected:

- Abort
- Report file + line
- No auto-redaction

---

## Diff-First Output Format

For `perm=read,propose`:

1. Change Summary
2. Files to Create / Update
3. Unified Diffs
4. Planned Shell Commands
5. Rationale
6. Open Questions

For `perm=read,propose,apply`:

- Perform actions
- Show resulting diffs
- Show `git status`
- Confirm `_GRAPH.tsv` and `_CATALOG.tsv` regenerated

For `perm=read,propose,apply,commit`:

- Same as apply
- Show `git log -1`

No automatic commit without explicit permission.

---

## Deterministic Guarantees

- IDs are canonical and never reused.
- Notes are canonical source of truth.
- Graph and catalog are regenerated whole-vault.
- Sorting strictly by id.
- LF line endings enforced for TSV files.
- No writes outside vault root.
- No commit without explicit permission.
- Validation tiers govern behavior.
- Canonical links are `[[id]]` / `[[id|...]]` only.

```

```
