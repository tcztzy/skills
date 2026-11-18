import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import resolve_paperbanana as resolver


class PortabilityTests(unittest.TestCase):
    def test_draft_from_manuscript_directory_without_online_libraries(self):
        with tempfile.TemporaryDirectory(prefix="figure project ") as tmp:
            project = Path(tmp)
            manuscript = project / "main.tex"
            source = r"\begin{figure}\caption{Offline figure}\end{figure}"
            manuscript.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-S", str(SCRIPTS / "manuscript_figure.py"),
                 "main.tex", "--figure", "1", "--draft-only"],
                cwd=project, capture_output=True, text=True, check=True,
            )
            summary = json.loads(result.stdout)
            plan = project / summary["run_dir"] / "shared" / "diagram_plan.json"
            self.assertIn("Offline figure", plan.read_text(encoding="utf-8"))
            self.assertEqual(manuscript.read_text(encoding="utf-8"), source)

    def test_changed_remote_archive_is_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / resolver.ARCHIVE_NAME
            archive.write_bytes(b"unexpected archive content")
            hub = Mock()
            hub.hf_hub_download.return_value = str(archive)
            target = Path(tmp) / "dataset"
            with patch.dict(sys.modules, {"huggingface_hub": hub}):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    resolver.download_archive_to_target(target)
            self.assertEqual(hub.hf_hub_download.call_args.kwargs["revision"], resolver.DATASET_REVISION)
            self.assertFalse(target.exists())
