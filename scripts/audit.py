#!/usr/bin/env python3
"""FINISHLINE static UI/UX audit.

Usage:
    python3 scripts/audit.py <project-dir> [--json|--out FILE] [--include-tests]

Exit codes:
    0  audit completed (findings may exist)
    1  audit completed and --fail-on threshold was reached
    2  invalid arguments or scan failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.rules import SEVERITY_ORDER, audit  # noqa: E402

SEVERITY_LABEL = {0: "CRITICAL", 1: "HIGH", 2: "MEDIUM", 3: "LOW"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="finishline-audit",
        description="Static UI/UX completeness audit. No network, no dependencies.",
    )
    parser.add_argument("root", nargs="?", default=".", help="Project directory to scan (default: current)")
    parser.add_argument("--json", action="store_true", help="Print the full audit JSON to stdout")
    parser.add_argument("--out", metavar="FILE", help="Write the audit JSON to FILE")
    parser.add_argument("--include-tests", action="store_true", help="Include tests/spec directories in the scan")
    parser.add_argument(
        "--fail-on",
        choices=["critical", "high", "medium", "low", "never"],
        default="never",
        help="Exit 1 when a finding at or above this severity exists (default: never)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the human summary on stderr")
    return parser.parse_args(argv)


def human_summary(result: dict[str, object]) -> str:
    project = result["project"]
    summary = result["summary"]
    findings = summary["findings"]
    components = summary["components"]
    lines = [
        f"FINISHLINE  {project['name']}  [{summary['readiness']}]",
        f"  {summary['readiness_reason']}",
        f"  files {project['files_scanned']} · lines {project['lines_scanned']:,} · stack {', '.join(project['stack'])}",
        f"  findings {findings['total']}  critical {findings['critical']}  high {findings['high']}  medium {findings['medium']}  low {findings['low']}",
        f"  confidence  verified {summary['confidence']['verified']}  inferred {summary['confidence']['inferred']}",
        f"  components {components['total']}  state coverage {components['state_coverage']}%",
    ]
    top = result["findings"][:5]
    if top:
        lines.append("  next findings:")
        for finding in top:
            lines.append(
                f"    {finding['severity'].upper():8} {finding['title']}  ({finding['file']}:{finding['line']})"
            )
    if not findings["total"]:
        lines.append("  No findings. Static checks cannot certify accessibility or visual quality; run capture + manual review.")
    lines.append("  This run is static. Screenshots and interaction states were not inspected.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        print(f"finishline: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        result = audit(root, include_tests=args.include_tests)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"finishline: audit failed: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        out_path = Path(args.out)
        if out_path.parent and not out_path.parent.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    if args.json:
        print(payload)
    elif not args.quiet:
        print(human_summary(result), file=sys.stderr)

    if args.fail_on != "never":
        threshold = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[f["severity"]] <= threshold for f in result["findings"]):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())