#!/usr/bin/env python3
"""Prepare real audit + screenshot evidence for the FINISHLINE workspace.

Usage:
    python3 scripts/workspace_data.py --audit audit.json --screenshots screenshots/screenshots.json --out ui/workspace/data
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema_check import validate  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="finishline-workspace-data", description="Load audit evidence into the workspace.")
    parser.add_argument("--audit", required=True, help="Audit JSON produced by scripts/audit.py")
    parser.add_argument("--screenshots", help="screenshots.json produced by scripts/capture.py")
    parser.add_argument("--out", default=str(SCRIPT_DIR.parent / "ui" / "workspace" / "data"))
    parser.add_argument("--label", help="Human project label shown in the workspace")
    parser.add_argument("--sample", action="store_true", help="Mark this dataset as a sample audit in the UI")
    parser.add_argument("--schema", default=str(SCRIPT_DIR.parent / "schemas" / "audit.schema.json"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit_path = Path(args.audit)
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"finishline-workspace-data: cannot read audit: {exc}", file=sys.stderr)
        return 2
    errors = validate(audit, schema)
    if errors:
        print("finishline-workspace-data: audit is invalid:", file=sys.stderr)
        for error in errors[:10]:
            print(f"  {error}", file=sys.stderr)
        return 2

    out_dir = Path(args.out).resolve()
    data_dir = out_dir
    shots_dir = out_dir / "shots"
    data_dir.mkdir(parents=True, exist_ok=True)
    if shots_dir.exists():
        for old in shots_dir.glob("*.png"):
            old.unlink()
    (data_dir / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    capture: dict[str, object] = {
        "captured": False,
        "count": 0,
        "captured_at": None,
        "shots": [],
        "skipped": [],
        "limitations": ["No screenshot manifest was supplied. Visual claims are unsupported."],
    }
    if args.screenshots:
        manifest_path = Path(args.screenshots)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"finishline-workspace-data: cannot read screenshot manifest: {exc}", file=sys.stderr)
            return 2
        shots = []
        skipped = list(manifest.get("skipped") or [])
        for shot in manifest.get("shots") or []:
            source = (manifest_path.parent / str(shot.get("path", ""))).resolve()
            if not source.exists() or not source.is_file():
                skipped.append({"page": shot.get("page"), "viewport": shot.get("viewport"), "reason": "screenshot file missing"})
                continue
            shots_dir.mkdir(parents=True, exist_ok=True)
            target_name = f"{shot.get('id', source.stem)}.png"
            shutil.copyfile(source, shots_dir / target_name)
            copied = dict(shot)
            copied["path"] = f"shots/{target_name}"
            copied["captured"] = True
            shots.append(copied)
        capture = {
            "captured": bool(shots),
            "count": len(shots),
            "captured_at": manifest.get("captured_at"),
            "target": manifest.get("target"),
            "tool": manifest.get("tool"),
            "viewports": manifest.get("viewports", []),
            "shots": shots,
            "skipped": skipped,
            "limitations": manifest.get("limitations") or [],
        }
    (data_dir / "screenshots.json").write_text(json.dumps(capture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    meta = {
        "project_label": args.label or audit.get("project", {}).get("name", "Project"),
        "sample": bool(args.sample),
        "audit_source": audit_path.name,
        "audit_generated_at": audit.get("generated_at"),
    }
    (data_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"workspace data ready: {len(audit.get('findings', []))} finding(s), "
        f"{capture['count']} screenshot(s) → {data_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())