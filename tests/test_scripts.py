"""CLI, report, workspace-data, capture and package-gate tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "defective-ui"
PYTHON = sys.executable

sys.path.insert(0, str(SCRIPTS))

from capture import parse_viewports, png_size  # noqa: E402


def run(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


class AuditCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "audit.json"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_audit_writes_json_and_summary(self) -> None:
        result = run("scripts/audit.py", str(FIXTURE), "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[blocked]", result.stderr)
        payload = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["findings"]["total"], 32)

    def test_audit_json_mode_is_machine_readable(self) -> None:
        result = run("scripts/audit.py", str(FIXTURE), "--json", "--quiet")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["verification"]["mode"], "static")

    def test_fail_on_threshold(self) -> None:
        result = run("scripts/audit.py", str(FIXTURE), "--fail-on", "high", "--quiet")
        self.assertEqual(result.returncode, 1)
        result = run("scripts/audit.py", str(ROOT / "examples"), "--fail-on", "high", "--quiet")
        self.assertEqual(result.returncode, 0)

    def test_invalid_directory_is_usage_error(self) -> None:
        result = run("scripts/audit.py", str(ROOT / "does-not-exist"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a directory", result.stderr)


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.audit_path = Path(cls.tmp.name) / "audit.json"
        result = run("scripts/audit.py", str(FIXTURE), "--out", str(cls.audit_path), "--quiet")
        assert result.returncode == 0, result.stderr

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_markdown_report_contains_findings_and_limitations(self) -> None:
        out = Path(self.tmp.name) / "report.md"
        result = run("scripts/report.py", str(self.audit_path), "--format", "md", "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        text = out.read_text(encoding="utf-8")
        self.assertIn("# FINISHLINE quality report", text)
        self.assertIn("## Findings", text)
        self.assertIn("Static analysis is evidence, not certification", text)
        self.assertIn("FL-0001", text)
        self.assertIn("## Component matrix", text)

    def test_html_report_is_standalone_and_escaped(self) -> None:
        out = Path(self.tmp.name) / "report.html"
        result = run("scripts/report.py", str(self.audit_path), "--format", "html", "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        text = out.read_text(encoding="utf-8")
        self.assertTrue(text.lower().startswith("<!doctype html>"))
        self.assertIn("FINISHLINE", text)
        self.assertIn("<style", text)
        self.assertNotIn("<script src=", text)
        self.assertIn("Component matrix", text)

    def test_invalid_audit_is_rejected(self) -> None:
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        result = run("scripts/report.py", str(bad), "--format", "md", "--out", str(Path(self.tmp.name) / "x.md"))
        self.assertNotEqual(result.returncode, 0)


class WorkspaceDataTests(unittest.TestCase):
    def test_loads_audit_and_real_screenshot_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_path = root / "audit.json"
            self.assertEqual(
                run("scripts/audit.py", str(FIXTURE), "--out", str(audit_path), "--quiet").returncode,
                0,
            )
            shots = root / "shots"
            shots.mkdir()
            source_png = ROOT / "ui" / "workspace" / "data" / "shots" / "index-desktop.png"
            target_png = shots / "index-desktop.png"
            target_png.write_bytes(source_png.read_bytes())
            manifest = {
                "captured_at": "2026-01-01T00:00:00+00:00",
                "tool": "test",
                "viewports": [{"name": "desktop", "width": 1440, "height": 1000}],
                "shots": [
                    {
                        "id": "index-desktop",
                        "page": "index.html",
                        "title": "Fixture",
                        "viewport": "desktop",
                        "width": 1440,
                        "height": 1000,
                        "path": "shots/index-desktop.png",
                    }
                ],
                "skipped": [],
                "limitations": ["Test fixture capture."],
            }
            manifest_path = root / "screenshots.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            out = root / "data"
            result = run(
                "scripts/workspace_data.py",
                "--audit",
                str(audit_path),
                "--screenshots",
                str(manifest_path),
                "--out",
                str(out),
                "--label",
                "Fixture",
                "--sample",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            loaded = json.loads((out / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["summary"]["findings"]["total"], 32)
            capture = json.loads((out / "screenshots.json").read_text(encoding="utf-8"))
            self.assertTrue(capture["captured"])
            self.assertEqual(capture["count"], 1)
            self.assertTrue((out / "shots" / "index-desktop.png").exists())
            meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
            self.assertTrue(meta["sample"])
            self.assertEqual(meta["project_label"], "Fixture")

    def test_rejects_audit_that_does_not_match_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid = root / "audit.json"
            invalid.write_text('{"summary": {}}', encoding="utf-8")
            result = run("scripts/workspace_data.py", "--audit", str(invalid), "--out", str(root / "data"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("audit is invalid", result.stderr)


class CaptureUtilityTests(unittest.TestCase):
    def test_viewport_parser(self) -> None:
        viewports = parse_viewports("desktop:1440x1000,mobile:390x844")
        self.assertEqual(viewports[0], {"name": "desktop", "width": 1440, "height": 1000})
        self.assertEqual(viewports[1]["width"], 390)

    def test_viewport_parser_rejects_invalid_values(self) -> None:
        for raw in ("desktop", "desktop:wide", "desktop:2000x200", ""):
            with self.assertRaises(ValueError):
                parse_viewports(raw)

    def test_png_size_reads_real_capture_header(self) -> None:
        path = ROOT / "ui" / "workspace" / "data" / "shots" / "index-mobile.png"
        size = png_size(path)
        self.assertIsNotNone(size)
        self.assertEqual(size[0], 390)
        self.assertGreater(size[1], 0)


class PackageGateTests(unittest.TestCase):
    def test_validate_passes_with_audit_and_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.json"
            run("scripts/audit.py", str(FIXTURE), "--out", str(audit_path), "--quiet")
            result = run("scripts/validate.py", "--audit", str(audit_path), "--strict", "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"], payload)
            self.assertEqual(payload["errors"], [])
            self.assertEqual(payload["warnings"], [])


if __name__ == "__main__":
    unittest.main()
