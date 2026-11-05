#!/usr/bin/env python3
"""Validate the FINISHLINE skill package and (optionally) an audit JSON file.

Usage:
    python3 scripts/validate.py [--root DIR] [--audit FILE] [--strict] [--json]
"""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import sys
from pathlib import Path
from urllib.parse import unquote

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema_check import validate  # noqa: E402

REQUIRED_REFERENCES = [
    "typography.md",
    "color-systems.md",
    "design-principles.md",
    "component-states.md",
    "interaction-feedback.md",
    "ux-writing.md",
    "accessibility.md",
    "responsive-design.md",
    "precision.md",
    "anti-slop.md",
    "visual-qa.md",
]
REQUIRED_TEMPLATES = ["design-audit.md", "state-matrix.md", "quality-report.md", "design-tokens.json"]
REQUIRED_SCRIPTS = ["audit.py", "validate.py", "report.py", "capture.py", "workspace_data.py"]
REQUIRED_EXAMPLES = ["login-page/index.html", "dashboard/index.html", "settings-page/index.html"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line.strip())
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def strip_fenced_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def check_skill(root: Path, report: Report) -> None:
    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        report.error("SKILL.md is missing")
        return
    text = skill_path.read_text(encoding="utf-8")
    front = parse_frontmatter(text)
    if not front:
        report.error("SKILL.md has no parseable YAML frontmatter")
        return
    name = front.get("name", "")
    description = front.get("description", "")
    if not NAME_RE.match(name):
        report.error(f"SKILL.md name {name!r} does not match ^[a-z0-9]+(-[a-z0-9]+)*$")
    if name != root.name:
        report.error(f"SKILL.md name {name!r} must match directory {root.name!r}")
    if not (1 <= len(description) <= 1024):
        report.error("SKILL.md description must be 1-1024 characters")
    if front.get("license") and "MIT" not in front["license"].upper():
        report.warn(f"SKILL.md license field is {front['license']!r}; repository LICENSE is MIT")
    report.note(f"skill: {name} — {len(description)} character description")

    for filename in REQUIRED_REFERENCES:
        path = root / "references" / filename
        if not path.exists():
            report.error(f"missing reference: references/{filename}")
        elif filename not in text:
            report.error(f"SKILL.md does not route to references/{filename}")
    for filename in REQUIRED_TEMPLATES:
        path = root / "templates" / filename
        if not path.exists():
            report.error(f"missing template: templates/{filename}")
        if filename.endswith(".json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except ValueError as exc:
                report.error(f"templates/{filename} is not valid JSON: {exc}")
    for filename in REQUIRED_SCRIPTS:
        path = root / "scripts" / filename
        if not path.exists():
            report.error(f"missing script: scripts/{filename}")
    for rel in REQUIRED_EXAMPLES:
        if not (root / "examples" / rel).exists():
            report.error(f"missing example: examples/{rel}")
    for rel in ["ui/workspace/index.html", "ui/workspace/styles.css", "ui/workspace/app.js", "ui/workspace/data/audit.json"]:
        if not (root / rel).exists():
            report.warn(f"workspace asset missing: {rel}")

    license_path = root / "LICENSE"
    if not license_path.exists():
        report.error("LICENSE is missing")
    elif "MIT License" not in license_path.read_text(encoding="utf-8", errors="ignore")[:200]:
        report.warn("LICENSE does not look like MIT")

    tests = root / "tests"
    if tests.exists():
        if not list(tests.glob("test_*.py")):
            report.warn("tests/ exists but contains no test_*.py files")
    else:
        report.warn("tests/ directory is missing")

    for script in (root / "scripts").rglob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            report.error(f"Python syntax error in {script.relative_to(root)}: {exc.msg}")
    report.note("python scripts compile")


def check_json_schema(root: Path, report: Report) -> None:
    schema_path = root / "schemas" / "audit.schema.json"
    if not schema_path.exists():
        report.error("schemas/audit.schema.json is missing")
        return
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        report.error(f"schema is not valid JSON: {exc}")
        return
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        report.warn("schema does not declare JSON Schema 2020-12")
    if "findings" not in schema.get("properties", {}):
        report.error("schema has no findings property")
    report.note("audit schema parses")


def check_markdown_links(root: Path, report: Report) -> None:
    broken = 0
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = strip_fenced_blocks(path.read_text(encoding="utf-8", errors="ignore"))
        for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = unquote(target.split("#", 1)[0])
            if not clean:
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                report.warn(f"broken link in {path.relative_to(root)}: {target}")
                broken += 1
    if broken == 0:
        report.note("no broken relative Markdown links")


def check_audit_file(path: Path, root: Path, report: Report) -> None:
    schema_path = root / "schemas" / "audit.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        instance = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        report.error(f"cannot validate audit file {path}: {exc}")
        return
    errors = validate(instance, schema)
    if errors:
        for message in errors[:20]:
            report.error(f"audit schema: {message}")
        if len(errors) > 20:
            report.error(f"audit schema: {len(errors) - 20} more error(s)")
    else:
        report.note(f"audit valid: {path}")
        findings = instance.get("summary", {}).get("findings", {}).get("total")
        components = instance.get("summary", {}).get("components", {}).get("total")
        report.note(f"audit contains {findings} finding(s), {components} component(s)")


def check_privacy(root: Path, report: Report) -> None:
    patterns = [
        "/" + "root" + "/",
        "/" + "storage" + "/" + "emulated" + "/" + "0" + "/",
        "ghp" + r"_[A-Za-z0-9]{20,}",
        "sk" + r"-[A-Za-z0-9]{20,}",
        "AKIA" + r"[0-9A-Z]{16}",
    ]
    hits = 0
    own_file = Path(__file__).resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.resolve() == own_file:
            continue
        if path.suffix.lower() in {".png", ".woff2", ".jpg", ".jpeg", ".gif", ".zip", ".woff", ".pyc"}:
            continue
        if path.stat().st_size > 1_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in patterns:
            if re.search(pattern, text):
                report.warn(f"possible private path or secret pattern in {path.relative_to(root)}")
                hits += 1
                break
    if hits == 0:
        report.note("privacy/secret pattern scan clean")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="finishline-validate", description="Validate the FINISHLINE package.")
    parser.add_argument("--root", default=str(SCRIPT_DIR.parent), help="Repository root (default: parent of scripts/)")
    parser.add_argument("--audit", metavar="FILE", help="Validate an audit JSON file against the schema")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable result")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"finishline-validate: not a directory: {root}", file=sys.stderr)
        return 2
    report = Report()
    check_skill(root, report)
    check_json_schema(root, report)
    check_markdown_links(root, report)
    check_privacy(root, report)
    if args.audit:
        check_audit_file(Path(args.audit), root, report)

    payload = {
        "ok": not report.errors and not (args.strict and report.warnings),
        "errors": report.errors,
        "warnings": report.warnings,
        "notes": report.info,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for note in report.info:
            print(f"  ok   {note}")
        for warning in report.warnings:
            print(f"  warn {warning}")
        for error in report.errors:
            print(f"  FAIL {error}")
        print(
            f"\n{'PASS' if payload['ok'] else 'FAIL'}  "
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s), {len(report.info)} check(s)"
        )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())