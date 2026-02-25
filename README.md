# Episteme

Episteme is a structured second-brain knowledgebase, built by your agents for your agents.

It exists so your important knowledge does not vanish into chat history. Episteme turns decisions, procedures, and lessons into durable notes your agents can retrieve, connect, and improve over time.

## Setup

1. Install the Episteme skill pack.

```bash
python3 scripts/install_skill_pack.py --dest auto
```

2. Validate the installation.

```bash
python3 scripts/validate_skill_pack.py --strict
```

3. Initialize your Episteme vault in chat.

```text
Episteme: setup perm=read,propose
```

4. Run a health check.

```text
Episteme: health perm=read,propose
```

That is enough to get started.

## Everyday Use

Ask questions from your existing knowledge:

```text
Episteme: what do we know about our deployment process?
```

Draft updates before writing anything:

```text
Episteme: write an update to our runbook perm=read,propose
```

Apply changes only when you want to:

```text
Episteme: write the approved update perm=read,propose,apply
```

## Command Aliases

You can also use these verbs when needed:
- setup: `init`, `bootstrap`, `repair`
- health: `audit`, `check`
- catalog: `reindex`, `graph`, `rebuild-index`

## Permissions (Simple)

- `perm=read`: read only
- `perm=read,propose`: read + propose changes (recommended default)
- `perm=read,propose,apply`: apply approved changes
- `perm=read,propose,apply,commit`: apply and commit

## Good Habits

- Use `perm=read,propose` unless you explicitly want writes.
- Run `health` before big updates.
- Never store secrets, tokens, or credentials in Episteme notes.

## Help

For script options:

```bash
python3 scripts/install_skill_pack.py --help
python3 scripts/validate_skill_pack.py --help
```
