#!/usr/bin/env python3
"""Capture real viewport screenshots with a local Chromium/Chrome binary.

Usage:
    python3 scripts/capture.py examples --out screenshots
    python3 scripts/capture.py ui/workspace --out docs/screenshots/workspace --viewports desktop:1440x1000,mobile:390x844
    python3 scripts/capture.py https://example.com --out screenshots --pages /

This is intentionally not a Playwright wrapper. It has no third-party
dependencies and records exactly what it captured (and what it failed to
capture) in screenshots.json. It does not click through interaction states.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
IGNORED = {".git", "node_modules", "dist", "build", ".next", "coverage", ".venv", "__pycache__"}
CHROME_CANDIDATES = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"]


@functools.lru_cache(maxsize=1)
def find_chrome(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() else None
    env = os.environ.get("CHROME_PATH") or os.environ.get("CHROMIUM_PATH")
    if env and Path(env).exists():
        return env
    return shutil.which(next((c for c in CHROME_CANDIDATES if shutil.which(c)), "")) if any(
        shutil.which(c) for c in CHROME_CANDIDATES
    ) else None


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        width, height = struct.unpack(">II", header[16:24])
        return width, height
    except OSError:
        return None


def parse_viewports(raw: str) -> list[dict[str, object]]:
    viewports = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise ValueError(f"viewport must be name:WIDTHxHEIGHT, got {token!r}")
        name, size = token.split(":", 1)
        match = re.fullmatch(r"(\d{2,5})x(\d{2,5})", size.lower())
        if not match:
            raise ValueError(f"viewport size must be WIDTHxHEIGHT, got {size!r}")
        width, height = int(match.group(1)), int(match.group(2))
        if not (240 <= width <= 3840 and 320 <= height <= 4320):
            raise ValueError(f"viewport {name} out of supported range: {width}x{height}")
        viewports.append({"name": name, "width": width, "height": height})
    if not viewports:
        raise ValueError("no viewports supplied")
    return viewports


def discover_pages(root: Path, out_dir: Path, pages_arg: str | None) -> list[str]:
    if pages_arg:
        pages = [token.strip() for token in pages_arg.split(",") if token.strip()]
    else:
        pages = []
        for path in sorted(root.rglob("*.html")):
            if any(part in IGNORED or part.startswith(".") for part in path.parts):
                continue
            if out_dir in path.parents:
                continue
            pages.append(path.relative_to(root).as_posix())
    if not pages:
        raise ValueError(f"no HTML pages found under {root}")
    return pages[:30]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class ServerThread:
    def __init__(self, root: Path):
        handler = functools.partial(QuietHandler, directory=str(root))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.port = self.httpd.server_address[1]

    def __enter__(self) -> "ServerThread":
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


def slugify(value: str) -> str:
    value = re.sub(r"\.html?$", "", value, flags=re.I)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "page"


def page_title(html_text: str) -> str:
    match = re.search(r"<title\b[^>]*>(.*?)</title>", html_text, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()[:120]


def capture_one(
    chrome: str,
    url: str,
    out_path: Path,
    viewport: dict[str, object],
    timeout: int,
) -> tuple[bool, str, int]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    profile = tempfile.mkdtemp(prefix="finishline-chrome-")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--force-device-scale-factor=1",
        f"--window-size={viewport['width']},{viewport['height']}",
        "--virtual-time-budget=3000",
        "--run-all-compositor-stages-before-draw",
        f"--user-data-dir={profile}",
        f"--screenshot={out_path.resolve()}",
        url,
    ]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 200:
            reason = (result.stderr or result.stdout or "no screenshot produced").strip().splitlines()
            return False, " / ".join(reason[-3:])[:400], 0
        return True, "", out_path.stat().st_size
    except subprocess.TimeoutExpired:
        return False, f"chromium timed out after {timeout}s", 0
    except OSError as exc:
        return False, str(exc), 0
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="finishline-capture", description="Capture real viewport screenshots.")
    parser.add_argument("target", help="Local directory to serve, or an http(s) URL")
    parser.add_argument("--out", default="screenshots", help="Output directory (default: screenshots)")
    parser.add_argument(
        "--viewports",
        default="desktop:1440x1000,mobile:390x844",
        help="Comma-separated name:WIDTHxHEIGHT (default: desktop:1440x1000,mobile:390x844)",
    )
    parser.add_argument("--pages", help="Comma-separated page paths. Default: all HTML files in a directory")
    parser.add_argument("--chrome", help="Explicit Chromium/Chrome executable")
    parser.add_argument("--timeout", type=int, default=60, help="Per-screenshot timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print the manifest to stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        viewports = parse_viewports(args.viewports)
    except ValueError as exc:
        print(f"finishline-capture: {exc}", file=sys.stderr)
        return 2
    chrome = find_chrome(args.chrome)
    if not chrome:
        print(
            "finishline-capture: no Chromium/Chrome found. Install one or set CHROME_PATH. "
            "No screenshots were captured; do not claim visual inspection.",
            file=sys.stderr,
        )
        return 3

    target = args.target
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "schema_version": "1.0",
        "generator": {"name": "finishline-capture", "version": "1.0.0"},
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "target": target,
        "tool": {"name": "chromium-headless", "binary": chrome},
        "viewports": viewports,
        "shots": [],
        "skipped": [],
        "limitations": [
            "Viewport screenshots only; scrolling states, hover/focus states and interaction flows are not captured.",
            "The page is rendered with a 3 second virtual-time budget; delayed async content may be missing.",
            "Screenshots prove pixels existed, not WCAG compliance or usability.",
        ],
    }

    def run_for(url_base: str, pages: list[str], page_reader) -> None:
        for page in pages:
            rel = page.lstrip("/")
            url = url_base.rstrip("/") + "/" + quote(rel) if rel else url_base
            title = page_reader(rel)
            for viewport in viewports:
                shot_id = f"{slugify(rel or 'index')}-{viewport['name']}"
                out_path = out_dir / f"{shot_id}.png"
                ok, reason, size = capture_one(chrome, url, out_path, viewport, args.timeout)
                if not ok:
                    manifest["skipped"].append(
                        {"page": rel or "/", "viewport": viewport["name"], "reason": reason}
                    )
                    continue
                dimensions = png_size(out_path) or (0, 0)
                manifest["shots"].append(
                    {
                        "id": shot_id,
                        "page": rel or "/",
                        "title": title,
                        "url": url,
                        "viewport": viewport["name"],
                        "width": dimensions[0],
                        "height": dimensions[1],
                        "path": out_path.name,
                        "bytes": size,
                        "captured": True,
                    }
                )

    if target.startswith(("http://", "https://")):
        parsed = urlparse(target)
        pages_arg = args.pages if args.pages is not None else (parsed.path or "/")
        pages = [token.strip() for token in pages_arg.split(",") if token.strip()]
        if not pages:
            pages = ["/"]
        base = f"{parsed.scheme}://{parsed.netloc}"
        run_for(base, pages, lambda rel: "")
        manifest["base_url"] = base
    else:
        root = Path(target).resolve()
        if not root.is_dir():
            print(f"finishline-capture: not a directory: {root}", file=sys.stderr)
            return 2
        try:
            pages = discover_pages(root, out_dir, args.pages)
        except ValueError as exc:
            print(f"finishline-capture: {exc}", file=sys.stderr)
            return 2
        with ServerThread(root) as server:
            def reader(rel: str) -> str:
                try:
                    return page_title((root / rel).read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    return ""

            run_for(server.base_url, pages, reader)
            manifest["base_url"] = server.base_url
        manifest["target"] = root.name

    manifest_path = out_dir / "screenshots.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    captured = len(manifest["shots"])
    skipped = len(manifest["skipped"])
    if args.json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(f"captured {captured} screenshot(s), skipped {skipped}; manifest: {manifest_path}", file=sys.stderr)
        for item in manifest["skipped"][:5]:
            print(f"  skipped {item['page']} [{item['viewport']}]: {item['reason']}", file=sys.stderr)
    if captured == 0:
        print("finishline-capture: nothing was captured; visual claims are unsupported.", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())