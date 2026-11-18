import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import runtime_registry as runtime


def write_fixture_wheel(directory, name, dependency=None):
    version = "1.0"
    dist = f"{name}-{version}.dist-info"
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    if dependency:
        metadata += f"Requires-Dist: {dependency}\n"
    files = {
        f"{name}/__init__.py": "",
        f"{dist}/METADATA": metadata,
        f"{dist}/WHEEL": "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record = f"{dist}/RECORD"
    files[record] = "".join(f"{path},,\n" for path in [*files, record])
    with ZipFile(directory / f"{name}-{version}-py3-none-any.whl", "w") as wheel:
        for path, contents in files.items():
            wheel.writestr(path, contents)


@unittest.skipUnless(os.name == "posix", "shared runtime uses the Unix venv layout")
class RuntimeSnapshotTests(unittest.TestCase):
    def test_replay_transitive_packages_and_keep_snapshot_after_failure(self):
        with tempfile.TemporaryDirectory(prefix="runtime snapshot ") as temp:
            root = Path(temp)
            wheels = root / "wheels"
            wheels.mkdir()
            write_fixture_wheel(wheels, "fixture_child")
            write_fixture_wheel(wheels, "fixture_parent", "fixture_child>=1")
            settings = {
                "PIP_NO_INDEX": "1", "PIP_FIND_LINKS": wheels.as_uri(),
                "PIP_NO_CACHE_DIR": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            }
            with patch.dict(os.environ, settings), patch.object(runtime, "command_exists", return_value=False):
                spec = {"packages": ["fixture_parent"]}
                with patch.dict(runtime.DOMAIN_SPECS, {"test-python": spec}):
                    info = runtime.install_python_runtime("test-python", root)
                    self.assertNotIn("error", info, info)
                    snapshot = Path(info["requirements_snapshot"])
                    original = snapshot.read_text(encoding="utf-8")
                    replay = runtime.ensure_venv(root / "second environment")
                    pip = [str(replay), "-m", "pip"]
                    subprocess.run([*pip, "install", "--no-deps", "-r", str(snapshot)], check=True, capture_output=True)
                    subprocess.run([*pip, "check"], check=True, capture_output=True)
                    observed = subprocess.check_output([*pip, "freeze", "--local", "--all"], text=True)
                    self.assertEqual(observed.splitlines(), original.splitlines()[1:])
                    self.assertIn("fixture-child==1.0", observed.lower().replace("_", "-"))

                    spec["packages"] = ["unavailable-fixture"]
                    failed = runtime.install_python_runtime("test-python", root)
                    self.assertIn("error", failed)
                    self.assertNotIn("requirements_snapshot", failed)
                    self.assertEqual(snapshot.read_text(encoding="utf-8"), original)
