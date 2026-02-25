#!/usr/bin/env python3
"""Install this skill pack into a target skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.exists():
        raise FileNotFoundError(f"skills root does not exist: {skills_root}")

    skills = sorted(
        path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )
    if not skills:
        raise RuntimeError(f"no installable skills found under {skills_root}")
    return skills


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install_skill(skill_dir: Path, dest_root: Path, force: bool) -> None:
    target = dest_root / skill_dir.name
    if target.exists():
        if not force:
            raise FileExistsError(
                f"target already exists: {target}. Re-run with --force to replace it."
            )
        remove_path(target)

    shutil.copytree(skill_dir, target)


def detect_destination(dest_arg: str) -> tuple[Path, str]:
    if dest_arg != "auto":
        return Path(dest_arg).expanduser(), "explicit --dest"

    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return Path(codex_home).expanduser() / "skills", "$CODEX_HOME/skills"

    home = Path.home()
    codex_skills = home / ".codex" / "skills"
    agents_skills = home / ".agents" / "skills"
    fallback = home / ".agent-skills"

    if codex_skills.exists():
        return codex_skills, "~/.codex/skills"
    if agents_skills.exists():
        return agents_skills, "~/.agents/skills"
    return fallback, "~/.agent-skills (fallback)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Episteme skills into a local skills directory."
    )
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parents[1] / "skills"),
        help="Path to the source skills directory. Default: repository skills/ directory.",
    )
    parser.add_argument(
        "--dest",
        default="auto",
        help=(
            "Destination directory for installed skills. Use 'auto' to detect runtime destination "
            "($CODEX_HOME/skills, ~/.codex/skills, ~/.agents/skills, then ~/.agent-skills fallback)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing skill directories in the destination.",
    )
    parser.add_argument(
        "--no-copy-registry",
        action="store_true",
        help="Do not copy skills/registry.yaml into the destination root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    dest_root, destination_source = detect_destination(args.dest)
    dest_root = dest_root.expanduser()
    dest_root.mkdir(parents=True, exist_ok=True)

    skills = discover_skills(skills_root)

    installed: list[str] = []
    for skill_dir in skills:
        install_skill(skill_dir, dest_root, force=args.force)
        installed.append(skill_dir.name)

    if not args.no_copy_registry:
        registry = skills_root / "registry.yaml"
        if registry.is_file():
            shutil.copy2(registry, dest_root / "registry.yaml")

    print(f"Resolved destination: {dest_root.resolve()} (source: {destination_source})")
    print(f"Installed {len(installed)} skill(s):")
    for skill_name in installed:
        print(f"- {skill_name}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
