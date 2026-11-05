"""Source discovery, CSS indexing, token extraction and colour utilities.

Standard library only. The scanner is intentionally conservative: it reports
what it can see in source and marks behavioural conclusions as inferred.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

CODE_EXTENSIONS = {
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".sass": "css",
    ".less": "css",
    ".js": "js",
    ".mjs": "js",
    ".cjs": "js",
    ".jsx": "jsx",
    ".ts": "ts",
    ".tsx": "tsx",
    ".vue": "vue",
    ".svelte": "svelte",
    ".astro": "astro",
}

MARKUP_KINDS = {"html", "jsx", "tsx", "vue", "svelte", "astro"}
CSS_KINDS = {"css", "vue", "svelte", "astro"}
SCRIPT_KINDS = {"js", "jsx", "ts", "tsx", "vue", "svelte", "astro"}

IGNORED_DIRS = {
    "node_modules",
    ".git",
    ".hg",
    ".svn",
    "dist",
    "build",
    "out",
    "output",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".astro",
    "coverage",
    "vendor",
    "bower_components",
    ".cache",
    ".parcel-cache",
    ".turbo",
    ".vercel",
    ".netlify",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".opencode",
    ".idea",
    ".vscode",
    ".DS_Store",
}

MAX_FILE_BYTES = 2_000_000


@dataclass
class SourceFile:
    path: Path
    rel: str
    text: str
    kind: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    def line_at(self, index: int) -> int:
        return self.text.count("\n", 0, max(0, index)) + 1

    def line_content(self, line_no: int) -> str:
        lines = self.lines
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()[:220]
        return ""

    def matches(self, pattern: str, flags: int = 0) -> list[re.Match[str]]:
        return list(re.finditer(pattern, self.text, flags))


@dataclass
class Project:
    root: Path
    name: str
    files: list[SourceFile] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    stack: list[str] = field(default_factory=list)
    total_bytes: int = 0

    @property
    def html_files(self) -> list[SourceFile]:
        return [f for f in self.files if f.kind in {"html", "vue", "svelte", "astro"}]

    @property
    def css_files(self) -> list[SourceFile]:
        return [f for f in self.files if f.kind in CSS_KINDS]

    @property
    def script_files(self) -> list[SourceFile]:
        return [f for f in self.files if f.kind in SCRIPT_KINDS]

    @property
    def markup_files(self) -> list[SourceFile]:
        return [f for f in self.files if f.kind in MARKUP_KINDS]

    @property
    def lines_scanned(self) -> int:
        return sum(len(f.lines) for f in self.files)

    def has(self, pattern: str, kinds: Iterable[str] | None = None, flags: int = 0) -> bool:
        selected = self.files if kinds is None else [f for f in self.files if f.kind in kinds]
        return any(re.search(pattern, f.text, flags) for f in selected)

    def first_match(self, pattern: str, kinds: Iterable[str] | None = None) -> tuple[SourceFile, re.Match[str]] | None:
        selected = self.files if kinds is None else [f for f in self.files if f.kind in kinds]
        for source in selected:
            match = re.search(pattern, source.text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return source, match
        return None


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def _detect_stack(root: Path, files: list[SourceFile]) -> list[str]:
    stack: list[str] = []
    exts = {f.kind for f in files}
    if "html" in exts:
        stack.append("html")
    if "css" in exts:
        stack.append("css")
    if exts & {"js", "jsx", "ts", "tsx"}:
        stack.append("javascript")
    if "vue" in exts:
        stack.append("vue")
    if "svelte" in exts:
        stack.append("svelte")
    package_path = root / "package.json"
    if package_path.exists():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            package = {}
        deps = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(package.get(key) or {})
        lookup = {
            "next": "next.js",
            "react": "react",
            "vue": "vue",
            "@angular/core": "angular",
            "svelte": "svelte",
            "astro": "astro",
            "tailwindcss": "tailwind",
            "@radix-ui/react-dialog": "radix",
            "@radix-ui/react-switch": "radix",
            "shadcn": "shadcn",
            "class-variance-authority": "shadcn",
            "vite": "vite",
        }
        for dep, label in lookup.items():
            if dep in deps and label not in stack:
                stack.append(label)
    return stack


def discover(root: Path, include_tests: bool = False) -> Project:
    root = root.resolve()
    name = root.name or "project"
    project = Project(root=root, name=name)
    for current, dirs, filenames in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith("."))
        if not include_tests:
            dirs[:] = [d for d in dirs if d not in {"tests", "test", "__tests__", "e2e", "spec"}]
        for filename in sorted(filenames):
            path = Path(current) / filename
            ext = path.suffix.lower()
            if ext not in CODE_EXTENSIONS:
                continue
            rel = path.relative_to(root).as_posix()
            if not include_tests and re.search(r"\.(test|spec)\.[^.]+$", filename):
                continue
            text = _read_text(path)
            if text is None:
                project.skipped.append({"path": rel, "reason": "binary, unreadable or larger than 2 MB"})
                continue
            if path.stat().st_size > 80_000 and text.count("\n") < 10:
                project.skipped.append({"path": rel, "reason": "minified file"})
                continue
            project.files.append(SourceFile(path=path, rel=rel, text=text, kind=CODE_EXTENSIONS[ext]))
            project.total_bytes += len(text.encode("utf-8", errors="ignore"))
    project.stack = _detect_stack(root, project.files)
    return project


# ---------------------------------------------------------------------------
# CSS indexing

_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def mask_css_comments(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return _COMMENT_RE.sub(replace, text)


@dataclass
class CSSRule:
    selector: str
    body: str
    file: str
    line: int
    base_offset: int = 0


def _iter_blocks(text: str, file: str) -> Iterator[tuple[str, str, int]]:
    masked = mask_css_comments(text)
    stack: list[dict[str, object]] = []
    boundary = 0
    i = 0
    length = len(masked)
    while i < length:
        char = masked[i]
        if char == "{":
            raw_selector = masked[boundary:i]
            selector = raw_selector.strip().splitlines()[-1].strip() if raw_selector.strip() else ""
            selector = re.sub(r"^@[^{]+$", "", selector).strip()
            stack.append({"selector": selector, "start": i + 1, "line": masked.count("\n", 0, i) + 1})
            boundary = i + 1
        elif char == "}":
            if stack:
                block = stack.pop()
                yield (
                    str(block["selector"]),
                    masked[int(block["start"]) : i],
                    int(block["line"]),
                )
            boundary = i + 1
        elif char == ";" and not stack:
            boundary = i + 1
        i += 1


def _extract_style_blocks(source: SourceFile) -> list[tuple[str, str, int]]:
    blocks = []
    if source.kind == "html":
        for match in re.finditer(r"<style\b[^>]*>(.*?)</style>", source.text, re.I | re.S):
            line = source.line_at(match.start(1))
            blocks.append((match.group(1), source.rel, line))
    if source.kind in {"vue", "svelte", "astro"}:
        for match in re.finditer(r"<style\b[^>]*>(.*?)</style>", source.text, re.I | re.S):
            blocks.append((match.group(1), source.rel, source.line_at(match.start(1))))
    return blocks


class CSSIndex:
    def __init__(self, project: Project):
        self.project = project
        self.rules: list[CSSRule] = []
        self.raw_parts: list[str] = []
        for source in project.files:
            if source.kind == "css":
                self.raw_parts.append(mask_css_comments(source.text))
                for selector, body, line in _iter_blocks(source.text, source.rel):
                    self.rules.append(CSSRule(selector=selector, body=body, file=source.rel, line=line))
            elif source.kind in {"html", "vue", "svelte", "astro"}:
                for css_text, file, base_line in _extract_style_blocks(source):
                    self.raw_parts.append(mask_css_comments(css_text))
                    for selector, body, line in _iter_blocks(css_text, file):
                        self.rules.append(
                            CSSRule(
                                selector=selector,
                                body=body,
                                file=file,
                                line=base_line + line - 1,
                            )
                        )

    @property
    def text(self) -> str:
        return "\n".join(f"{r.selector} {{{r.body}}}" for r in self.rules)

    @property
    def raw_text(self) -> str:
        return "\n".join(self.raw_parts)

    def matching(self, pattern: str, flags: int = re.I) -> list[CSSRule]:
        return [rule for rule in self.rules if re.search(pattern, rule.selector, flags)]

    def has(self, pattern: str, flags: int = re.I) -> bool:
        return bool(re.search(pattern, self.raw_text or self.text, flags))

    def has_property(self, pattern: str) -> bool:
        return any(re.search(pattern, rule.body, re.I) for rule in self.rules)

    def class_rules(self, class_name: str) -> list[CSSRule]:
        needle = re.compile(r"\." + re.escape(class_name) + r"(?![\w-])")
        return [rule for rule in self.rules if needle.search(rule.selector)]

    def state_for_class(self, class_name: str, state_pattern: str) -> CSSRule | None:
        needle = re.compile(r"\." + re.escape(class_name) + r"(?![\w-])")
        for rule in self.rules:
            if needle.search(rule.selector) and re.search(state_pattern, rule.selector, re.I):
                return rule
        return None


def css_index(project: Project) -> CSSIndex:
    return CSSIndex(project)


# ---------------------------------------------------------------------------
# Tokens

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
COLOR_FN_RE = re.compile(r"\b(rgba?|hsla?)\([^)]*\)", re.I)
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;{}]+)", re.I)
SPACING_RE = re.compile(
    r"(?:margin|padding|gap|row-gap|column-gap|inset)\s*(?:-\w+)?\s*:\s*([^;{}]+)", re.I
)
RADIUS_RE = re.compile(r"border(?:-[a-z]+)?-radius\s*:\s*([^;{}]+)", re.I)
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;{}]+)", re.I)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;{}]+)", re.I)
FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;{}]+)", re.I)
TRANSITION_RE = re.compile(r"transition(?:-property)?\s*:\s*([^;{}]+)", re.I)

CSS_VAR_DEF_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;{}]+);")


def _split_values(raw: str) -> list[str]:
    values = []
    for part in re.split(r"\s+|,", raw.strip()):
        part = part.strip()
        if part:
            values.append(part)
    return values


def _norm_color(value: str) -> str | None:
    value = value.strip().lower()
    if value.startswith("#"):
        return normalize_hex(value)
    match = re.match(r"rgba?\(([^)]+)\)", value)
    if match:
        parts = [p.strip() for p in match.group(1).replace("/", " ").split(",")]
        if len(parts) >= 3:
            try:
                channels = [int(float(p.rstrip("%"))) for p in parts[:3]]
                alpha = 1.0
                if len(parts) > 3:
                    alpha = float(parts[3].rstrip("%"))
                    if "%" in parts[3]:
                        alpha /= 100
                if alpha < 0.999:
                    return None
                if all(0 <= c <= 255 for c in channels):
                    return "#%02X%02X%02X" % tuple(channels)
            except ValueError:
                return None
    return None


def normalize_hex(value: str) -> str | None:
    value = value.strip().lstrip("#")
    if len(value) in (3, 4):
        value = "".join(ch * 2 for ch in value[:3])
    elif len(value) == 8:
        if value[-2:].lower() != "ff":
            return None
        value = value[:6]
    if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return None
    return "#" + value.upper()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for channel in rgb:
        c = channel / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(a: str, b: str) -> float:
    la = relative_luminance(hex_to_rgb(a))
    lb = relative_luminance(hex_to_rgb(b))
    lighter, darker = max(la, lb), min(la, lb)
    return round((lighter + 0.05) / (darker + 0.05), 2)


@dataclass
class DesignSystem:
    colors: list[dict[str, object]]
    fonts: list[dict[str, object]]
    font_sizes: list[dict[str, object]]
    spacing: list[dict[str, object]]
    radii: list[dict[str, object]]
    shadows: list[dict[str, object]]
    custom_properties: list[dict[str, str]]
    literals_vs_tokens: dict[str, int]
    notes: list[str]


def extract_design_system(project: Project, index: CSSIndex) -> DesignSystem:
    color_counts: dict[str, int] = {}
    fonts: dict[str, int] = {}
    font_sizes: dict[str, int] = {}
    spacing: dict[str, int] = {}
    radii: dict[str, int] = {}
    shadows: dict[str, int] = {}
    weights: dict[str, int] = {}
    custom_properties: dict[str, str] = {}

    relevant = [f for f in project.files if f.kind in CSS_KINDS or f.kind in SCRIPT_KINDS]
    for source in relevant:
        for match in HEX_RE.finditer(source.text):
            normalized = normalize_hex(match.group(0))
            if normalized:
                color_counts[normalized] = color_counts.get(normalized, 0) + 1
        for match in COLOR_FN_RE.finditer(source.text):
            normalized = _norm_color(match.group(0))
            if normalized:
                color_counts[normalized] = color_counts.get(normalized, 0) + 1
        for match in CSS_VAR_DEF_RE.finditer(source.text):
            custom_properties.setdefault(match.group(1), match.group(2).strip()[:80])

    for rule in index.rules:
        for match in FONT_FAMILY_RE.finditer(rule.body):
            families = [x.strip().strip("'\"") for x in match.group(1).split(",")]
            primary = families[0] if families else ""
            alias = re.fullmatch(r"var\((--[a-zA-Z0-9_-]+)\)", primary)
            if alias:
                resolved = custom_properties.get(alias.group(1), "")
                resolved_primary = resolved.split(",")[0].strip().strip("'\"")
                if resolved_primary and not resolved_primary.startswith("var("):
                    primary = resolved_primary
            if primary:
                fonts[primary] = fonts.get(primary, 0) + 1
        for match in FONT_SIZE_RE.finditer(rule.body):
            value = match.group(1).strip()
            if value and not value.startswith("var("):
                font_sizes[value] = font_sizes.get(value, 0) + 1
        for match in SPACING_RE.finditer(rule.body):
            for value in _split_values(match.group(1)):
                if re.fullmatch(r"-?\d*\.?\d+(px|rem|em)", value):
                    spacing[value] = spacing.get(value, 0) + 1
        for match in RADIUS_RE.finditer(rule.body):
            for value in _split_values(match.group(1)):
                if value != "0" and re.fullmatch(r"-?\d*\.?\d+(px|rem|em|%)|9999px", value):
                    radii[value] = radii.get(value, 0) + 1
        for match in SHADOW_RE.finditer(rule.body):
            value = match.group(1).strip()[:100]
            if value and value != "none":
                shadows[value] = shadows.get(value, 0) + 1
        for match in FONT_WEIGHT_RE.finditer(rule.body):
            value = match.group(1).strip()
            if value:
                weights[value] = weights.get(value, 0) + 1

    literal_uses = sum(color_counts.values())
    token_refs = 0
    for source in relevant:
        token_refs += len(re.findall(r"var\(--[a-zA-Z0-9_-]+\)", source.text))

    def rows(mapping: dict[str, int], limit: int = 40) -> list[dict[str, object]]:
        return [
            {"value": key, "count": count}
            for key, count in sorted(mapping.items(), key=lambda item: (-item[1], item[0]))[:limit]
        ]

    notes = []
    if len(weights) > 4:
        notes.append(f"{len(weights)} distinct font weights declared; confirm each is intentional.")
    if literal_uses > 20 and token_refs < literal_uses:
        notes.append("Colour literals outnumber CSS variable references; inspect token adoption.")
    if not custom_properties:
        notes.append("No CSS custom properties found; tokens may live in a framework theme.")

    return DesignSystem(
        colors=[
            {"value": value, "count": count, "role": "inferred"}
            for value, count in sorted(color_counts.items(), key=lambda item: (-item[1], item[0]))[:40]
        ],
        fonts=rows(fonts),
        font_sizes=rows(font_sizes),
        spacing=rows(spacing),
        radii=rows(radii),
        shadows=rows(shadows),
        custom_properties=[
            {"name": name, "value": value} for name, value in sorted(custom_properties.items())[:100]
        ],
        literals_vs_tokens={"colour_literals": literal_uses, "token_references": token_refs},
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Contrast audit (only same-block, literal foreground/background pairs)

_DECL_COLOR_RE = re.compile(r"(?<![\w-])color\s*:\s*([^;{}]+)", re.I)
_DECL_BG_RE = re.compile(r"background(?:-color)?\s*:\s*([^;{}]+)", re.I)
_DECL_SIZE_RE = re.compile(r"font-size\s*:\s*([^;{}]+)", re.I)
_DECL_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;{}]+)", re.I)


def _first_literal_color(raw: str) -> str | None:
    if "var(" in raw or "gradient" in raw.lower() or "url(" in raw.lower():
        return None
    match = HEX_RE.search(raw) or COLOR_FN_RE.search(raw)
    if not match:
        return None
    return _norm_color(match.group(0))


def contrast_pairs(index: CSSIndex) -> list[dict[str, object]]:
    pairs = []
    seen: set[tuple[str, str, str, str]] = set()
    for rule in index.rules:
        selectors = rule.selector
        if not selectors or selectors.startswith("@") or "::selection" in selectors or "::backdrop" in selectors:
            continue
        fg_raw = _DECL_COLOR_RE.search(rule.body)
        bg_raw = _DECL_BG_RE.search(rule.body)
        if not fg_raw or not bg_raw:
            continue
        fg = _first_literal_color(fg_raw.group(1))
        bg = _first_literal_color(bg_raw.group(1))
        if not fg or not bg:
            continue
        key = (rule.file, selectors, fg, bg)
        if key in seen:
            continue
        seen.add(key)
        size_raw = _DECL_SIZE_RE.search(rule.body)
        weight_raw = _DECL_WEIGHT_RE.search(rule.body)
        font_px = None
        if size_raw:
            px = re.search(r"(\d+(?:\.\d+)?)px", size_raw.group(1))
            if px:
                font_px = float(px.group(1))
        bold = bool(weight_raw and weight_raw.group(1).strip() in {"600", "700", "800", "900", "bold"})
        large = bool(font_px and (font_px >= 24 or (bold and font_px >= 18.66)))
        threshold = 3.0 if large else 4.5
        ratio = contrast_ratio(fg, bg)
        if ratio < threshold:
            pairs.append(
                {
                    "selector": selectors.strip()[:120],
                    "file": rule.file,
                    "line": rule.line,
                    "foreground": fg,
                    "background": bg,
                    "ratio": ratio,
                    "threshold": threshold,
                }
            )
    return pairs


# ---------------------------------------------------------------------------
# Utility helpers

TAG_ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(\"[^\"]*\"|'[^']*'|\{[^}]*\}|[^\s>]+)")


def parse_attributes(tag: str) -> dict[str, str]:
    attrs = {}
    for match in TAG_ATTR_RE.finditer(tag):
        value = match.group(2)
        if value[:1] in {"'", '"'}:
            value = value[1:-1]
        attrs[match.group(1).lower()] = value
    return attrs


def strip_tags(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\{[^{}]*\}", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, length: int = 140) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"
