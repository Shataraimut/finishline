"""FINISHLINE static audit rules and result assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .components import ComponentInventory, Evidence, collect_evidence, discover_components
from .scanner import (
    CSSIndex,
    Project,
    SourceFile,
    contrast_pairs,
    css_index,
    discover,
    extract_design_system,
    parse_attributes,
    strip_tags,
    truncate,
)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

CHECK_REGISTRY = [
    "a11y.viewport",
    "a11y.lang-title",
    "a11y.image-alt",
    "a11y.input-labels",
    "a11y.icon-button-label",
    "a11y.div-click",
    "a11y.focus-visible",
    "a11y.reduced-motion",
    "a11y.skip-link",
    "a11y.landmark",
    "a11y.zoom-disabled",
    "a11y.mobile-input-size",
    "a11y.contrast",
    "a11y.hover-only",
    "a11y.aria-live",
    "a11y.new-tab",
    "form.validation",
    "form.failure-feedback",
    "form.success-feedback",
    "form.pending-feedback",
    "form.secret-reveal",
    "form.unsaved-changes",
    "form.auth-error",
    "state.toggle-on",
    "state.button-loading",
    "state.input-invalid",
    "state.component-coverage",
    "state.empty",
    "state.dialog-close",
    "state.dialog-escape",
    "state.dialog-focus",
    "state.dropdown-empty",
    "state.disabled-style",
    "interaction.destructive-confirm",
    "interaction.network-error",
    "interaction.toast-live",
    "interaction.focus-first-error",
    "precision.fixed-width",
    "precision.spacing-grid",
    "precision.radius-system",
    "precision.z-index",
    "precision.important",
    "precision.icon-sizes",
    "precision.color-tokens",
    "typography.family-count",
    "typography.type-scale",
    "typography.weights",
    "typography.line-height",
    "typography.font-display",
    "responsive.media-queries",
    "responsive.table-overflow",
    "responsive.touch-action",
    "responsive.overflow-mask",
    "anti-slop.lorem",
    "anti-slop.hype-copy",
    "anti-slop.gradient",
    "anti-slop.glass",
    "anti-slop.radius",
    "motion.transition-all",
]


@dataclass
class Finding:
    check: str
    category: str
    title: str
    severity: str
    file: str
    line: int
    evidence: str
    why: str
    repair: str
    confidence: str = "verified"
    component: str | None = None
    status: str = "open"
    id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "check": self.check,
            "category": self.category,
            "title": self.title,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "evidence": truncate(self.evidence, 260),
            "why": self.why,
            "repair": self.repair,
            "confidence": self.confidence,
            "component": self.component,
            "status": self.status,
        }


@dataclass
class AuditRules:
    project: Project
    index: CSSIndex
    evidence: Evidence
    inventory: ComponentInventory
    findings: list[Finding] = field(default_factory=list)
    _dedupe: set[tuple[str, str, str]] = field(default_factory=set)

    @property
    def anchor(self) -> SourceFile | None:
        for source in self.project.files:
            if source.kind in {"css", "html", "vue", "svelte", "astro"}:
                return source
        return self.project.files[0] if self.project.files else None

    def _location(
        self, source: SourceFile | None, match: re.Match[str] | None, line: int | None = None
    ) -> tuple[str, int]:
        if source is None:
            return self.project.name, line or 1
        if line is not None:
            return source.rel, line
        if match is not None:
            return source.rel, source.line_at(match.start())
        return source.rel, 1

    def add(
        self,
        check: str,
        category: str,
        title: str,
        severity: str,
        why: str,
        repair: str,
        source: SourceFile | None = None,
        match: re.Match[str] | None = None,
        evidence: str = "",
        confidence: str = "verified",
        component: str | None = None,
        dedupe_key: str | None = None,
        line: int | None = None,
    ) -> None:
        source = source or self.anchor
        file_name, resolved_line = self._location(source, match, line)
        key = (check, file_name, dedupe_key or "file")
        if key in self._dedupe:
            return
        self._dedupe.add(key)
        if not evidence:
            evidence = truncate(match.group(0), 220) if match else "project-level evidence"
        self.findings.append(
            Finding(
                check=check,
                category=category,
                title=title,
                severity=severity,
                file=file_name,
                line=resolved_line,
                evidence=evidence,
                why=why,
                repair=repair,
                confidence=confidence,
                component=component,
            )
        )

    def run(self) -> None:
        self.markup_rules()
        self.form_rules()
        self.feedback_rules()
        self.css_rules()
        self.typography_rules()
        self.precision_rules()
        self.responsive_rules()
        self.anti_slop_rules()
        self.component_rules()

    # ------------------------------------------------------------------
    # Markup / accessibility

    def markup_rules(self) -> None:
        pages = self.project.html_files
        for source in pages:
            text = source.text
            head = text[:6000]
            viewport = re.search(
                r"<meta\b[^>]*name\s*=\s*[\"']viewport[\"'][^>]*content\s*=\s*[\"']([^\"']+)[\"']",
                head,
                re.I,
            )
            if not viewport:
                self.add(
                    "a11y.viewport",
                    "accessibility",
                    "Page has no viewport meta tag",
                    "high",
                    "Mobile browsers assume a desktop layout width, producing unusable zoomed-out pages.",
                    "Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`.",
                    source,
                    re.search(r"<head\b[^>]*>", head, re.I),
                    evidence="<head> without viewport meta",
                )
            elif re.search(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1(?:\.0+)?(?:[,\"']|$)", viewport.group(1), re.I):
                self.add(
                    "a11y.zoom-disabled",
                    "accessibility",
                    "Browser zoom is disabled",
                    "high",
                    "People with low vision must be able to zoom. Disabling pinch zoom breaks a core accessibility need.",
                    "Remove `user-scalable=no` and `maximum-scale=1` from the viewport tag.",
                    source,
                    viewport,
                )

            html_tag = re.search(r"<html\b[^>]*>", head, re.I)
            lang = re.search(r"\blang\s*=\s*[\"']([^\"']+)[\"']", html_tag.group(0), re.I) if html_tag else None
            title = re.search(r"<title\b[^>]*>(.*?)</title>", head, re.I | re.S)
            if not lang:
                self.add(
                    "a11y.lang-title",
                    "accessibility",
                    "Document language is missing",
                    "medium",
                    "Screen readers cannot select the correct pronunciation rules without a page language.",
                    "Add a valid `lang` attribute to `<html>`.",
                    source,
                    html_tag,
                    evidence=truncate(html_tag.group(0), 120) if html_tag else "<html> without lang",
                )
            if not title or not strip_tags(title.group(1)):
                self.add(
                    "a11y.lang-title",
                    "accessibility",
                    "Page has no descriptive title",
                    "medium",
                    "Titles identify pages in tabs, history and assistive technology page lists.",
                    "Add a unique, descriptive `<title>`.",
                    source,
                    re.search(r"<head\b[^>]*>", head, re.I),
                    dedupe_key="title",
                )

            imgs = []
            for match in re.finditer(r"<img\b[^>]*>", text, re.I):
                attrs = parse_attributes(match.group(0))
                if "alt" not in attrs:
                    imgs.append(match)
            if imgs:
                self.add(
                    "a11y.image-alt",
                    "accessibility",
                    "Images are missing alt text",
                    "high",
                    "Assistive technology cannot describe images without `alt`; decorative images still need `alt=\"\"`.",
                    "Add meaningful alt text, or `alt=\"\"` for purely decorative images.",
                    source,
                    imgs[0],
                    evidence=f"{len(imgs)} image(s) without alt; first: {truncate(imgs[0].group(0), 100)}",
                )

            label_ids = set(re.findall(r"<label\b[^>]*\bfor\s*=\s*[\"']([^\"']+)[\"']", text, re.I))
            missing_labels = []
            for match in re.finditer(r"<input\b[^>]*>", text, re.I):
                attrs = parse_attributes(match.group(0))
                input_type = attrs.get("type", "text").lower()
                if input_type in {"hidden", "submit", "button", "reset", "image"}:
                    continue
                has_label = (
                    attrs.get("id") in label_ids
                    or "aria-label" in attrs
                    or "aria-labelledby" in attrs
                    or "title" in attrs
                )
                if not has_label:
                    before = text[max(0, match.start() - 260) : match.start()]
                    if re.search(r"<label\b[^>]*>[^<]*$", before, re.I):
                        has_label = True
                if not has_label:
                    missing_labels.append(match)
            if missing_labels:
                self.add(
                    "a11y.input-labels",
                    "accessibility",
                    "Inputs have no accessible label",
                    "critical",
                    "A placeholder is not a label: it disappears when typing and is inconsistently announced.",
                    "Associate a `<label for>` or add `aria-label`/`aria-labelledby`.",
                    source,
                    missing_labels[0],
                    evidence=f"{len(missing_labels)} unlabelled input(s); first: {truncate(missing_labels[0].group(0), 120)}",
                )

            unlabelled_buttons = []
            for match in re.finditer(r"<button\b([^>]*)>(.*?)</button>", text, re.I | re.S):
                attrs = parse_attributes(match.group(1))
                inner = match.group(2)
                if strip_tags(inner) or attrs.get("aria-label") or attrs.get("title") or attrs.get("aria-labelledby"):
                    continue
                if re.search(r"<svg\b", inner, re.I) or re.search(r"<(?:img|span)\b[^>]*class=[\"'][^\"']*(?:icon|glyph)", inner, re.I):
                    unlabelled_buttons.append(match)
            if unlabelled_buttons:
                self.add(
                    "a11y.icon-button-label",
                    "accessibility",
                    "Icon-only button has no accessible name",
                    "high",
                    "A visible icon is not a name. Screen-reader users hear only “button”.",
                    "Add an `aria-label` that names the action, or visible text.",
                    source,
                    unlabelled_buttons[0],
                    evidence=f"{len(unlabelled_buttons)} icon button(s); first: {truncate(unlabelled_buttons[0].group(0), 120)}",
                )

            for match in re.finditer(r"<(div|span)\b[^>]*\bonclick\s*=[^>]*>", text, re.I):
                tag = match.group(0)
                if re.search(r"\brole\s*=", tag, re.I) and re.search(r"\btabindex\s*=", tag, re.I):
                    continue
                self.add(
                    "a11y.div-click",
                    "accessibility",
                    "Clickable div/span lacks button semantics",
                    "high",
                    "`<div onclick>` is not focusable and does not respond to Enter or Space.",
                    "Use `<button>` for actions, or add role, tabindex and keyboard handling.",
                    source,
                    match,
                )
                break

            if re.search(r"<nav\b", text, re.I) and not re.search(r"skip[ -]?(?:to|link)|skip-link", text, re.I):
                self.add(
                    "a11y.skip-link",
                    "accessibility",
                    "No skip-to-content link",
                    "low",
                    "Keyboard and switch users must traverse repeated navigation on every page.",
                    "Add a visible-on-focus link to `#main` at the start of the body.",
                    source,
                    re.search(r"<body\b[^>]*>", text, re.I),
                )
            if not re.search(r"<main\b|role\s*=\s*[\"']main[\"']", text, re.I):
                self.add(
                    "a11y.landmark",
                    "accessibility",
                    "Page has no main landmark",
                    "medium",
                    "Screen-reader users cannot jump directly to primary content.",
                    "Wrap primary content in `<main>` (one per page).",
                    source,
                    re.search(r"<body\b[^>]*>", text, re.I),
                )

            for match in re.finditer(r"<a\b[^>]*target\s*=\s*[\"']_blank[\"'][^>]*>", text, re.I):
                if not re.search(r"rel\s*=\s*[\"'][^\"']*noopener", match.group(0), re.I):
                    self.add(
                        "a11y.new-tab",
                        "accessibility",
                        "New-tab link lacks rel=noopener",
                        "low",
                        "The opened page can access `window.opener` in some browsers.",
                        "Add `rel=\"noopener noreferrer\"` (and announce the new tab when appropriate).",
                        source,
                        match,
                    )
                    break

            if re.search(r"<dialog\b|role\s*=\s*[\"']dialog[\"']", text, re.I):
                if not self.evidence.escape_handling and not re.search(r"<dialog\b", text, re.I):
                    self.add(
                        "state.dialog-escape",
                        "interaction",
                        "Dialog has no Escape handler",
                        "medium",
                        "Keyboard users expect Escape to dismiss a modal overlay.",
                        "Close on `Escape` and return focus to the trigger.",
                        source,
                        re.search(r"<dialog\b|role\s*=\s*[\"']dialog[\"']", text, re.I),
                        confidence="inferred",
                    )
                if not self.evidence.focus_management:
                    self.add(
                        "state.dialog-focus",
                        "accessibility",
                        "Dialog focus management is not evidenced",
                        "high",
                        "Without a focus trap and focus return, keyboard users can tab into the obscured page.",
                        "Use a native `<dialog>` with `showModal()`, or implement focus trap, initial focus and return.",
                        source,
                        re.search(r"<dialog\b|role\s*=\s*[\"']dialog[\"']", text, re.I),
                        confidence="inferred",
                    )

    # ------------------------------------------------------------------
    # Forms and feedback

    def form_rules(self) -> None:
        sources = self.project.html_files
        credential_forms = 0
        forms_with_fields = 0
        has_password = False
        for source in sources:
            text = source.text
            for match in re.finditer(r"<form\b([^>]*)>(.*?)</form>", text, re.I | re.S):
                attrs = parse_attributes(match.group(1))
                inner = match.group(2)
                if not re.search(r"<(?:input|textarea|select)\b", inner, re.I):
                    continue
                forms_with_fields += 1
                if re.search(r"<input\b[^>]*type\s*=\s*[\"']password[\"']", inner, re.I):
                    has_password = True
                    credential_forms += 1
                if not re.search(r"\brequired\b|aria-invalid|:invalid|\.error\b|validate\(", text, re.I):
                    self.add(
                        "form.validation",
                        "forms",
                        "Form has fields but no validation path",
                        "high",
                        "Users receive no guidance until a server rejects the request, often losing context.",
                        "Add constraints, inline field errors, and focus the first invalid field on submit.",
                        source,
                        match,
                        evidence=truncate(match.group(0), 160),
                        confidence="inferred",
                    )
                if re.search(r"<input\b[^>]*type\s*=\s*[\"']password[\"']", inner, re.I) and not self.evidence.reveal_secret:
                    self.add(
                        "form.secret-reveal",
                        "forms",
                        "Password field cannot be revealed",
                        "medium",
                        "Users cannot verify what they typed, increasing failed sign-ins.",
                        "Add a labelled show/hide control that preserves the value and focus.",
                        source,
                        match,
                        confidence="inferred",
                    )
                if self.evidence.async_flow and self.evidence.submit_handler:
                    if not self.evidence.success_feedback:
                        self.add(
                            "form.success-feedback",
                            "feedback",
                            "Async form has no success feedback",
                            "high",
                            "The request may succeed while the interface remains silent, so users repeat the action.",
                            "Show a persistent success state (inline, banner or toast) after the request resolves.",
                            source,
                            match,
                            confidence="inferred",
                        )
                    if not self.evidence.error_feedback:
                        self.add(
                            "form.failure-feedback",
                            "feedback",
                            "Async form has no failure feedback",
                            "critical",
                            "A failed network or server response leaves the user with no explanation or recovery path.",
                            "Render an error with a retry path; keep entered values; announce it.",
                            source,
                            match,
                            confidence="inferred",
                        )
                    if not self.evidence.loading:
                        self.add(
                            "form.pending-feedback",
                            "feedback",
                            "Async form has no pending state",
                            "high",
                            "Without a pending state users cannot tell whether the click registered and may double-submit.",
                            "Disable the trigger, keep its label, show a progress indicator, and prevent duplicate submits.",
                            source,
                            match,
                            confidence="inferred",
                        )
                if re.search(r"<textarea\b|<input\b[^>]*\btype\s*=\s*[\"'](?:text|email|url|number|tel)[\"']", inner, re.I):
                    field_count = len(re.findall(r"<(?:input|textarea)\b", inner, re.I))
                    if field_count >= 3 and not self.evidence.unsaved_warning:
                        self.add(
                            "form.unsaved-changes",
                            "interaction",
                            "Editable form has no unsaved-changes guard",
                            "low",
                            "Navigating away silently discards edits and undermines trust in the save action.",
                            "Track dirtiness and warn before navigation, or support autosave with a clear status.",
                            source,
                            match,
                            confidence="inferred",
                        )
            if re.search(r"type\s*=\s*[\"']password[\"']", text, re.I) and not re.search(
                r"aria-live|role\s*=\s*[\"']alert[\"']|error[-_ ]?message|form[-_ ]?error", text, re.I
            ):
                self.add(
                    "form.auth-error",
                    "forms",
                    "Password flow has no visible error surface",
                    "critical",
                    "Authentication failure must be explained in the interface, not only in the console or a redirect.",
                    "Add an inline error region with `role=\"alert\"`, preserve the email, and clear the password.",
                    source,
                    re.search(r"type\s*=\s*[\"']password[\"']", text, re.I),
                    confidence="inferred",
                )

        if credential_forms and not re.search(
            r"autocomplete\s*=\s*[\"'](?:username|current-password|email)[\"']", "\n".join(s.text for s in sources), re.I
        ):
            self.add(
                "form.auth-error",
                "forms",
                "Credential fields lack autocomplete hints",
                "low",
                "Password managers depend on `username` and `current-password` autocomplete values.",
                "Add `autocomplete=\"username\"` and `autocomplete=\"current-password\"`.",
                sources[0],
                re.search(r"<form\b", sources[0].text, re.I),
                dedupe_key="autocomplete",
                confidence="inferred",
            )

        anchors = [s for s in sources if re.search(r"<(?:button|a)\b[^>]*>\s*(?:Delete|Remove|Revoke|Discard|Reset|Deactivate)", s.text, re.I)]
        confirmation = re.search(
            r"confirm\s*\(|<dialog\b|role\s*=\s*[\"']alertdialog[\"']|undo|data-confirm", "\n".join(s.text for s in self.project.files), re.I
        )
        if anchors and not confirmation:
            source = anchors[0]
            match = re.search(r"<(?:button|a)\b[^>]*>\s*(?:Delete|Remove|Revoke|Discard|Reset|Deactivate)[^<]*", source.text, re.I)
            self.add(
                "interaction.destructive-confirm",
                "interaction",
                "Destructive action has no confirmation or undo",
                "high",
                "A single misclick can destroy data with no recovery path.",
                "Require explicit confirmation naming the object, or provide a time-bound Undo.",
                source,
                match,
                confidence="inferred",
            )

    def feedback_rules(self) -> None:
        text = "\n".join(f.text for f in self.project.files)
        if re.search(r"class\s*=\s*[\"'][^\"']*toast", text, re.I) and not self.evidence.toast_live:
            source = next((f for f in self.project.html_files if re.search(r"toast", f.text, re.I)), None)
            self.add(
                "interaction.toast-live",
                "feedback",
                "Toast notifications are not announced",
                "medium",
                "Visual-only toasts are invisible to screen-reader users.",
                "Add `role=\"status\"` (polite) or `role=\"alert\"` (assertive) and a persistent live region.",
                source,
                re.search(r"class\s*=\s*[\"'][^\"']*toast", source.text, re.I) if source else None,
            )
        if self.evidence.validation and not re.search(r"\.focus\s*\(|focusFirst|firstError", text, re.I):
            source = next((f for f in self.project.script_files if re.search(r"valid|error", f.text, re.I)), None)
            self.add(
                "interaction.focus-first-error",
                "forms",
                "Validation does not focus the first error",
                "medium",
                "Keyboard and screen-reader users may not discover which field needs attention.",
                "On submit failure, focus the first invalid field or an error summary that links to it.",
                source,
                re.search(r"valid|error", source.text, re.I) if source else None,
                confidence="inferred",
            )

        for source in self.project.script_files:
            if re.search(r"\bfetch\s*\(", source.text) and not re.search(r"\bcatch\s*\(|\btry\s*\{|\.catch\(", source.text):
                self.add(
                    "interaction.network-error",
                    "interaction",
                    "Fetch call has no rejection path",
                    "high",
                    "Network failure can leave a permanent loading state or an unhandled rejection.",
                    "Wrap requests in try/catch, show an actionable error, and restore the control state.",
                    source,
                    re.search(r"\bfetch\s*\(", source.text),
                    confidence="inferred",
                )
                break

    # ------------------------------------------------------------------
    # CSS / accessibility details

    def css_rules(self) -> None:
        index = self.index
        if re.search(r"outline\s*:\s*(?:none|0)\b", index.text, re.I) and not self.evidence.focus_replacement:
            rule = next((r for r in index.rules if re.search(r"outline\s*:\s*(?:none|0)\b", r.body, re.I)), None)
            self.add(
                "a11y.focus-visible",
                "accessibility",
                "Focus outline is removed without a replacement",
                "high",
                "Keyboard focus becomes invisible, making the interface unusable without a pointer.",
                "Replace the removed outline with a visible `:focus-visible` ring (≥3:1 against adjacent colours).",
                self._source_for(rule.file) if rule else None,
                evidence=_rule_text(rule) if rule else "",
                line=rule.line if rule else None,
            )
        if not self.evidence.focus_visible and re.search(r":focus\b", index.text, re.I) is None:
            self.add(
                "a11y.focus-visible",
                "accessibility",
                "No visible focus styling found",
                "high",
                "Pointer users see hover states; keyboard users need an equally clear location cue.",
                "Add `:focus-visible` styles with sufficient area and contrast, then verify with Tab.",
                self.anchor,
                evidence="no :focus or :focus-visible rule found",
                dedupe_key="no-focus",
                confidence="inferred",
            )
        if self.evidence.transition and not self.evidence.native_reduced_motion:
            self.add(
                "a11y.reduced-motion",
                "accessibility",
                "Motion does not respect reduced-motion preference",
                "medium",
                "Vestibular and attention-sensitive users can be harmed by unavoidable animation.",
                "Add a `prefers-reduced-motion: reduce` branch that removes non-essential movement and transitions.",
                self.anchor,
                evidence="transitions/animations present without prefers-reduced-motion",
                confidence="inferred",
            )

        for rule in index.rules:
            if re.search(r":hover", rule.selector, re.I) and re.search(r"display\s*:\s*(?:block|flex|grid)", rule.body, re.I):
                if not index.has(r":focus-within") and not index.has(r":focus-visible"):
                    self.add(
                        "a11y.hover-only",
                        "accessibility",
                        "Content is revealed on hover only",
                        "medium",
                        "Touch and keyboard users cannot trigger hover to reach the content.",
                        "Reveal with focus and/or an explicit toggle as well as hover.",
                        self._source_for(rule.file),
                        evidence=_rule_text(rule),
                        line=rule.line,
                        confidence="inferred",
                    )
                    break

        for rule in index.rules:
            if re.search(r"<(?:input|textarea)\b|(?:^|[\s,>+~])(?:input|textarea)(?![\w-])|(?:^|[\s,>+~])\.input(?![\w-])", rule.selector, re.I):
                size = re.search(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", rule.body, re.I)
                if size and float(size.group(1)) < 16:
                    self.add(
                        "a11y.mobile-input-size",
                        "accessibility",
                        "Input text is below 16px",
                        "low",
                        "iOS Safari may zoom the page when a small input receives focus, disrupting layout.",
                        "Use ≥16px input text on mobile (or set it inside a mobile media query).",
                        self._source_for(rule.file),
                        evidence=_rule_text(rule),
                        dedupe_key=rule.selector,
                        line=rule.line,
                        confidence="inferred",
                    )
                    break

        for pair in contrast_pairs(index):
            self.add(
                "a11y.contrast",
                "accessibility",
                f"Text contrast is {pair['ratio']}:1",
                "high",
                f"The declared foreground/background pair misses the {pair['threshold']}:1 threshold at this text size. "
                "Contrast computed from static CSS literals; verify against the rendered state.",
                f"Adjust the pair to at least {pair['threshold']}:1 (WCAG 2.2 AA), preserving hierarchy.",
                self._source_for(str(pair["file"])),
                match=None,
                evidence=f"{pair['selector']} → {pair['foreground']} on {pair['background']}",
                dedupe_key=str(pair["selector"]),
                confidence="verified",
                line=int(pair["line"]),
            )
            if len([f for f in self.findings if f.check == "a11y.contrast"]) >= 8:
                break

        if re.search(r"transition\s*:\s*all\b", index.text, re.I):
            rule = next((r for r in index.rules if re.search(r"transition\s*:\s*all\b", r.body, re.I)), None)
            self.add(
                "motion.transition-all",
                "motion",
                "transition: all is used",
                "low",
                "It animates unexpected properties, can cause layout jank, and hides intent.",
                "List the properties that should transition.",
                self._source_for(rule.file) if rule else None,
                evidence=_rule_text(rule) if rule else "",
                line=rule.line if rule else None,
            )

    def typography_rules(self) -> None:
        ds = self._design_system
        if len(ds.fonts) > 3:
            self.add(
                "typography.family-count",
                "typography",
                f"{len(ds.fonts)} font families are in use",
                "medium",
                "Too many families blur hierarchy and add loading cost.",
                "Choose one UI family plus at most one display or mono companion; remove the rest.",
                self.anchor,
                evidence=", ".join(f["value"] for f in ds.fonts[:6]),
                confidence="verified",
            )
        sizes = [row for row in ds.font_sizes if not str(row["value"]).startswith("var(")]
        if len(sizes) > 8:
            self.add(
                "typography.type-scale",
                "typography",
                f"{len(sizes)} distinct font sizes are declared",
                "low",
                "A scale with many near-neighbours reads as accidental rather than intentional.",
                "Consolidate to a documented type scale (typically 6–8 steps).",
                self.anchor,
                evidence=", ".join(str(s["value"]) for s in sizes[:10]),
                confidence="verified",
            )
        weights = set()
        for source in self.project.css_files:
            for match in re.finditer(r"font-weight\s*:\s*(\d{3}|bold|normal)", source.text, re.I):
                weights.add(match.group(1).lower())
        if len(weights) > 4:
            self.add(
                "typography.weights",
                "typography",
                f"{len(weights)} font weights are used",
                "low",
                "Excess weights flatten the distinction between emphasis levels.",
                "Keep 2–3 weights with clear roles.",
                self.anchor,
                evidence=", ".join(sorted(weights)),
            )

        for rule in self.index.rules:
            if re.search(r"(?:^|[\s,>+~])(?:body|\.prose|\.body|p)\b", rule.selector, re.I):
                size = re.search(r"font-size\s*:\s*(\d+(?:\.\d+)?)(px|rem)", rule.body, re.I)
                lh = re.search(r"line-height\s*:\s*([\d.]+)(px|rem)?", rule.body, re.I)
                if lh:
                    value = float(lh.group(1))
                    unit = lh.group(2)
                    if unit in (None, ""):
                        too_tight = value < 1.4
                    elif unit == "px" and size and size.group(2) == "px":
                        too_tight = value < float(size.group(1)) * 1.4
                    else:
                        too_tight = value < 18
                    if too_tight:
                        self.add(
                            "typography.line-height",
                            "typography",
                            "Body line-height is too tight",
                            "medium",
                            "Dense leading slows reading and hurts low-vision scanning.",
                            "Use roughly 1.45–1.65 for body text; adjust by typeface.",
                            self._source_for(rule.file),
                            evidence=_rule_text(rule),
                            dedupe_key=rule.selector,
                            line=rule.line,
                        )
                        break

        if "@font-face" in self.index.raw_text and not re.search(r"font-display\s*:", self.index.raw_text, re.I):
            self.add(
                "typography.font-display",
                "typography",
                "Web fonts have no font-display strategy",
                "low",
                "Invisible text or layout shift can occur while fonts load.",
                "Use `font-display: swap` (or optional/fallback) with a metrically similar fallback.",
                self.anchor,
                evidence="@font-face without font-display",
                confidence="inferred",
            )

    def precision_rules(self) -> None:
        ds = self._design_system
        radii = [row for row in ds.radii if row["value"] not in {"50%", "9999px"}]
        if len(radii) > 5:
            self.add(
                "precision.radius-system",
                "precision",
                f"{len(radii)} radius values are in use",
                "low",
                "Unsystematic corners weaken component family resemblance.",
                "Define a small radius scale and map components to roles (control, surface, pill).",
                self.anchor,
                evidence=", ".join(str(r["value"]) for r in radii[:8]),
            )
        off_grid = []
        for row in ds.spacing:
            value = str(row["value"])
            match = re.fullmatch(r"(-?\d+(?:\.\d+)?)px", value)
            if not match:
                continue
            px = float(match.group(1))
            if px in {0, 1, 2} or abs(px) > 160:
                continue
            if px % 4 != 0:
                off_grid.append(value)
        if len(off_grid) > 3:
            self.add(
                "precision.spacing-grid",
                "precision",
                f"{len(off_grid)} spacing values sit off the 4px grid",
                "low",
                "Optical alignment is fine, but accidental 3/5/7px values usually indicate drift.",
                "Confirm each off-grid value is deliberate; otherwise snap to the spacing scale.",
                self.anchor,
                evidence=", ".join(sorted(set(off_grid))[:10]),
            )
        z_values = sorted({int(m.group(1)) for f in self.project.css_files for m in re.finditer(r"z-index\s*:\s*(-?\d+)", f.text)})
        if len(z_values) > 6 or any(abs(z) > 999 for z in z_values):
            self.add(
                "precision.z-index",
                "precision",
                "z-index values lack a system",
                "low",
                "Ad-hoc stacking contexts cause overlays to appear beneath the wrong layer.",
                "Define a small z-index scale by layer role (base, sticky, dropdown, modal, toast).",
                self.anchor,
                evidence=", ".join(str(z) for z in z_values[:12]),
            )
        important = sum(len(re.findall(r"!important", f.text, re.I)) for f in self.project.css_files)
        if important > 12:
            self.add(
                "precision.important",
                "precision",
                "!important is used heavily",
                "low",
                "Specificity escalation makes state overrides unpredictable.",
                "Reduce !important use; fix selector ownership instead.",
                self.anchor,
                evidence=f"{important} !important declarations",
            )
        svg_sizes = set()
        for source in self.project.html_files:
            for match in re.finditer(r"<svg\b[^>]*\b(?:width|height)\s*=\s*[\"'](\d+)", source.text, re.I):
                svg_sizes.add(int(match.group(1)))
        if len(svg_sizes) > 4:
            self.add(
                "precision.icon-sizes",
                "precision",
                "Inline SVG sizes vary without an obvious scale",
                "low",
                "Icon weight and alignment drift when sizes are chosen ad hoc.",
                "Define icon sizes (e.g. 16/20/24) and align them to text.",
                self.anchor,
                evidence=", ".join(str(s) for s in sorted(svg_sizes)),
            )
        literal = ds.literals_vs_tokens.get("colour_literals", 0)
        tokens = ds.literals_vs_tokens.get("token_references", 0)
        if literal >= 12 and (tokens == 0 or literal > tokens * 2):
            self.add(
                "precision.color-tokens",
                "precision",
                "Colour literals outnumber token references",
                "medium",
                "Scattered hex values make themes, dark mode and contrast fixes expensive.",
                "Move recurring colours into named semantic custom properties and reference them.",
                self.anchor,
                evidence=f"{literal} colour literals / {tokens} token references",
                confidence="verified",
            )

    def responsive_rules(self) -> None:
        if self.project.html_files and not self.index.has(r"@media"):
            source = self.anchor
            self.add(
                "responsive.media-queries",
                "responsive",
                "No responsive breakpoints found",
                "high",
                "The layout has no declared adaptation between viewport sizes.",
                "Add layout changes at content-driven breakpoints; verify at mobile, tablet and desktop widths.",
                source,
                evidence="no @media rules in stylesheets",
                confidence="inferred",
            )
        if self.index.has(r"overflow-x\s*:\s*hidden"):
            rule = next((r for r in self.index.rules if re.search(r"overflow-x\s*:\s*hidden", r.body, re.I)), None)
            self.add(
                "responsive.overflow-mask",
                "responsive",
                "Horizontal overflow is hidden",
                "medium",
                "Hiding overflow can conceal a broken layout instead of fixing it.",
                "Find the overflowing element at each viewport; only hide overflow for deliberate clipping.",
                self._source_for(rule.file) if rule else None,
                evidence=_rule_text(rule) if rule else "",
                line=rule.line if rule else None,
                confidence="inferred",
            )
        for rule in self.index.rules:
            width = re.search(r"(?<!max-)(?<!min-)\bwidth\s*:\s*(\d{3,4})px", rule.body, re.I)
            if width and int(width.group(1)) > 720 and not re.search(r"max-width", rule.body, re.I):
                self.add(
                    "precision.fixed-width",
                    "precision",
                    "Fixed width exceeds small viewports",
                    "medium",
                    "A fixed desktop width forces horizontal scrolling or clipping on mobile.",
                    "Use a fluid width with `max-width`, or add a breakpoint override.",
                    self._source_for(rule.file),
                    evidence=_rule_text(rule),
                    dedupe_key=rule.selector,
                    line=rule.line,
                    confidence="inferred",
                )
                break
        for source in self.project.html_files:
            if re.search(r"<table\b", source.text, re.I):
                if not re.search(r"<table\b[^>]*class=[\"'][^\"']*(?:responsive|scroll)|overflow-x|table-(?:scroll|responsive|container|wrapper)", source.text, re.I):
                    self.add(
                        "responsive.table-overflow",
                        "responsive",
                        "Table has no narrow-screen strategy",
                        "low",
                        "Wide tables overflow the viewport and hide columns.",
                        "Allow horizontal scrolling in a labelled region, or switch to a stacked layout.",
                        source,
                        re.search(r"<table\b[^>]*>", source.text, re.I),
                        confidence="inferred",
                    )
        if self.project.html_files and not self.evidence.touch_action:
            self.add(
                "responsive.touch-action",
                "responsive",
                "Controls do not declare touch-action: manipulation",
                "low",
                "Double-tap delay and zoom can make repeated controls feel unresponsive.",
                "Set `touch-action: manipulation` on interactive controls.",
                self.anchor,
                evidence="no touch-action: manipulation",
                confidence="inferred",
            )

    def anti_slop_rules(self) -> None:
        text = "\n".join(f.text for f in self.project.files)
        if re.search(r"lorem ipsum|dolor sit amet", text, re.I):
            source = next((f for f in self.project.html_files if re.search(r"lorem ipsum", f.text, re.I)), None)
            self.add(
                "anti-slop.lorem",
                "content",
                "Lorem ipsum placeholder copy is present",
                "medium",
                "Placeholder copy hides layout problems that real content would reveal.",
                "Replace with representative product copy at short, average and long lengths.",
                source,
                re.search(r"lorem ipsum[^<]{0,80}", source.text, re.I) if source else None,
            )
        hype = r"\b(?:elevate|seamless(?:ly)?|unlock|revolutioni[sz]e|supercharge|empower|effortless(?:ly)?|game[- ]changing|cutting[- ]edge|next[- ]generation)\b"
        hype_matches = list(re.finditer(hype, text, re.I))
        if len(hype_matches) >= 2:
            source = next((f for f in self.project.html_files if re.search(hype, f.text, re.I)), None)
            self.add(
                "anti-slop.hype-copy",
                "content",
                "Promotional filler copy is present",
                "low",
                "Generic superlatives reduce trust and rarely explain what the product does.",
                "Replace with specific, user-facing verbs and outcomes; name things by what users control.",
                source,
                hype_matches[0] if source else None,
                evidence=f"{len(hype_matches)} hype terms; first: {hype_matches[0].group(0)}",
            )
        if re.search(r"linear-gradient\([^)]*(?:#6366f1|#8b5cf6|#a855f7|#7c3aed|#4f46e5|#3b82f6)", text, re.I):
            match = re.search(r"linear-gradient\([^)]*(?:#6366f1|#8b5cf6|#a855f7|#7c3aed|#4f46e5|#3b82f6)[^)]*\)", text, re.I)
            self.add(
                "anti-slop.gradient",
                "anti-slop",
                "Generic purple/blue gradient detected",
                "low",
                "The default AI gradient is rarely tied to product meaning; it reads as a template.",
                "If colour is carrying identity, justify this exact palette; otherwise use a deliberate surface system.",
                self.anchor,
                match,
                confidence="verified",
            )
        if len(re.findall(r"backdrop-filter\s*:\s*blur", text, re.I)) > 2:
            self.add(
                "anti-slop.glass",
                "anti-slop",
                "Glassmorphism is applied repeatedly",
                "low",
                "Blur does not create hierarchy by itself and often reduces legibility.",
                "Use one deliberate translucent surface if it clarifies layering; make the rest opaque.",
                self.anchor,
                evidence="3+ backdrop-filter: blur declarations",
            )
        big_radii = [r for r in self._design_system.radii if re.fullmatch(r"(2[4-9]|[3-9]\d|\d{3,})px", str(r["value"]))]
        if len(big_radii) > 3:
            self.add(
                "anti-slop.radius",
                "anti-slop",
                "Many large border radii are in use",
                "low",
                "Uniform heavy rounding flattens hierarchy and is a common generated-UI default.",
                "Reserve large radii for a specific role; keep nested radii concentric.",
                self.anchor,
                evidence=", ".join(str(r["value"]) for r in big_radii[:8]),
            )

    # ------------------------------------------------------------------
    # Derived component-state findings

    def component_rules(self) -> None:
        toggles = [c for c in self.inventory.components if c.kind == "toggle"]
        missing_toggles = []
        for component in toggles:
            state = next((s for s in component.states if s.name == "on"), None)
            if state and state.status == "missing":
                missing_toggles.append(component)
        if missing_toggles:
            first = missing_toggles[0]
            names = ", ".join(f"{c.name} ({c.file}:{c.line})" for c in missing_toggles[:4])
            self.add(
                "state.toggle-on",
                "component-state",
                f"{len(missing_toggles)} toggle(s) have no distinct ON state",
                "high",
                "ON and OFF are the two essential states of a switch. If users cannot tell them apart, the control lies about the setting.",
                "Style the checked/on state with more than colour alone (position, shape, icon or label), and verify both states.",
                self._source_for(first.file),
                match=None,
                evidence=names,
                confidence="inferred",
                dedupe_key="toggles-on",
                line=first.line,
            )

        async_buttons = []
        for component in self.inventory.components:
            if component.kind == "button":
                state = next((s for s in component.states if s.name == "loading"), None)
                if state and state.status == "missing":
                    async_buttons.append(component)
        if async_buttons:
            component = async_buttons[0]
            self.add(
                "state.button-loading",
                "component-state",
                "Async submit button has no loading state",
                "high",
                "Users cannot tell whether the action started, so they click again or abandon the flow.",
                "Keep the label, add a spinner/progress state, disable the button, and guard against duplicate submits.",
                self._source_for(component.file),
                match=None,
                evidence=f"{len(async_buttons)} affected button(s); first: {component.name}",
                confidence="inferred",
                line=component.line,
            )

        for component in self.inventory.components:
            if component.kind == "input":
                state = next((s for s in component.states if s.name == "invalid"), None)
                if state and state.status == "missing":
                    self.add(
                        "state.input-invalid",
                        "component-state",
                        "Validated input has no invalid state",
                        "high",
                        "Users cannot see which field failed validation when the error appears only on submit.",
                        "Add an invalid style, inline message and `aria-invalid`; keep the value.",
                        self._source_for(component.file),
                        match=None,
                        evidence=f"{component.name} at {component.file}:{component.line}",
                        confidence="inferred",
                        dedupe_key=component.id,
                        line=component.line,
                    )
                    break

        for component in self.inventory.components:
            if component.kind == "dropdown":
                state = next((s for s in component.states if s.name == "empty/no results"), None)
                if state and state.status == "missing":
                    self.add(
                        "state.dropdown-empty",
                        "component-state",
                        "Dropdown has no no-results state",
                        "medium",
                        "A searchable menu with zero matches looks broken unless it explains the emptiness and next step.",
                        "Render a no-results row with the query and a way to clear it.",
                        self._source_for(component.file),
                        match=None,
                        evidence=f"{component.name} at {component.file}:{component.line}",
                        confidence="inferred",
                        dedupe_key=component.id,
                        line=component.line,
                    )
                    break

        for component in self.inventory.components:
            if component.kind == "dialog":
                missing_escape = any(s.name == "escape" and s.status == "missing" for s in component.states)
                missing_focus = any(s.name == "focus" and s.status in {"missing", "partial"} for s in component.states)
                if missing_escape:
                    self.add(
                        "state.dialog-escape",
                        "interaction",
                        "Dialog has no Escape path",
                        "medium",
                        "Escape is a standard dismissal expectation and a keyboard recovery path.",
                        "Close on Escape and return focus to the trigger.",
                        self._source_for(component.file),
                        match=None,
                        evidence=f"{component.name} at {component.file}:{component.line}",
                        confidence="inferred",
                        line=component.line,
                    )
                if missing_focus:
                    self.add(
                        "state.dialog-focus",
                        "accessibility",
                        "Dialog focus handling is incomplete",
                        "high",
                        "Focus can escape into the background, trapping keyboard users in the wrong layer.",
                        "Use a native modal dialog or a tested focus trap with return.",
                        self._source_for(component.file),
                        match=None,
                        evidence=f"{component.name} at {component.file}:{component.line}",
                        confidence="inferred",
                        line=component.line,
                    )

        low_coverage = [c for c in self.inventory.components if c.coverage < 50 and c.kind in {"form", "toggle", "button", "input", "dialog"}]
        if len(low_coverage) >= 3:
            names = ", ".join(c.name for c in low_coverage[:4])
            self.add(
                "state.component-coverage",
                "component-state",
                f"{len(low_coverage)} components have less than 50% state coverage",
                "medium",
                "A component that only works on the happy path is not finished.",
                "Work through the component matrix from highest-risk state to lowest; verify each in the browser.",
                self._source_for(low_coverage[0].file),
                match=None,
                evidence=names,
                confidence="inferred",
                line=low_coverage[0].line,
            )

        if self.evidence.async_flow and not self.evidence.empty_state:
            self.add(
                "state.empty",
                "component-state",
                "No empty state is evidenced for dynamic content",
                "medium",
                "Lists, searches and tables with zero results are common; without an empty state they look broken.",
                "Add intentional empty, no-results and first-run states with a next action.",
                self.anchor,
                evidence="async flow without empty-state copy or component",
                confidence="inferred",
            )

        if re.search(r"\bdisabled\b", "\n".join(f.text for f in self.project.markup_files), re.I) and not self.evidence.disabled_rule:
            source = next(f for f in self.project.markup_files if re.search(r"\bdisabled\b", f.text, re.I))
            self.add(
                "state.disabled-style",
                "component-state",
                "Disabled controls are not visually distinguished",
                "medium",
                "Users try to activate controls that cannot work, without knowing why.",
                "Style disabled controls with reduced emphasis and preserve readable contrast; explain if needed.",
                source,
                re.search(r"<[^>]*\bdisabled\b[^>]*>", source.text, re.I),
                confidence="inferred",
                dedupe_key="disabled",
            )

        states = [s for c in self.inventory.components for s in c.states]
        if states and not any(s.name == "focus" and s.status in {"complete", "partial"} for s in states):
            self.add(
                "a11y.focus-visible",
                "accessibility",
                "Interactive components have no focus state",
                "high",
                "Keyboard navigation is not usable without a visible focus location.",
                "Implement focus-visible styles for every interactive component and verify by tabbing through the flow.",
                self.anchor,
                evidence="no component has an evidenced focus state",
                confidence="inferred",
                dedupe_key="component-focus",
            )

    # ------------------------------------------------------------------
    # Helpers

    @property
    def _design_system(self):
        if not hasattr(self, "_ds_cache"):
            self._ds_cache = extract_design_system(self.project, self.index)
        return self._ds_cache

    def _source_for(self, rel: str) -> SourceFile | None:
        for source in self.project.files:
            if source.rel == rel:
                return source
        return None


def _rule_text(rule) -> str:
    if not rule:
        return ""
    return f"{rule.selector.strip()[:80]} {{ {truncate(rule.body, 100)} }}"


def audit(root: Path | str, include_tests: bool = False) -> dict[str, object]:
    root_path = Path(root).resolve()
    project = discover(root_path, include_tests=include_tests)
    index = css_index(project)
    evidence = collect_evidence(project, index)
    inventory = discover_components(project, index, evidence)
    rules = AuditRules(project=project, index=index, evidence=evidence, inventory=inventory)
    rules.run()

    rules.findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line, f.check))
    for number, finding in enumerate(rules.findings, start=1):
        finding.id = f"FL-{number:04d}"

    design_system = extract_design_system(project, index)
    counts = {severity: sum(1 for f in rules.findings if f.severity == severity) for severity in SEVERITY_ORDER}
    confidence = {
        "verified": sum(1 for f in rules.findings if f.confidence == "verified"),
        "inferred": sum(1 for f in rules.findings if f.confidence == "inferred"),
    }
    component_counts = inventory.counts()
    if not project.files:
        readiness = "insufficient-evidence"
        readiness_reason = "No supported source files were found."
    elif counts["critical"]:
        readiness = "blocked"
        readiness_reason = f"{counts['critical']} critical finding(s) break core flows."
    elif counts["high"]:
        readiness = "at-risk"
        readiness_reason = f"{counts['high']} high-severity finding(s) need resolution before sign-off."
    elif counts["medium"]:
        readiness = "needs-polish"
        readiness_reason = f"{counts['medium']} medium finding(s) remain; core flows are not blocked."
    else:
        readiness = "ready"
        readiness_reason = "No critical, high or medium finding was detected by the static checks."

    limitations = [
        "Static source analysis only: no screenshot or browser was used by this run.",
        "Absence of a state is inferred from missing source evidence; framework-generated state may exist outside scanned files.",
        "Contrast findings use same-block literal colour pairs; variables, gradients, images and alpha compositing are excluded.",
        "Automated checks cannot verify screen-reader usability, cognitive load, or task success. Manual WCAG 2.2 AA review is still required.",
        "Component associations are heuristic and use filename/class evidence; review the matrix instead of treating it as proof.",
    ]
    if project.skipped:
        limitations.append(f"{len(project.skipped)} file(s) skipped (minified, binary, or >2 MB).")

    return {
        "schema_version": "1.0",
        "generator": {
            "name": "finishline",
            "version": "1.0.0",
            "mode": "static",
        },
        "project": {
            "name": project.name,
            "root": ".",
            "stack": project.stack or ["unknown"],
            "files_scanned": len(project.files),
            "lines_scanned": project.lines_scanned,
            "bytes_scanned": project.total_bytes,
            "skipped_files": project.skipped,
        },
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "summary": {
            "readiness": readiness,
            "readiness_reason": readiness_reason,
            "findings": {
                "total": len(rules.findings),
                "critical": counts["critical"],
                "high": counts["high"],
                "medium": counts["medium"],
                "low": counts["low"],
            },
            "confidence": confidence,
            "components": {
                "total": len(inventory.components),
                "complete": component_counts.get("complete", 0),
                "partial": component_counts.get("partial", 0),
                "missing": component_counts.get("missing", 0),
                "state_coverage": inventory.coverage,
                "by_kind": inventory.by_kind(),
            },
        },
        "design_system": {
            "colors": design_system.colors,
            "fonts": design_system.fonts,
            "font_sizes": design_system.font_sizes,
            "spacing": design_system.spacing,
            "radii": design_system.radii,
            "shadows": design_system.shadows,
            "custom_properties": design_system.custom_properties,
            "literals_vs_tokens": design_system.literals_vs_tokens,
            "notes": design_system.notes,
        },
        "components": [component.to_dict() for component in inventory.components],
        "findings": [finding.to_dict() for finding in rules.findings],
        "verification": {
            "mode": "static",
            "rendered": False,
            "checks_run": CHECK_REGISTRY,
            "check_count": len(CHECK_REGISTRY),
            "screenshots": 0,
            "limitations": limitations,
        },
    }