# Retrieval and Writing Reference

Load this reference when executing retrieval ranking, excerpt generation, and write-policy decisions.

## Retrieval Prerequisites

- Retrieval happens before reasoning when Episteme is invoked.
- Regenerate `_GRAPH.tsv` and `_CATALOG.tsv` if missing before retrieval.
- User can explicitly disable retrieval with a direct instruction.

## Retrieval Output (Default top-k=10)

Per selected note include:
- `id`, `title`, `type`, `domain`, `status`, `confidence`, `updated`
- `summary`
- `score`
- `why_selected`
- deterministic `excerpt`

## Deterministic Excerpt

Use the first 12 non-empty body lines after frontmatter while excluding:
- heading lines (`#...`)
- fenced code blocks and their content

If fewer than 12 eligible lines exist, return all eligible lines.

## Query Normalization

Apply before matching:
- lowercase
- split on non-alphanumeric separators
- treat `-` as separator
- remove empty tokens
- no stemming/synonyms

## Deterministic Scoring

Weighted sum:
- domain match: +30
- tag overlap: +20
- keyword overlap: +15
- entity overlap: +15
- type intent match: +15
- status stable: +10
- status draft: +5
- status deprecated: -50
- confidence high: +10
- confidence medium: +5
- review overdue: +5
- wikilink 1-hop proximity: +5
- superseded: -40

Superseded if:
- `status: deprecated`, or
- `superseded_by` is non-empty.

Tie-breakers:
1. Higher score
2. Newer `updated`
3. Lexicographic `id`

## Intent-Aware Type Boosting

Patterns:
- `how do`, `runbook`, `steps` -> `procedure`
- `why did`, `decision` -> `adr`
- `what is`, `define` -> `concept`
- `incident`, `failure` -> `postmortem`
- `status`, `plan` -> `project`

Matching type gets +15.

## Persistence Policy

Eligible:
- concepts, procedures, books, ADRs, projects, postmortems, environment facts, runbooks

Forbidden:
- personal life details
- sensitive client data
- credentials/secrets/tokens/private keys

## Secret Handling

No auto-redaction. On suspected secret:
- abort apply/commit
- report file + line
- require manual correction

Detectors include:
- PEM blocks
- AWS/GCP/GitHub token patterns
- `.env` key/value patterns
