from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "runtime_registry.py"
SPEC = importlib.util.spec_from_file_location("runtime_registry", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeRegistryTests(unittest.TestCase):
    def test_runtime_root_honors_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CODEX_SKILL_RUNTIME_ROOT": tmp}, clear=False):
            self.assertEqual(MODULE.resolve_runtime_root(), Path(tmp).resolve())

    def test_runtime_domain_mapping(self) -> None:
        self.assertEqual(MODULE.runtime_domain_for_skill("doc"), "docs-python")
        self.assertEqual(MODULE.runtime_domain_for_skill("latex-to-word"), "core-tools")
        self.assertEqual(MODULE.runtime_domain_for_skill("jupyter-notebook"), "science-python")
        self.assertEqual(MODULE.runtime_domain_for_skill("paper-visualizer"), "science-python")
        self.assertEqual(MODULE.runtime_domain_for_skill("openai-docs"), "core-tools")
        self.assertEqual(MODULE.runtime_domain_for_skill("skill-manager"), "core-tools")

    def test_ambient_python_state_exposes_leak_flag(self) -> None:
        state = MODULE.ambient_python_state()
        self.assertIn("executable", state)
        self.assertIn("project_local_dependency_leak", state)

    def test_render_shell_init_exports_expected_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rendered = MODULE.render_shell_init(tmp)
            self.assertIn('CODEX_SKILL_RUNTIME_ROOT', rendered)
            self.assertIn('CODEX_DOCS_RUNTIME_PYTHON', rendered)
            self.assertIn('CODEX_SCIENCE_RUNTIME_PYTHON', rendered)
            self.assertIn('CODEX_ML_RUNTIME_PYTHON', rendered)
            self.assertIn(str(Path.home() / '.nix-profile' / 'bin'), rendered)
            self.assertIn(str(Path.home() / '.npm-global' / 'bin'), rendered)

    def test_write_shell_init_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = MODULE.write_shell_init(tmp)
            self.assertTrue(target.exists())
            content = target.read_text(encoding='utf-8')
            self.assertIn('CODEX_SKILL_RUNTIME_ROOT', content)

    def test_load_or_probe_registry_uses_existing_cache_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = MODULE.registry_path(root)
            payload = {"domains": {domain: {} for domain in MODULE.DOMAIN_SPECS}}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            before = target.read_text(encoding="utf-8")
            before_mtime = target.stat().st_mtime_ns
            loaded = MODULE.load_or_probe_registry(runtime_root=root, install_missing=False)

            self.assertEqual(loaded, payload)
            self.assertEqual(target.read_text(encoding="utf-8"), before)
            self.assertEqual(target.stat().st_mtime_ns, before_mtime)
            self.assertFalse(MODULE.shell_init_path(root).exists())

    def test_load_or_probe_registry_without_cache_stays_in_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = MODULE.registry_path(root)

            with patch.dict(os.environ, {"HOME": tmp, "USERPROFILE": tmp, "PATH": tmp}):
                loaded = MODULE.load_or_probe_registry(runtime_root=root, install_missing=False)

            self.assertIn("domains", loaded)
            self.assertEqual(loaded["runtime_root"], str(root.resolve()))
            self.assertFalse(target.exists())
            self.assertFalse(MODULE.shell_init_path(root).exists())

    def test_partial_refresh_preserves_other_domains_and_rejects_typos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runtime"
            with patch.dict(os.environ, {"HOME": tmp, "USERPROFILE": tmp, "PATH": tmp}):
                before = MODULE.build_registry(runtime_root=root, domains={"core-tools"}, install_missing=False)
                after = MODULE.build_registry(runtime_root=root, domains={"docs-python"}, install_missing=False)
                self.assertEqual(after["domains"]["core-tools"], before["domains"]["core-tools"])
                self.assertEqual(set(after["domains"]), {"core-tools", "docs-python"})
                script = MODULE_PATH.with_name("bootstrap-global-skill-runtime.py")
                typo = subprocess.run(
                    [sys.executable, str(script), "--no-install", "--domain", "typo", "--runtime-root", str(root)],
                    capture_output=True,
                )
                self.assertNotEqual(typo.returncode, 0)
                self.assertEqual(MODULE.load_registry(root), after)

    @unittest.skipUnless(os.name == "posix" and shutil.which("sh"), "POSIX shell integration")
    def test_helpers_work_with_custom_installation_and_spaced_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "someone's home"
            runtime = home / "my $runtimes"
            commands = home / ".nix-profile" / "bin"
            commands.mkdir(parents=True)
            with patch.dict(os.environ, {"HOME": str(home), "PATH": str(commands), "CODEX_SKILL_RUNTIME_ROOT": ""}):
                MODULE.build_registry(runtime_root=runtime, domains={"docs-python"}, install_missing=False)
                shell = subprocess.run(
                    ["/bin/sh", "-ec", '. "$1"; . "$1"; echo "$CODEX_SKILL_RUNTIME_ROOT"; echo "$PATH"',
                     "sh", str(MODULE.shell_init_path(runtime))],
                    check=True, capture_output=True, text=True,
                )
                self.assertEqual(shell.stdout.splitlines(), [str(runtime.resolve()), str(commands)])
                refresh = subprocess.run(
                    [str(MODULE.refresh_helper_path()), "--no-install", "--domain", "science-python"],
                    check=True, capture_output=True, text=True,
                )
                self.assertEqual(json.loads(refresh.stdout)["runtime_root"], str(runtime.resolve()))
                self.assertEqual(set(MODULE.load_registry(runtime)["domains"]), {"docs-python", "science-python"})


if __name__ == "__main__":
    unittest.main()
