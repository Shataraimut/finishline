#!/usr/bin/env python3
"""Render a FINISHLINE audit JSON as Markdown or a self-contained HTML report.

Usage:
    python3 scripts/report.py audit.json --format md --out report.md
    python3 scripts/report.py audit.json --format html --out report.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema_check import validate  # noqa: E402

SEVERITIES = ["critical", "high", "medium", "low"]
SEVERITY_TITLE = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
STATUS_GLYPH = {"complete": "✓", "partial": "◐", "missing": "✗", "n/a": "—"}


def state_order(name: str) -> tuple[int, str]:
    order = {
        "default": 0,
        "off": 1,
        "closed": 1,
        "on": 2,
        "open": 2,
        "hover": 3,
        "focus": 4,
        "active": 5,
        "selected": 5,
        "filled": 6,
        "invalid": 7,
        "disabled": 8,
        "readonly": 9,
        "loading": 10,
        "pending": 11,
        "validation": 12,
        "success": 13,
        "failure": 14,
        "empty/no results": 15,
        "escape": 16,
        "focus": 17,
        "close": 18,
        "transition": 19,
        "confirm": 20,
        "polite announcement": 21,
        "error": 22,
    }
    return order.get(name, 40), name


def load_audit(path: Path, schema_path: Path) -> dict:
    audit = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = validate(audit, schema)
    if errors:
        raise ValueError("Audit does not match schemas/audit.schema.json:\n  " + "\n  ".join(errors[:12]))
    return audit


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_report(audit: dict) -> str:
    project = audit["project"]
    summary = audit["summary"]
    findings = audit["findings"]
    components = audit["components"]
    lines = [
        f"# FINISHLINE quality report — {project['name']}",
        "",
        f"**Readiness:** `{summary['readiness']}` — {summary['readiness_reason']}  ",
        f"**Generated:** {audit['generated_at']}  ",
        f"**Mode:** {audit['verification']['mode']} ({'rendered' if audit['verification']['rendered'] else 'source-only'})  ",
        f"**Scope:** {project['files_scanned']} files · {project['lines_scanned']:,} lines · stack: {', '.join(project['stack'])}  ",
        f"**Confidence:** {summary['confidence']['verified']} verified · {summary['confidence']['inferred']} inferred",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for severity in SEVERITIES:
        lines.append(f"| {SEVERITY_TITLE[severity]} | {summary['findings'][severity]} |")
    components_summary = summary["components"]
    lines += [
        f"| **Total** | **{summary['findings']['total']}** |",
        "",
        f"Component state coverage: **{components_summary['state_coverage']}%** "
        f"({components_summary['complete']} complete, {components_summary['partial']} partial, "
        f"{components_summary['missing']} missing).",
        "",
        "> Static analysis is evidence, not certification. Inferred findings require human or rendered confirmation.",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No static findings. This does not prove visual, interaction or accessibility quality.")
    for severity in SEVERITIES:
        group = [f for f in findings if f["severity"] == severity]
        if not group:
            continue
        lines += [f"### {SEVERITY_TITLE[severity]} ({len(group)})", ""]
        for finding in group:
            lines += [
                f"#### `{finding['id']}` {finding['title']}",
                "",
                f"- **Location:** `{finding['file']}:{finding['line']}`",
                f"- **Category:** {finding['category']}",
                f"- **Check:** `{finding['check']}`",
                f"- **Confidence:** {finding['confidence']}",
                "",
                f"**Evidence**  ",
                f"> {md_escape(finding['evidence'])}",
                "",
                f"**Why it matters**  ",
                finding["why"],
                "",
                f"**Repair**  ",
                finding["repair"],
                "",
            ]
    lines += ["## Component matrix", ""]
    if not components:
        lines.append("No interactive components were detected.")
    else:
        state_names = sorted({state["name"] for component in components for state in component["states"]}, key=state_order)
        header = "| Component | Kind | " + " | ".join(state_names) + " | Coverage |"
        divider = "|---|---|" + "|".join("---" for _ in state_names) + "|---:|"
        lines += [header, divider]
        for component in components:
            states = {state["name"]: state["status"] for state in component["states"]}
            cells = [STATUS_GLYPH.get(states.get(name, "n/a"), "—") for name in state_names]
            lines.append(
                f"| {md_escape(component['name'])} | {component['kind']} | " + " | ".join(cells) + f" | {component['coverage']}% |"
            )
        lines += ["", "Legend: ✓ complete · ◐ partial · ✗ missing · — not applicable.", ""]

    design = audit["design_system"]
    lines += ["## Design system evidence", "", "### Typography", ""]
    if design["fonts"]:
        for font in design["fonts"]:
            lines.append(f"- `{font['value']}` — {font['count']} declaration(s)")
    else:
        lines.append("- No font families declared in scanned CSS.")
    if design["font_sizes"]:
        lines.append("")
        lines.append("Font sizes: " + ", ".join(f"`{row['value']}`" for row in design["font_sizes"]))
    lines += ["", "### Colour", ""]
    if design["colors"]:
        lines.append(", ".join(f"`{color['value']}` ×{color['count']}" for color in design["colors"][:18]))
    else:
        lines.append("No colour literals found.")
    lines += [
        "",
        f"Colour literals: {design['literals_vs_tokens']['colour_literals']} · token references: {design['literals_vs_tokens']['token_references']}",
        "",
        "### Tokens",
        "",
    ]
    if design["custom_properties"]:
        for token in design["custom_properties"][:24]:
            lines.append(f"- `{token['name']}: {token['value']}`")
        if len(design["custom_properties"]) > 24:
            lines.append(f"- … {len(design['custom_properties']) - 24} more")
    else:
        lines.append("No CSS custom properties found.")
    lines += ["", "## Verification", "", "Checks run:", ""]
    for check in audit["verification"]["checks_run"]:
        lines.append(f"- `{check}`")
    lines += ["", "Limitations:", ""]
    for limitation in audit["verification"]["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


HTML_STYLE = """
:root { --paper:#f2f2ee; --surface:#fbfbf7; --ink:#171a18; --muted:#5e645f; --rule:#d4d7ce; --accent:#a83a24; --ok:#2f6b4f; --warn:#8a5b13; --bad:#a12f25; --mono:ui-monospace,SFMono-Regular,Menlo,monospace; --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:15px/1.6 var(--sans); }
main { max-width:1080px; margin:0 auto; padding:56px 28px 96px; }
header { border-bottom:1px solid var(--ink); padding-bottom:28px; margin-bottom:32px; }
.eyebrow { font:500 11px/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--muted); }
h1 { font-size:clamp(30px,5vw,52px); line-height:1.05; letter-spacing:-.025em; margin:12px 0; font-weight:600; }
h2 { font-size:24px; margin:52px 0 16px; border-top:1px solid var(--rule); padding-top:20px; }
h3 { font-size:18px; margin:28px 0 10px; }
h4 { font-size:15px; margin:26px 0 8px; }
p { max-width:76ch; }
.meta { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin:24px 0; }
.meta div { border-left:2px solid var(--rule); padding-left:12px; }
.meta dt { font:500 10px/1.2 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }
.meta dd { margin:3px 0 0; }
.pill { display:inline-block; border:1px solid currentColor; border-radius:2px; padding:2px 7px; font:500 10px/1.3 var(--mono); text-transform:uppercase; letter-spacing:.08em; }
.critical { color:var(--bad); } .high { color:#8f4516; } .medium { color:var(--warn); } .low { color:var(--muted); } .ready { color:var(--ok); }
table { width:100%; border-collapse:collapse; font-size:13px; margin:12px 0 24px; }
th { text-align:left; font:500 10px/1.2 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid var(--ink); padding:8px 6px; vertical-align:bottom; }
td { border-bottom:1px solid var(--rule); padding:8px 6px; vertical-align:top; }
td.num, th.num { text-align:right; }
tr:hover td { background:#fff; }
.finding { background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--rule); padding:18px 20px; margin:14px 0; }
.finding.critical { border-left-color:var(--bad); } .finding.high { border-left-color:#8f4516; } .finding.medium { border-left-color:var(--warn); } .finding.low { border-left-color:var(--muted); }
.finding h4 { margin-top:0; }
code, pre { font-family:var(--mono); }
pre { background:#e8e9e3; padding:12px; overflow:auto; font-size:12px; }
blockquote { margin:8px 0 14px; padding:6px 0 6px 14px; border-left:2px solid var(--rule); color:var(--muted); }
.legend { color:var(--muted); font-size:12px; }
li { margin:4px 0; }
footer { margin-top:64px; padding-top:20px; border-top:1px solid var(--rule); color:var(--muted); font-size:12px; }
@media print { body { background:#fff; } main { max-width:none; padding:0; } .finding { break-inside:avoid; } }
"""


def html_report(audit: dict) -> str:
    project = audit["project"]
    summary = audit["summary"]
    findings = audit["findings"]
    components = audit["components"]
    design = audit["design_system"]
    esc = html.escape
    severity_pill = f'<span class="pill {esc(summary["readiness"])}">{esc(summary["readiness"])}</span>'
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>FINISHLINE report — {esc(project['name'])}</title>",
        f"<style>{HTML_STYLE}</style>",
        "</head><body><main>",
        '<header><p class="eyebrow">FINISHLINE / interface quality report</p>',
        f"<h1>{esc(project['name'])}</h1>",
        f"<p>{severity_pill} &nbsp; {esc(summary['readiness_reason'])}</p></header>",
        '<dl class="meta">',
        f"<div><dt>Generated</dt><dd>{esc(audit['generated_at'])}</dd></div>",
        f"<div><dt>Mode</dt><dd>{esc(audit['verification']['mode'])} · {'rendered' if audit['verification']['rendered'] else 'source only'}</dd></div>",
        f"<div><dt>Scope</dt><dd>{project['files_scanned']} files · {project['lines_scanned']:,} lines</dd></div>",
        f"<div><dt>Confidence</dt><dd>{summary['confidence']['verified']} verified · {summary['confidence']['inferred']} inferred</dd></div>",
        "</dl>",
        "<h2>Summary</h2>",
        '<table><thead><tr><th>Severity</th><th class="num">Count</th></tr></thead><tbody>',
    ]
    for severity in SEVERITIES:
        parts.append(f'<tr><td>{SEVERITY_TITLE[severity]}</td><td class="num">{summary["findings"][severity]}</td></tr>')
    components_summary = summary["components"]
    parts += [
        f'<tr><td><strong>Total</strong></td><td class="num"><strong>{summary["findings"]["total"]}</strong></td></tr>',
        "</tbody></table>",
        f"<p>Component state coverage: <strong>{components_summary['state_coverage']}%</strong> "
        f"({components_summary['complete']} complete, {components_summary['partial']} partial, {components_summary['missing']} missing).</p>",
        "<blockquote>Static analysis is evidence, not certification. Inferred findings require human or rendered confirmation.</blockquote>",
        "<h2>Findings</h2>",
    ]
    if not findings:
        parts.append("<p>No static findings. This does not prove visual, interaction or accessibility quality.</p>")
    for severity in SEVERITIES:
        group = [f for f in findings if f["severity"] == severity]
        if not group:
            continue
        parts.append(f"<h3>{SEVERITY_TITLE[severity]} <span class='legend'>({len(group)})</span></h3>")
        for finding in group:
            parts += [
                f'<article class="finding {esc(severity)}">',
                f"<h4><code>{esc(finding['id'])}</code> {esc(finding['title'])}</h4>",
                f"<p class='legend'>{esc(finding['file'])}:{finding['line']} · {esc(finding['category'])} · "
                f"{esc(finding['confidence'])}</p>",
                f"<p><strong>Evidence</strong></p><pre>{esc(finding['evidence'])}</pre>",
                f"<p><strong>Why it matters</strong><br>{esc(finding['why'])}</p>",
                f"<p><strong>Repair</strong><br>{esc(finding['repair'])}</p>",
                "</article>",
            ]
    parts += ["<h2>Component matrix</h2>"]
    if components:
        state_names = sorted({state["name"] for component in components for state in component["states"]}, key=state_order)
        parts.append("<table><thead><tr><th>Component</th><th>Kind</th>")
        for name in state_names:
            parts.append(f"<th>{esc(name)}</th>")
        parts.append('<th class="num">Coverage</th></tr></thead><tbody>')
        for component in components:
            states = {state["name"]: state["status"] for state in component["states"]}
            parts.append(f"<tr><td>{esc(component['name'])}</td><td>{esc(component['kind'])}</td>")
            for name in state_names:
                status = states.get(name, "n/a")
                parts.append(f'<td title="{esc(status)}">{STATUS_GLYPH.get(status, "—")}</td>')
            parts.append(f'<td class="num">{component["coverage"]}%</td></tr>')
        parts.append("</tbody></table>")
        parts.append('<p class="legend">✓ complete · ◐ partial · ✗ missing · — not applicable</p>')
    else:
        parts.append("<p>No interactive components detected.</p>")
    parts += ["<h2>Design system evidence</h2>", "<h3>Typography</h3><ul>"]
    if design["fonts"]:
        for font in design["fonts"]:
            parts.append(f"<li><code>{esc(font['value'])}</code> — {font['count']} declaration(s)</li>")
    else:
        parts.append("<li>No font families declared in scanned CSS.</li>")
    parts.append("</ul>")
    if design["font_sizes"]:
        parts.append("<p>Font sizes: " + ", ".join(f"<code>{esc(row['value'])}</code>" for row in design["font_sizes"]) + "</p>")
    parts.append("<h3>Colour</h3>")
    if design["colors"]:
        parts.append("<p>" + ", ".join(f"<code>{esc(color['value'])}</code> ×{color['count']}" for color in design["colors"][:18]) + "</p>")
    else:
        parts.append("<p>No colour literals found.</p>")
    parts.append(
        f"<p>Colour literals: {design['literals_vs_tokens']['colour_literals']} · "
        f"token references: {design['literals_vs_tokens']['token_references']}</p>"
    )
    parts.append("<h3>Tokens</h3><ul>")
    if design["custom_properties"]:
        for token in design["custom_properties"][:24]:
            parts.append(f"<li><code>{esc(token['name'])}: {esc(token['value'])}</code></li>")
    else:
        parts.append("<li>No CSS custom properties found.</li>")
    parts += ["</ul>", "<h2>Verification</h2><h3>Checks run</h3><ul>"]
    for check in audit["verification"]["checks_run"]:
        parts.append(f"<li><code>{esc(check)}</code></li>")
    parts += ["</ul><h3>Limitations</h3><ul>"]
    for limitation in audit["verification"]["limitations"]:
        parts.append(f"<li>{esc(limitation)}</li>")
    parts += [
        "</ul>",
        f"<footer>FINISHLINE {esc(audit['generator']['version'])} · generated from {esc(project['name'])}</footer>",
        "</main></body></html>",
    ]
    return "\n".join(parts)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="finishline-report", description="Render a FINISHLINE audit.")
    parser.add_argument("audit", help="Audit JSON file")
    parser.add_argument("--format", choices=["md", "html"], help="Output format (inferred from --out suffix)")
    parser.add_argument("--out", metavar="FILE", help="Write report to FILE (default: stdout)")
    parser.add_argument("--schema", default=str(SCRIPT_DIR.parent / "schemas" / "audit.schema.json"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit_path = Path(args.audit)
    try:
        audit = load_audit(audit_path, Path(args.schema))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"finishline-report: {exc}", file=sys.stderr)
        return 2
    fmt = args.format
    if not fmt:
        if args.out and args.out.lower().endswith(".html"):
            fmt = "html"
        else:
            fmt = "md"
    output = html_report(audit) if fmt == "html" else markdown_report(audit)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output + "\n", encoding="utf-8")
        print(f"wrote {path} ({fmt})", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())