from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_skill_pack.py"
SKILLS_ROOT = REPO_ROOT / "skills"


class ValidateSkillPackTests(unittest.TestCase):
    def run_validator(self, skills_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            sys.executable,
            str(VALIDATOR),
            "--skills-root",
            str(skills_root),
            *extra_args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def test_strict_validation_passes_for_current_pack(self) -> None:
        result = self.run_validator(SKILLS_ROOT, "--strict")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Validated", result.stdout)

    def test_fails_on_delegate_trigger_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            temp_skills = tmp_root / "skills"
            shutil.copytree(SKILLS_ROOT, temp_skills)

            registry = temp_skills / "registry.yaml"
            content = registry.read_text(encoding="utf-8")
            content = content.replace('      - "/episteme repair"\n', "")
            registry.write_text(content, encoding="utf-8")

            result = self.run_validator(temp_skills)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("delegate verb 'repair'", result.stderr)

    def test_fails_on_unknown_delegate_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            temp_skills = tmp_root / "skills"
            shutil.copytree(SKILLS_ROOT, temp_skills)

            registry = temp_skills / "registry.yaml"
            content = registry.read_text(encoding="utf-8")
            content = content.replace("      check: episteme-health", "      check: episteme-missing")
            registry.write_text(content, encoding="utf-8")

            result = self.run_validator(temp_skills)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown target skill 'episteme-missing'", result.stderr)


if __name__ == "__main__":
    unittest.main()
