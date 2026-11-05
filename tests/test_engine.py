"""Static engine regression and correctness tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.components import collect_evidence, discover_components  # noqa: E402
from lib.rules import CHECK_REGISTRY, audit  # noqa: E402
from lib.scanner import (  # noqa: E402
    contrast_ratio,
    css_index,
    discover,
    extract_design_system,
    normalize_hex,
    parse_attributes,
    strip_tags,
)
from lib.schema_check import validate  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "defective-ui"
SCHEMA = json.loads((ROOT / "schemas" / "audit.schema.json").read_text(encoding="utf-8"))


def build_project(root: Path, html: str, css: str = "", js: str = "") -> Path:
    (root / "index.html").write_text(html, encoding="utf-8")
    if css:
        (root / "styles.css").write_text(css, encoding="utf-8")
    if js:
        (root / "app.js").write_text(js, encoding="utf-8")
    return root


def base_html(body: str = "", head: str = "") -> str:
    return (
        "<!doctype html><html lang=\"en\"><head>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Test page</title>"
        f"{head}</head><body><main><h1>Test page</h1>{body}</main></body></html>"
    )


class ScannerTests(unittest.TestCase):
    def test_hex_normalization(self) -> None:
        self.assertEqual(normalize_hex("#fff"), "#FFFFFF")
        self.assertEqual(normalize_hex("#1D5A48"), "#1D5A48")
        self.assertEqual(normalize_hex("#1d5a48ff"), "#1D5A48")
        self.assertIsNone(normalize_hex("#1d5a4880"))
        self.assertIsNone(normalize_hex("not-a-colour"))

    def test_contrast_ratio(self) -> None:
        self.assertEqual(contrast_ratio("#000000", "#FFFFFF"), 21.0)
        self.assertEqual(contrast_ratio("#777777", "#FFFFFF"), 4.48)

    def test_parse_attributes_and_strip_tags(self) -> None:
        attrs = parse_attributes('<button class="btn primary" type="button" aria-label="Close">x</button>')
        self.assertEqual(attrs["class"], "btn primary")
        self.assertEqual(attrs["type"], "button")
        self.assertEqual(attrs["aria-label"], "Close")
        self.assertEqual(strip_tags("<p>Hello <strong>world</strong></p>"), "Hello world")

    def test_discover_skips_dependencies_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(root, base_html("<button>Save</button>"))
            (root / "node_modules").mkdir()
            (root / "node_modules" / "bad.html").write_text("<html>", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_ui.py").write_text("x = 1\n", encoding="utf-8")
            project = discover(root)
            rels = {f.rel for f in project.files}
            self.assertEqual(rels, {"index.html"})
            self.assertIn("html", project.stack)

    def test_font_family_alias_resolves_through_custom_property(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html(),
                ':root { --font-sans: "IBM Plex Sans", sans-serif; }\nbody { font-family: var(--font-sans); }\n',
            )
            project = discover(root)
            design = extract_design_system(project, css_index(project))
            families = {row["value"] for row in design.fonts}
            self.assertIn("IBM Plex Sans", families)
            self.assertNotIn("var(--font-sans)", families)

    def test_reduced_motion_is_detected_through_media_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html(),
                "@media (prefers-reduced-motion: reduce) { .card { transition: none; } }\n",
            )
            project = discover(root)
            evidence = collect_evidence(project, css_index(project))
            self.assertTrue(evidence.native_reduced_motion)

    def test_touch_action_is_detected_from_css_property(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(root, base_html(), "button { touch-action: manipulation; }\n")
            project = discover(root)
            evidence = collect_evidence(project, css_index(project))
            self.assertTrue(evidence.touch_action)


class RuleRegressionTests(unittest.TestCase):
    def test_input_action_class_does_not_trigger_mobile_input_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html('<form><label for="email">Email</label><input id="email" class="input" type="email"></form>'),
                ".input { font-size: 16px; }\n.input-action { font-size: 12px; }\n",
            )
            result = audit(root)
            checks = {f["check"] for f in result["findings"]}
            self.assertNotIn("a11y.mobile-input-size", checks)

    def test_mobile_input_rule_still_fires_for_real_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html('<form><label for="email">Email</label><input id="email" class="input" type="email"></form>'),
                ".input { font-size: 14px; }\n",
            )
            result = audit(root)
            self.assertIn("a11y.mobile-input-size", {f["check"] for f in result["findings"]})

    def test_wrapped_table_scroll_is_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html('<div class="table-scroll"><table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>A</td></tr></tbody></table></div>'),
                ".table-scroll { overflow-x: auto; }\n",
            )
            result = audit(root)
            self.assertNotIn("responsive.table-overflow", {f["check"] for f in result["findings"]})

    def test_unwrapped_table_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(root, base_html("<table><tr><td>A</td></tr></table>"), "body { margin: 0; }\n")
            result = audit(root)
            self.assertIn("responsive.table-overflow", {f["check"] for f in result["findings"]})

    def test_nested_switch_input_is_counted_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html(
                    '<label class="switch">'
                    '<input class="switch-input" type="checkbox" role="switch" aria-label="Usage alerts">'
                    '<span class="switch-track"></span><span>Usage alerts</span></label>'
                ),
                ".switch { display: flex; gap: 8px; }\n"
                ".switch-input { appearance: none; }\n"
                ".switch-input:focus-visible { outline: 2px solid #176685; }\n"
                ".switch-input:checked + .switch-track { background: #1d5a48; }\n",
            )
            result = audit(root)
            toggles = [c for c in result["components"] if c["kind"] == "toggle"]
            self.assertEqual(len(toggles), 1)
            states = {s["name"]: s["status"] for s in toggles[0]["states"]}
            self.assertEqual(states["on"], "complete")

    def test_rule_findings_point_to_the_actual_css_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(
                root,
                base_html("<p>Content</p>"),
                "/* line 1 */\nbody { margin: 0; }\n.wide { width: 1200px; }\n",
            )
            result = audit(root)
            finding = next(f for f in result["findings"] if f["check"] == "precision.fixed-width")
            self.assertEqual(finding["line"], 3)

    def test_contrast_finding_is_evidence_backed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(root, base_html("<p class=\"muted\">Muted</p>"), ".muted { color: #777777; background: #ffffff; }\n")
            result = audit(root)
            findings = [f for f in result["findings"] if f["check"] == "a11y.contrast"]
            self.assertTrue(findings)
            self.assertIn("4.48:1", findings[0]["title"])
            self.assertEqual(findings[0]["confidence"], "verified")

    def test_check_registry_matches_run_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_project(root, base_html())
            result = audit(root)
            self.assertEqual(result["verification"]["checks_run"], CHECK_REGISTRY)
            self.assertEqual(result["verification"]["check_count"], len(CHECK_REGISTRY))
            self.assertGreaterEqual(len(CHECK_REGISTRY), 59)


class FixtureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = audit(FIXTURE)

    def test_fixture_exposes_blocking_findings(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["readiness"], "blocked")
        self.assertEqual(summary["findings"]["total"], 32)
        self.assertEqual(summary["findings"]["critical"], 3)
        self.assertEqual(summary["findings"]["high"], 10)
        self.assertEqual(summary["findings"]["medium"], 7)
        self.assertEqual(summary["findings"]["low"], 12)
        self.assertEqual(summary["components"]["total"], 14)
        self.assertEqual(summary["components"]["state_coverage"], 46)

    def test_fixture_has_expected_core_findings(self) -> None:
        checks = {f["check"] for f in self.result["findings"]}
        for expected in (
            "a11y.input-labels",
            "form.failure-feedback",
            "form.auth-error",
            "interaction.network-error",
        ):
            self.assertIn(expected, checks)

    def test_audit_matches_schema(self) -> None:
        errors = validate(self.result, SCHEMA)
        self.assertEqual(errors, [])

    def test_finding_ids_are_stable_and_sorted(self) -> None:
        ids = [f["id"] for f in self.result["findings"]]
        self.assertEqual(ids, [f"FL-{index:04d}" for index in range(1, len(ids) + 1)])
        severities = [f["severity"] for f in self.result["findings"]]
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.assertEqual(severities, sorted(severities, key=lambda value: order[value]))

    def test_schema_rejects_tampered_audit(self) -> None:
        tampered = json.loads(json.dumps(self.result))
        tampered["summary"]["readiness"] = "perfect"
        self.assertTrue(validate(tampered, SCHEMA))

    def test_example_pages_have_no_blocking_findings(self) -> None:
        result = audit(ROOT / "examples")
        summary = result["summary"]
        self.assertEqual(summary["readiness"], "ready")
        self.assertEqual(summary["findings"]["critical"], 0)
        self.assertEqual(summary["findings"]["high"], 0)
        self.assertEqual(summary["findings"]["medium"], 0)
        self.assertEqual(validate(result, SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
