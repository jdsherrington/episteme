from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "scripts" / "install_skill_pack.py"


def create_sample_pack(root: Path) -> Path:
    skills_root = root / "skills"
    (skills_root / "episteme").mkdir(parents=True, exist_ok=True)
    (skills_root / "episteme-setup").mkdir(parents=True, exist_ok=True)

    (skills_root / "episteme" / "SKILL.md").write_text(
        textwrap.dedent(
            """\
            ---
            name: episteme
            description: core
            ---

            # Episteme
            """
        ),
        encoding="utf-8",
    )
    (skills_root / "episteme-setup" / "SKILL.md").write_text(
        textwrap.dedent(
            """\
            ---
            name: episteme-setup
            description: setup
            ---

            # Setup
            """
        ),
        encoding="utf-8",
    )

    (skills_root / "registry.yaml").write_text(
        textwrap.dedent(
            """\
            version: 1
            format: markdown-frontmatter
            skills:
              - id: episteme
                path: episteme/SKILL.md
                triggers:
                  - "Episteme: <query|write>"
              - id: episteme-setup
                path: episteme-setup/SKILL.md
                triggers:
                  - "Episteme: setup"
            """
        ),
        encoding="utf-8",
    )

    return skills_root


class InstallSkillPackTests(unittest.TestCase):
    def run_installer(self, skills_root: Path, env: dict[str, str], *extra_args: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            str(INSTALLER),
            "--skills-root",
            str(skills_root),
            *extra_args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)

    def test_auto_detect_prefers_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            skills_root = create_sample_pack(tmp_root)
            codex_home = tmp_root / "codex-home"
            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env["CODEX_HOME"] = str(codex_home)

            result = self.run_installer(skills_root, env)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("source: $CODEX_HOME/skills", result.stdout)
            self.assertTrue((codex_home / "skills" / "episteme" / "SKILL.md").is_file())

    def test_registry_copy_default_and_opt_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            skills_root = create_sample_pack(tmp_root)
            env = os.environ.copy()
            env["HOME"] = str(tmp_root / "home")
            env.pop("CODEX_HOME", None)

            codex_skills = Path(env["HOME"]) / ".codex" / "skills"
            codex_skills.mkdir(parents=True, exist_ok=True)

            result_default = self.run_installer(skills_root, env)
            self.assertEqual(result_default.returncode, 0, msg=result_default.stderr)
            self.assertTrue((codex_skills / "registry.yaml").is_file())

            explicit_dest = tmp_root / "explicit-dest"
            result_opt_out = self.run_installer(
                skills_root,
                env,
                "--dest",
                str(explicit_dest),
                "--no-copy-registry",
            )
            self.assertEqual(result_opt_out.returncode, 0, msg=result_opt_out.stderr)
            self.assertFalse((explicit_dest / "registry.yaml").exists())


if __name__ == "__main__":
    unittest.main()
