"""Verify measurement formulas and CLI behavior using independent small oracles.

Hand-computable graphs and a breadth-first reference check reflexive reachability,
cycle handling and directional fan counts. Temporary projects verify actual token
counts, static Python resolution, Rust owner normalization, file deduplication,
missing data, baseline deltas and read-only selection. No target code is executed.
"""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import measure


class GraphTests(unittest.TestCase):
    def test_hand_calculated_chain_cycle_isolates_and_empty(self):
        cases = [
            ({"a": {"b"}, "b": {"c"}, "c": set()}, 6, 2 / 3, 0, 0),
            ({"a": {"b"}, "b": {"a"}, "c": set()}, 5, 5 / 9, 2, 2),
            ({"a": set(), "b": set(), "c": set()}, 3, 1 / 3, 0, 0),
            ({"a": {"a"}}, 1, 1, 1, 1),
            ({}, 0, None, 0, 0),
        ]
        for graph, pairs, pc, cyclic, largest in cases:
            with self.subTest(graph=graph):
                result = measure.graph_metrics(graph)
                self.assertEqual(result["reachable_pairs"], pairs)
                self.assertEqual(result["pc"], pc)
                self.assertEqual(result["cyclic_nodes"], cyclic)
                self.assertEqual(result["largest_cycle_size"], largest)
                self.assertEqual(result["cyclic_ratio"], cyclic / len(graph) if graph else None)

    def test_reachability_and_scc_match_independent_bfs(self):
        rng = random.Random(482)
        for n in range(1, 18):
            names = [str(i) for i in range(n)]
            graph = {a: {b for b in names if rng.random() < 0.13} for a in names}
            closure = {}
            for start in names:
                seen = {start}
                pending = [start]
                while pending:
                    for target in graph[pending.pop()]:
                        if target not in seen:
                            seen.add(target)
                            pending.append(target)
                closure[start] = seen
            cyclic = {a for a in names if a in graph[a] or any(a != b and b in closure[a] and a in closure[b] for b in names)}
            result = measure.graph_metrics(graph)
            self.assertEqual(result["reachable_pairs"], sum(map(len, closure.values())))
            self.assertEqual(result["cyclic_nodes"], len(cyclic))
            for row in result["hotspots"]:
                name = row["node"]
                self.assertEqual(row["visible_fan_out"], len(closure[name]))
                self.assertEqual(row["visible_fan_in"], sum(name in targets for targets in closure.values()))

    def test_chain_exceeds_recursion_limit(self):
        graph = {str(i): {str(i + 1)} if i < 1199 else set() for i in range(1200)}
        result = measure.graph_metrics(graph)
        self.assertEqual(result["reachable_pairs"], 1200 * 1201 // 2)
        self.assertEqual(result["cyclic_nodes"], 0)

    def test_unknown_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            measure.graph_metrics({"a": {"missing"}})


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.report = self.base / "report.json"

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def run_report(self, *options):
        with redirect_stdout(StringIO()):
            self.assertEqual(measure.main([str(self.root), "--selection", "walk", "--json", str(self.report), *map(str, options)]), 0)
        return json.loads(self.report.read_text(encoding="utf-8"))

    def graph_input(self, **updates):
        graph = {
            "schema_version": 1, "scope": "fixture", "granularity": "module",
            "extractor": {"name": "fixture", "version": "1", "command": "fixture export"},
            "limitations": [], "unresolved": [], "nodes": [], "edges": [],
        }
        graph.update(updates)
        path = self.base / "graph.json"
        path.write_text(json.dumps(graph), encoding="utf-8")
        return path

    def test_exact_tokens_roles_crlf_and_source_text_not_execution(self):
        self.write("hello.py", "raise RuntimeError('must never execute')\r\n")
        self.write("README.md", "hello world")
        self.write("tests/test_a.py", "hello world")
        report = self.run_report()
        self.assertEqual(report["size"]["documentation"]["tokens"], 2)
        self.assertEqual(report["size"]["tests"]["tokens"], 2)
        row = report["files"]["hello.py"]
        self.assertEqual(row["bytes"], len(b"raise RuntimeError('must never execute')\r\n"))
        self.assertEqual(row["sha256"], hashlib.sha256(b"raise RuntimeError('must never execute')\r\n").hexdigest())
        self.assertEqual(report["unmeasured"]["fault_detection"], None)

    def test_unicode_and_special_looking_tokens_use_ordinary_encoding(self):
        import tiktoken

        text = "中文\r\n<|endoftext|>"
        self.write("README.md", text)
        report = self.run_report()
        tokens = tiktoken.get_encoding("cl100k_base").encode(text, disallowed_special=())
        self.assertEqual(report["size"]["documentation"]["tokens"], len(tokens))

    def test_python_absolute_relative_initialization_and_isolates(self):
        self.write("src/pkg/__init__.py", "")
        self.write("src/pkg/a.py", "from . import b\nfrom pkg.b import value\n")
        self.write("src/pkg/b.py", "value = 4\n")
        self.write("src/pkg/isolated.py", "pass\n")
        report = self.run_report("--python-root", "src", "--entry", "pkg.a")
        edges = {tuple(edge) for edge in report["graph"]["edges"]}
        self.assertEqual(edges, {("pkg.a", "pkg"), ("pkg.a", "pkg.b")})
        self.assertEqual(report["graph"]["metrics"]["nodes"], 4)
        self.assertEqual(report["graph"]["missing"], {})
        self.assertEqual(report["entry_closure"]["files"], ["src/pkg/__init__.py", "src/pkg/a.py", "src/pkg/b.py"])

    def test_rust_items_collapse_and_shared_file_entry_union_is_deduplicated(self):
        self.write("src/lib.rs", "// hello\n")
        nodes = [
            {"id": "crate", "kind": "module", "files": ["src/lib.rs"]},
            {"id": "crate::a", "kind": "module", "files": ["src/lib.rs"]},
            {"id": "crate::a::f", "kind": "item", "owner": "crate::a", "files": ["src/lib.rs"]},
            {"id": "crate::a::g", "kind": "item", "owner": "crate::a", "files": ["src/lib.rs"]},
        ]
        path = self.graph_input(nodes=nodes, edges=[["crate", "crate::a::f"], ["crate::a::f", "crate::a::g"], ["crate::a::f", "crate::a::f"]])
        report = self.run_report("--graph", path, "--entry", "crate", "--entry", "crate::a")
        self.assertEqual(report["graph"]["metrics"]["nodes"], 2)
        self.assertEqual(report["graph"]["metrics"]["edges"], 1)
        self.assertEqual(report["graph"]["metrics"]["cyclic_nodes"], 0)
        self.assertEqual(report["graph"]["metadata"]["collapsed_intra_module_edges"], 2)
        self.assertEqual(report["entry_closure"]["tokens"], report["files"]["src/lib.rs"]["tokens"])

    def test_typescript_file_graph_preserves_cycle_and_isolate(self):
        for name in ("a.ts", "b.ts", "isolate.ts"):
            self.write(name, "export const value = 1;")
        nodes = [{"id": name, "kind": "file", "files": [name]} for name in ("a.ts", "b.ts", "isolate.ts")]
        path = self.graph_input(granularity="file", nodes=nodes, edges=[["a.ts", "b.ts"], ["b.ts", "a.ts"]])
        report = self.run_report("--graph", path, "--entry", "a.ts")
        self.assertEqual(report["graph"]["metrics"]["pc"], 5 / 9)
        self.assertEqual(report["graph"]["metrics"]["cyclic_ratio"], 2 / 3)
        self.assertEqual(report["graph"]["missing"], {})
        self.assertEqual(report["entry_closure"]["files"], ["a.ts", "b.ts"])

    def test_missing_files_parse_failures_and_dynamic_imports_are_visible(self):
        (self.root / "bad.py").write_bytes(b"\xff")
        self.write("syntax.py", "this is broken (\n")
        self.write("dynamic.py", "import importlib\nimportlib.import_module(name)\n")
        report = self.run_report()
        self.assertIsNone(report["size"]["production"]["tokens"])
        missing = report["graph"]["missing"]
        self.assertEqual(missing["selected_source_files_unmapped"], ["bad.py"])
        self.assertEqual(len(missing["parse_failures"]), 1)
        self.assertEqual(len(missing["unresolved"]), 1)

    def test_missing_entry_mapping_produces_null_not_zero(self):
        self.write("a.ts", "export const a = 1;")
        path = self.graph_input(granularity="file", nodes=[{"id": "a.ts", "kind": "file", "files": []}])
        report = self.run_report("--graph", path, "--entry", "a.ts")
        self.assertIsNone(report["entry_closure"]["tokens"])
        self.assertEqual(report["entry_closure"]["unmapped_nodes"], ["a.ts"])

    def test_baseline_reports_actual_savings_and_rejects_changed_policy(self):
        self.write("a.py", "import b\n")
        self.write("b.py", "value = 1\n")
        self.write("README.md", "hello world")
        before = self.run_report("--entry", "a")
        baseline = self.base / "before.json"
        baseline.write_text(json.dumps(before), encoding="utf-8")
        self.write("README.md", "hello")
        self.write("a.py", "pass\n")
        after = self.run_report("--entry", "a", "--baseline", baseline)
        delta = after["comparison"]["delta_after_minus_before"]
        self.assertEqual(delta["tokens.documentation"], -1)
        self.assertEqual(delta["graph.reachable_pairs"], -1)
        self.assertEqual(delta["graph.pc"], -0.25)
        self.assertEqual(delta["entry_closure.tokens"], after["files"]["a.py"]["tokens"] - before["entry_closure"]["tokens"])
        incompatible = self.run_report("--entry", "a", "--exclude", "README.md", "--baseline", baseline)
        self.assertFalse(incompatible["comparison"]["compatible_policy"])
        self.assertTrue(all(value is None for value in incompatible["comparison"]["delta_after_minus_before"].values()))

    def test_invalid_graph_or_missing_extraction_fails_instead_of_token_only(self):
        self.write("a.rs", "fn main() {}")
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
            self.run_report()
        self.assertEqual(raised.exception.code, 2)
        path = self.graph_input(nodes=[{"id": "fn", "kind": "item", "files": ["a.rs"]}])
        with self.assertRaises(ValueError):
            measure.load_graph(path)

    def test_selection_and_output_preserve_project(self):
        self.write("a.py", "pass\n")
        self.write(".env", "SECRET=do-not-read")
        self.write("target/unused.py", "raise RuntimeError()")
        (self.root / "link.py").symlink_to(self.root / "a.py")
        report = self.run_report()
        self.assertEqual(set(report["files"]), {"a.py"})
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
            measure.main([str(self.root), "--selection", "walk", "--json", str(self.root / "a.py")])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual((self.root / "a.py").read_text(), "pass\n")

    def test_git_selection_retains_untracked_but_omits_ignored(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", "ignored.py\n")
        self.write("a.py", "pass\n")
        self.write("ignored.py", "pass\n")
        with redirect_stdout(StringIO()):
            measure.main([str(self.root), "--json", str(self.report)])
        report = json.loads(self.report.read_text())
        self.assertEqual(set(report["files"]), {"a.py"})


if __name__ == "__main__":
    unittest.main()
