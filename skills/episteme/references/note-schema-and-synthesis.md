# Note Schema and Synthesis Reference

Load this reference when validating note schema, stable requirements, synthesis notes, orphan rules, and apply/commit guardrails.

## Core Note Frontmatter

```yaml
id: <stable-id>
title: "<human title>"
type: concept|book|procedure|adr|project|postmortem|env|index|glossary|inbox
domain: <string>
status: draft|stable|deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high|medium|low
tags: []
summary: "1-2 sentence summary"
links: []
sources: []
```

Optional:
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

## Field Requirements

- Tier 0 requires valid frontmatter + valid `id` for all notes.
- Non-inbox notes missing any core fields (`title`, `type`, `domain`, `status`, `created`, `updated`, `confidence`) are Tier 0.
- Inbox notes require `id` at Tier 0; missing non-identity fields are Tier 1.

## Stable Requirements

For `status: stable`:
- `keywords` length >= 3
- `stability: volatile` requires `review_due`
- overdue `review_due` is Tier 1

Volatile defaults for domains:
- tooling
- APIs
- frameworks
- AI models
- vendor services

Default behavior:
```yaml
stability: volatile
review_due: created + 30 days
```

## Append-Only Types

Types:
- `adr`
- `postmortem`

Rules:
- Frontmatter corrections allowed.
- Body is append-only.
- Corrections go under an amendment section.

## Synthesis Thresholds

Create/update synthesis when threshold met:
- Tag cluster: >= 12 stable notes -> `00_INDEX/TAGS/<tag>.md`
- Domain cluster: >= 30 stable notes -> `00_INDEX/DOMAINS/<domain>.md`

Required headings:
- `## Members`
- `## Top Takeaways`
- `## Conflicts / Open Questions`
- `## Recommended Reading Order`

Membership definition:
- under `## Members`, one canonical link per line (`- [[ID]]`)

Up-to-date means:
1. all cluster members listed
2. required headings present
3. synthesis `updated` >= newest member `updated`

## Orphan Rule

Stable note is orphaned when:
- `status: stable`
- `links_in_count == 0`
- and either:
  - relevant synthesis exists but note is missing from members section, or
  - no relevant synthesis exists (unconditional orphan)

## Apply/Commit Guardrails

Before apply/commit:
- Tier 0 clear
- regenerate graph/catalog whole-vault
- include regenerated artifacts when changed
- no secrets
- clean working tree

Tier 1 scoped blocking in core workflows:
- new unresolved links
- unresolved links in modified notes
- orphan/stable/supersession/synthesis violations

Existing unresolved links in untouched notes are reported debt only.

Setup exception:
- apply allowed (with explicit permission) for repair/bootstrap
- commit blocked until Tier 1 clear
