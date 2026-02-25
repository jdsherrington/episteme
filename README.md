# Episteme Skill Pack

Episteme is a deterministic, git-backed knowledge workflow for Markdown vaults. It helps operators retrieve, audit, and update vault knowledge with explicit permission gates and diff-first behavior. This repository contains the Episteme skills, shared contract, registry mapping, and operational scripts.

Hard rule: Episteme is explicit-invocation only. If it is not invoked, it does not run.

This guide is for both:
- operators using Episteme commands in chat
- maintainers operating the skill pack and keeping routing/validation healthy

## Quickstart

### 1. Install the skill pack

```bash
python3 scripts/install_skill_pack.py --dest auto
```

Expected outcome:
- Skills are installed into the detected runtime destination.
- `registry.yaml` is copied by default.
- The script prints the resolved destination and detection source.

### 2. Validate the pack in strict mode

```bash
python3 scripts/validate_skill_pack.py --strict
```

Expected outcome:
- Validation succeeds with `Validated ...` output.
- Any warning is treated as an error in strict mode.

### 3. First-run interaction patterns (in chat)

Setup or bootstrap:
```text
Episteme: setup perm=read,propose
Episteme: bootstrap perm=read,propose,apply
```
Expected outcome:
- Proposes or applies idempotent vault initialization/repair steps.
- Uses graph-first index bootstrap behavior.

Health or audit:
```text
Episteme: health perm=read,propose
Episteme: audit perm=read,propose
```
Expected outcome:
- Regenerates deterministic artifacts for analysis.
- Reports tiered findings and proposes corrective diffs.

Normal query or update:
```text
Episteme: what changed in our API runbooks this month?
Episteme: write an update to the deployment procedure perm=read,propose
```
Expected outcome:
- Retrieval-before-reasoning for query flows.
- Diff-first proposed changes for write flows unless apply is explicitly allowed.

## Invocation Surface

Supported invocation forms:
- `Episteme: ...`
- `/episteme ...`
- `Episteme: <query|write>`
- `/episteme <query|write>`

## Routing and Aliases

Routing source of truth:
- Authoritative dispatch matrix: `skills/episteme/SKILL.md`
- Runtime mapping for non-Codex integrations: `skills/registry.yaml`

If they disagree, `skills/episteme/SKILL.md` is authoritative.

### Routed verbs

| Verb | Routed skill |
| --- | --- |
| `setup` | `episteme-setup` |
| `init` | `episteme-setup` |
| `bootstrap` | `episteme-setup` |
| `repair` | `episteme-setup` |
| `health` | `episteme-health` |
| `audit` | `episteme-health` |
| `check` | `episteme-health` |
| `catalog` | `episteme-catalog` |
| `reindex` | `episteme-catalog` |
| `graph` | `episteme-catalog` |
| `rebuild-index` | `episteme-catalog` |

Any Episteme command without one of the routed subcommands is handled by core `episteme` behavior.

## Effective Usage Patterns

Do this:
- Use `perm=read,propose` by default.
- Run `health` before high-impact apply/commit operations.
- Keep diffs small and review regenerated `_GRAPH.tsv`/`_CATALOG.tsv` updates.
- Treat Tier 1 findings as structural debt to resolve early.

Avoid this:
- Skipping explicit Episteme invocation.
- Requesting apply/commit without explicit permission.
- Treating derived TSV artifacts as canonical source of truth.
- Storing secrets, credentials, or tokens in notes.

## Permissions and Safety

### Permission ladder

| Permission | Typical use |
| --- | --- |
| `perm=read` | Pure analysis/read-only checks |
| `perm=read,propose` | Default mode for retrieval + diff proposals |
| `perm=read,propose,apply` | Apply approved changes to working tree |
| `perm=read,propose,apply,commit` | Full write flow including commit |

### Diff-first expectation

Proposed changes should be presented as:
1. Change summary
2. Files affected
3. Unified diffs
4. Rationale
5. Open questions

### Apply/commit preconditions (practical)

Before apply/commit:
- Tier 0 must be clear.
- Graph/catalog regeneration must succeed and changed artifacts must be included.
- Working tree must be clean.
- No secrets detected.

Secret handling behavior:
- Abort apply/commit.
- Report file and line.
- No auto-redaction.

## Validation Tiers (User View)

- Tier 0: fatal. Blocks retrieval/index/apply/commit.
- Tier 1: structural. Retrieval/index can continue; apply/commit blocking follows scoped guardrails.
- Tier 2: hygiene warnings.

Hybrid setup exception:
- `episteme-setup` may allow `apply` for repair/bootstrap with explicit permission while Tier 1 exists.
- Tier 1 still blocks commit.

Canonical semantics: `skills/_shared/episteme-contract.md`.

## Architecture: Where Truth Lives

- `skills/episteme/SKILL.md`
  - Core behavior + authoritative dispatch matrix.
- `skills/_shared/episteme-contract.md`
  - Canonical validation tiers and gating semantics.
- `skills/episteme/references/`
  - Deterministic indexing, retrieval/writing policy, schema/synthesis rules.
- `skills/registry.yaml`
  - Runtime routing/triggers for integrations.

Canonical data model:
- Notes under `<VAULT_ROOT>/episteme/` are canonical.
- `_GRAPH.tsv` and `_CATALOG.tsv` are derived deterministic artifacts.

## Scripts and Operations

### Installer

```bash
python3 scripts/install_skill_pack.py --help
```

Key flags:
- `--skills-root`
- `--dest` (`auto` supported)
- `--force`
- `--no-copy-registry`

Auto destination order for `--dest auto`:
1. `$CODEX_HOME/skills`
2. `~/.codex/skills`
3. `~/.agents/skills`
4. `~/.agent-skills` (fallback)

Registry behavior:
- `registry.yaml` is copied by default.
- Use `--no-copy-registry` to opt out.

### Validator

```bash
python3 scripts/validate_skill_pack.py --help
```

Key flags:
- `--skills-root`
- `--strict`
- `--no-registry-check`

Use `--no-registry-check` only for scoped local edits where registry integrity is intentionally deferred.

## Troubleshooting

### Strict validation fails

Symptoms:
- `validate_skill_pack.py --strict` exits non-zero.

Actions:
1. Run strict validator and capture errors:
   ```bash
   python3 scripts/validate_skill_pack.py --strict
   ```
2. Resolve routing/trigger/shared-contract reference mismatches.
3. Re-run strict validator.

### Missing trigger parity or alias mismatch

Symptoms:
- Errors mentioning delegate verbs, missing target triggers, or registry-trigger presence.

Actions:
1. Check authoritative dispatch in `skills/episteme/SKILL.md`.
2. Sync `skills/registry.yaml` delegates/triggers to that matrix.
3. Ensure target `SKILL.md` invocation sections include the same aliases.

### Destination conflict during install

Symptoms:
- Installer reports existing target directory conflict.

Actions:
1. Re-run with force when replacement is intended:
   ```bash
   python3 scripts/install_skill_pack.py --dest auto --force
   ```
2. Or use explicit alternate destination via `--dest`.

### Unknown delegate target

Symptoms:
- Validator reports unknown delegate target skill.

Actions:
1. Fix `skills/registry.yaml` delegate target ids.
2. Confirm target folder exists and has matching `name` frontmatter.
3. Re-run strict validator.

### Recommended triage sequence

1. `python3 scripts/validate_skill_pack.py --strict`
2. Inspect dispatch matrix and registry alignment.
3. Run regression tests:
   ```bash
   python3 -m unittest discover -s scripts/tests -v
   ```

## Maintainer Deep Links

- Core skill: [skills/episteme/SKILL.md](skills/episteme/SKILL.md)
- Shared contract: [skills/_shared/episteme-contract.md](skills/_shared/episteme-contract.md)
- Registry: [skills/registry.yaml](skills/registry.yaml)
- Deterministic indexing reference: [skills/episteme/references/deterministic-indexing.md](skills/episteme/references/deterministic-indexing.md)
- Retrieval/writing reference: [skills/episteme/references/retrieval-and-writing.md](skills/episteme/references/retrieval-and-writing.md)
- Note schema/synthesis reference: [skills/episteme/references/note-schema-and-synthesis.md](skills/episteme/references/note-schema-and-synthesis.md)
- Installer script: [scripts/install_skill_pack.py](scripts/install_skill_pack.py)
- Validator script: [scripts/validate_skill_pack.py](scripts/validate_skill_pack.py)
- Script tests: [scripts/tests](scripts/tests)
