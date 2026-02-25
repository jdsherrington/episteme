#!/usr/bin/env python3
"""Validate Episteme skill pack structure and cross-file integrity."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,64}$")
SHARED_CONTRACT_TOKEN = "_shared/episteme-contract.md"


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(skill_path: Path) -> tuple[dict[str, str], list[str]]:
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []

    if not lines or lines[0].strip() != "---":
        return {}, ["missing opening frontmatter delimiter '---' at line 1"]

    frontmatter: dict[str, str] = {}
    end_index = None
    for idx, line in enumerate(lines[1:], start=2):
        stripped = line.strip()
        if stripped == "---":
            end_index = idx
            break
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line {idx}: {line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = clean_scalar(value)
        if not key:
            errors.append(f"empty frontmatter key on line {idx}")
            continue
        frontmatter[key] = value

    if end_index is None:
        errors.append("missing closing frontmatter delimiter '---'")

    return frontmatter, errors


def discover_skills(skills_root: Path) -> list[Path]:
    return sorted(
        path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )


def validate_skill(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_path = skill_dir / "SKILL.md"
    frontmatter, parse_errors = parse_frontmatter(skill_path)
    for parse_error in parse_errors:
        errors.append(f"{skill_dir.name}: {parse_error}")

    if parse_errors:
        return errors, warnings

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        errors.append(f"{skill_dir.name}: missing required frontmatter field 'name'")
    elif not NAME_PATTERN.match(name):
        errors.append(
            f"{skill_dir.name}: invalid name '{name}' (expected lowercase letters, digits, hyphens)"
        )
    elif name != skill_dir.name:
        errors.append(
            f"{skill_dir.name}: frontmatter name '{name}' does not match folder name '{skill_dir.name}'"
        )

    if not description:
        errors.append(f"{skill_dir.name}: missing required frontmatter field 'description'")

    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        warnings.append(
            f"{skill_dir.name}: SKILL.md has {line_count} lines (recommended maximum is 500)"
        )

    return errors, warnings


def parse_registry(registry_path: Path) -> tuple[list[dict[str, object]], list[str]]:
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    skills: list[dict[str, object]] = []

    i = 0
    total = len(lines)
    while i < total:
        line = lines[i]
        match_id = re.match(r"^  - id:\s*(\S+)\s*$", line)
        if not match_id:
            i += 1
            continue

        record: dict[str, object] = {
            "id": clean_scalar(match_id.group(1)),
            "path": "",
            "triggers": [],
            "excludes": [],
            "delegates": {},
        }

        i += 1
        active_section: str | None = None
        while i < total:
            current = lines[i]
            if re.match(r"^  - id:\s*", current):
                break

            match_section = re.match(r"^    (triggers|excludes|delegates):\s*$", current)
            if match_section:
                active_section = match_section.group(1)
                i += 1
                continue

            match_path = re.match(r"^    path:\s*(.+)$", current)
            if match_path:
                record["path"] = clean_scalar(match_path.group(1))
                active_section = None
                i += 1
                continue

            if active_section in {"triggers", "excludes"}:
                match_item = re.match(r"^      -\s*(.+)$", current)
                if match_item:
                    cast_list = record[active_section]
                    assert isinstance(cast_list, list)
                    cast_list.append(clean_scalar(match_item.group(1)))
                    i += 1
                    continue

            if active_section == "delegates":
                match_delegate = re.match(r"^      ([a-z0-9-]+):\s*([a-z0-9-]+)\s*$", current)
                if match_delegate:
                    cast_map = record["delegates"]
                    assert isinstance(cast_map, dict)
                    cast_map[match_delegate.group(1)] = match_delegate.group(2)
                    i += 1
                    continue

            i += 1

        if not record["path"]:
            errors.append(f"registry: skill '{record['id']}' missing required field 'path'")

        skills.append(record)

    if not skills:
        errors.append("registry: no skills found")

    return skills, errors


def validate_registry_integrity(skills_root: Path, discovered: list[Path]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    registry_path = skills_root / "registry.yaml"
    if not registry_path.is_file():
        errors.append(f"registry: missing file {registry_path}")
        return errors, warnings

    records, parse_errors = parse_registry(registry_path)
    errors.extend(parse_errors)
    if parse_errors:
        return errors, warnings

    by_id: dict[str, dict[str, object]] = {}
    for record in records:
        skill_id = str(record["id"])
        if skill_id in by_id:
            errors.append(f"registry: duplicate id '{skill_id}'")
            continue
        by_id[skill_id] = record

    discovered_by_name = {path.name: path for path in discovered}

    for skill_id, record in by_id.items():
        path_value = str(record["path"])
        skill_file = skills_root / path_value
        if not skill_file.is_file():
            errors.append(f"registry: skill '{skill_id}' path does not exist: {skill_file}")
            continue

        if skill_file.parent.name != skill_id:
            errors.append(
                f"registry: skill '{skill_id}' path folder '{skill_file.parent.name}' does not match id"
            )

        frontmatter, frontmatter_errors = parse_frontmatter(skill_file)
        if frontmatter_errors:
            errors.append(
                f"registry: skill '{skill_id}' frontmatter parse error at {skill_file}: "
                + "; ".join(frontmatter_errors)
            )
        else:
            skill_name = frontmatter.get("name", "")
            if skill_name != skill_id:
                errors.append(
                    f"registry: skill '{skill_id}' frontmatter name '{skill_name}' does not match id"
                )

        if skill_id not in discovered_by_name:
            errors.append(
                f"registry: skill id '{skill_id}' does not have a discoverable skill folder with SKILL.md"
            )

        content = skill_file.read_text(encoding="utf-8")
        for trigger in record["triggers"]:
            trigger_text = str(trigger)
            if trigger_text not in content:
                errors.append(
                    f"registry: trigger '{trigger_text}' for skill '{skill_id}' is not present in {skill_file}"
                )

    root = by_id.get("episteme")
    if not root:
        errors.append("registry: missing required root skill id 'episteme'")
    else:
        delegates = root.get("delegates", {})
        excludes = root.get("excludes", [])
        assert isinstance(delegates, dict)
        assert isinstance(excludes, list)

        delegate_keys = set(delegates.keys())
        exclude_keys = {str(item) for item in excludes}
        if delegate_keys != exclude_keys:
            errors.append(
                "registry: episteme excludes must exactly match delegate verbs "
                f"(delegates={sorted(delegate_keys)}, excludes={sorted(exclude_keys)})"
            )

        for verb, target in delegates.items():
            if target not in by_id:
                errors.append(
                    f"registry: delegate verb '{verb}' points to unknown target skill '{target}'"
                )
                continue

            target_record = by_id[target]
            target_triggers = {str(item) for item in target_record["triggers"]}
            expected = {f"Episteme: {verb}", f"/episteme {verb}"}
            missing = sorted(expected - target_triggers)
            if missing:
                errors.append(
                    f"registry: delegate verb '{verb}' -> '{target}' missing target triggers {missing}"
                )

    for skill_dir in discovered:
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        if SHARED_CONTRACT_TOKEN not in content:
            errors.append(
                f"{skill_dir.name}: missing shared contract reference containing '{SHARED_CONTRACT_TOKEN}'"
            )

    return errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Episteme skill pack format.")
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parents[1] / "skills"),
        help="Path to the skills root directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    parser.add_argument(
        "--no-registry-check",
        action="store_true",
        help="Skip registry cross-file integrity checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.exists():
        print(f"error: skills root does not exist: {skills_root}", file=sys.stderr)
        return 1

    skills = discover_skills(skills_root)
    if not skills:
        print(f"error: no skill folders with SKILL.md found under {skills_root}", file=sys.stderr)
        return 1

    seen_names: set[str] = set()
    all_errors: list[str] = []
    all_warnings: list[str] = []

    for skill_dir in skills:
        errors, warnings = validate_skill(skill_dir)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

        skill_path = skill_dir / "SKILL.md"
        frontmatter, parse_errors = parse_frontmatter(skill_path)
        if not parse_errors and "name" in frontmatter:
            skill_name = frontmatter["name"]
            if skill_name in seen_names:
                all_errors.append(f"{skill_dir.name}: duplicate skill name '{skill_name}'")
            seen_names.add(skill_name)

    if not args.no_registry_check:
        registry_errors, registry_warnings = validate_registry_integrity(skills_root, skills)
        all_errors.extend(registry_errors)
        all_warnings.extend(registry_warnings)

    for warning in all_warnings:
        print(f"warning: {warning}")

    if args.strict and all_warnings:
        all_errors.extend([f"strict mode: {warning}" for warning in all_warnings])

    if all_errors:
        for error in all_errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skills)} skill(s) under {skills_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
