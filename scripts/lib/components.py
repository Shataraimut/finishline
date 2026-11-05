"""Component discovery and state-matrix inference from source evidence.

The matrix is explicitly labelled as static inference in the audit output.
A missing state means "no source evidence was found", not "the state is proven
broken". Rendered verification can upgrade confidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .scanner import CSSIndex, CSSRule, Project, SourceFile, parse_attributes, strip_tags, truncate


VALID_STATE_STATUSES = {"complete", "partial", "missing", "n/a"}


@dataclass
class StateAssessment:
    name: str
    status: str
    evidence: str
    confidence: str = "inferred"

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "evidence": truncate(self.evidence, 180),
            "confidence": self.confidence,
        }


@dataclass
class Component:
    kind: str
    name: str
    file: str
    line: int
    states: list[StateAssessment]
    element: str = ""
    id: str = ""

    @property
    def coverage(self) -> int:
        relevant = [s for s in self.states if s.status != "n/a"]
        if not relevant:
            return 100
        points = sum(1 if s.status == "complete" else 0.5 if s.status == "partial" else 0 for s in relevant)
        return round(100 * points / len(relevant))

    @property
    def status(self) -> str:
        relevant = [s for s in self.states if s.status != "n/a"]
        if not relevant:
            return "complete"
        if any(s.status == "missing" for s in relevant):
            return "partial" if self.coverage >= 50 else "missing"
        if any(s.status == "partial" for s in relevant):
            return "partial"
        return "complete"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "status": self.status,
            "coverage": self.coverage,
            "element": truncate(self.element, 220),
            "states": [s.to_dict() for s in self.states],
        }


@dataclass
class Evidence:
    """Project-level signals used to assess individual components."""

    focus_visible: bool
    focus_rule: bool
    focus_replacement: bool
    hover_rule: bool
    active_rule: bool
    disabled_rule: bool
    invalid_rule: bool
    loading: bool
    success_feedback: bool
    error_feedback: bool
    empty_state: bool
    validation: bool
    async_flow: bool
    submit_handler: bool
    escape_handling: bool
    focus_management: bool
    unsaved_warning: bool
    reveal_secret: bool
    toast_live: bool
    native_reduced_motion: bool
    transition: bool
    dark_mode: bool
    touch_action: bool


def collect_evidence(project: Project, index: CSSIndex) -> Evidence:
    text = "\n".join(f.text for f in project.files)
    js = "\n".join(f.text for f in project.script_files)
    markup = "\n".join(f.text for f in project.markup_files)

    focus_visible = bool(index.has(r":focus-visible"))
    focus_rule = focus_visible or bool(index.has(r":focus(?!-visible)"))
    focus_replacement = bool(
        re.search(r":focus(?:-visible)?[^{]*\{[^}]*outline\s*:\s*(?!none|0)", index.text, re.I | re.S)
        or re.search(r":focus(?:-visible)?[^{]*\{[^}]*box-shadow\s*:", index.text, re.I | re.S)
    )
    loading = bool(
        re.search(r"aria-busy|is-loading|loading|spinner|skeleton|progress", markup + js, re.I)
    )
    success_feedback = bool(
        re.search(
            r"(toast|alert|status|feedback)[^\n]{0,80}(success|saved|created|updated|copied)|"
            r"(success|saved|created|updated|copied)[^\n]{0,80}(toast|alert|status|feedback)",
            markup + js,
            re.I,
        )
        or re.search(r"role=[\"']status[\"']", markup, re.I)
    )
    error_feedback = bool(
        re.search(
            r"role=[\"']alert[\"']|aria-live=[\"']assertive[\"']|\.error\b|error-message|form-error|field-error|invalid-feedback",
            markup + js,
            re.I,
        )
    )
    empty_state = bool(
        re.search(r"no results|no matches|nothing (?:here|yet)|no items|empty[-_ ]?state|is-empty|emptyState|data-empty", text, re.I)
        or re.search(r"role=[\"']status[\"'][^>]*>\s*(?:No|Nothing)", text, re.I)
    )
    validation = bool(
        re.search(r"\brequired\b|aria-invalid|setCustomValidity|:invalid|\.invalid|\.error\b|validate\(", markup + js, re.I)
    )
    async_flow = bool(
        re.search(r"\bfetch\s*\(|\baxios\b|XMLHttpRequest|\$\.ajax|useSWR|useQuery|await\s+.*\(", js)
    )
    submit_handler = bool(
        re.search(r"addEventListener\s*\(\s*[\"']submit[\"']|onSubmit\s*=|@submit\s*=|onsubmit\s*=", js + markup, re.I)
    )
    escape_handling = bool(re.search(r"Escape|keydown|keyup|key:\s*[\"']Escape|keyCode\s*===?\s*27", js, re.I))
    focus_management = bool(re.search(r"aria-modal|inert|focus-trap|focusTrap|\.focus\(\)", js + markup, re.I))
    unsaved_warning = bool(
        re.search(r"beforeunload|isDirty|dirty|unsaved|useBeforeUnload", js + markup, re.I)
    )
    reveal_secret = bool(
        re.search(r"show[-_ ]?password|toggle[-_ ]?password|reveal[-_ ]?secret|showApiKey|type=[\"']password[\"']", js + markup, re.I)
        and re.search(r"aria-label=[\"'][^\"']*(?:show|hide|reveal)[^\"']*[\"']|show[-_ ]?password|toggle[-_ ]?password", js + markup, re.I)
    )
    toast_live = bool(re.search(r"aria-live", markup, re.I))
    native_reduced_motion = bool(re.search(r"prefers-reduced-motion", index.raw_text or index.text, re.I))
    transition = bool(re.search(r"transition\s*:|animation\s*:|@keyframes", index.text, re.I))
    dark_mode = bool(re.search(r"prefers-color-scheme|data-theme|\.dark\b", text, re.I))
    touch_action = bool(re.search(r"touch-action\s*:\s*manipulation", index.raw_text or index.text, re.I))

    return Evidence(
        focus_visible=focus_visible,
        focus_rule=focus_rule,
        focus_replacement=focus_replacement,
        hover_rule=bool(index.has(r":hover")),
        active_rule=bool(index.has(r":active")),
        disabled_rule=bool(index.has(r":disabled|\[disabled\]|\[aria-disabled")),
        invalid_rule=bool(index.has(r":invalid|\[aria-invalid|\.invalid|\.error")),
        loading=loading,
        success_feedback=success_feedback,
        error_feedback=error_feedback,
        empty_state=empty_state,
        validation=validation,
        async_flow=async_flow,
        submit_handler=submit_handler,
        escape_handling=escape_handling,
        focus_management=focus_management,
        unsaved_warning=unsaved_warning,
        reveal_secret=reveal_secret,
        toast_live=toast_live,
        native_reduced_motion=native_reduced_motion,
        transition=transition,
        dark_mode=dark_mode,
        touch_action=touch_action,
    )


def _classes(attrs: dict[str, str]) -> list[str]:
    raw = attrs.get("class") or ""
    if not raw or raw.startswith("{"):
        return []
    return [c for c in re.split(r"\s+", raw) if c]


def _class_state_rule(index: CSSIndex, classes: list[str], pattern: str) -> CSSRule | None:
    for class_name in classes:
        rule = index.state_for_class(class_name, pattern)
        if rule:
            return rule
    return None


def _rule_evidence(rule: CSSRule) -> str:
    return f"{rule.selector.strip()[:80]} ({rule.file}:{rule.line})"


def _class_variant(attrs: dict[str, str], variant: str) -> bool:
    raw = attrs.get("class") or ""
    return bool(re.search(rf"(^|\s){re.escape(variant)}:", raw))


def _svg_only(inner: str) -> bool:
    cleaned = re.sub(r"<svg\b.*?</svg>", " ", inner, flags=re.I | re.S)
    return not strip_tags(cleaned)


def _element_name(kind: str, attrs: dict[str, str], inner: str, fallback: str) -> str:
    for key in ("aria-label", "title", "placeholder", "name", "id", "data-testid"):
        value = attrs.get(key, "").strip()
        if value and not value.startswith("{"):
            return truncate(value, 48)
    text = strip_tags(inner)
    if text:
        return truncate(text, 48)
    return fallback


def _button_states(
    attrs: dict[str, str],
    name: str,
    index: CSSIndex,
    evidence: Evidence,
    in_form: bool,
) -> list[StateAssessment]:
    classes = _classes(attrs)
    is_submit = attrs.get("type", "").lower() == "submit" or (
        in_form and attrs.get("type", "submit").lower() not in {"button", "reset"}
    )
    async_relevant = evidence.async_flow and is_submit
    states: list[StateAssessment] = [StateAssessment("default", "complete", "element present", "verified")]

    for state_name, pattern, variant in (("hover", ":hover", "hover"), ("active", ":active", "active")):
        rule = _class_state_rule(index, classes, pattern)
        if rule:
            states.append(StateAssessment(state_name, "complete", _rule_evidence(rule), "verified"))
        elif _class_variant(attrs, variant):
            states.append(StateAssessment(state_name, "complete", f"{variant}: utility variant", "verified"))
        elif index.has(rf"\bbutton{pattern}") or index.has(rf"\ba{pattern}"):
            states.append(StateAssessment(state_name, "partial", f"generic {pattern} rule only"))
        else:
            states.append(StateAssessment(state_name, "missing", f"no {pattern} styling found"))

    rule = _class_state_rule(index, classes, r":focus-visible")
    if rule:
        states.append(StateAssessment("focus", "complete", _rule_evidence(rule), "verified"))
    elif _class_variant(attrs, "focus-visible") or _class_variant(attrs, "focus"):
        states.append(StateAssessment("focus", "complete", "focus utility variant", "verified"))
    elif evidence.focus_visible:
        states.append(StateAssessment("focus", "partial", "project-level :focus-visible rule"))
    elif evidence.focus_rule:
        states.append(StateAssessment("focus", "partial", "only generic :focus styling"))
    else:
        states.append(StateAssessment("focus", "missing", "no focus styling found"))

    disabled_relevant = in_form or evidence.async_flow or "disabled" in attrs
    if disabled_relevant:
        rule = _class_state_rule(index, classes, r":disabled|\[disabled\]|\[aria-disabled")
        if rule:
            states.append(StateAssessment("disabled", "complete", _rule_evidence(rule), "verified"))
        elif _class_variant(attrs, "disabled"):
            states.append(StateAssessment("disabled", "complete", "disabled utility variant", "verified"))
        elif "disabled" in attrs:
            states.append(StateAssessment("disabled", "partial", "attribute present; no distinct style for this button"))
        elif evidence.disabled_rule:
            states.append(StateAssessment("disabled", "partial", "project-level disabled styling only"))
        else:
            states.append(StateAssessment("disabled", "missing", "no disabled styling found"))
    else:
        states.append(StateAssessment("disabled", "n/a", "no form or async action"))

    if async_relevant:
        if re.search(r"loading|spinner|aria-busy", " ".join([attrs.get("class", ""), name]), re.I):
            states.append(StateAssessment("loading", "complete", "loading hook on button", "verified"))
        elif evidence.loading:
            states.append(StateAssessment("loading", "partial", "async flow and loading UI elsewhere"))
        else:
            states.append(StateAssessment("loading", "missing", "async submit with no loading state"))
    else:
        states.append(StateAssessment("loading", "n/a", "no async submit action"))

    states.append(StateAssessment("success", "n/a", "feedback belongs to the form or journey"))
    return states


def _toggle_states(
    attrs: dict[str, str],
    index: CSSIndex,
    evidence: Evidence,
    native_checkbox: bool = False,
) -> list[StateAssessment]:
    classes = _classes(attrs)
    states: list[StateAssessment] = []
    custom = not native_checkbox or bool(classes) or attrs.get("role") == "switch"

    rule = _class_state_rule(index, classes, r":not\(:checked\)|\[aria-checked=[\"']?false|\[data-state=[\"']?(?:off|unchecked)")
    if rule:
        states.append(StateAssessment("off", "complete", _rule_evidence(rule), "verified"))
    elif custom and classes:
        base = _class_state_rule(index, classes, r".")
        states.append(
            StateAssessment("off", "complete" if base else "missing", _rule_evidence(base) if base else "no base styling")
        )
    else:
        states.append(StateAssessment("off", "complete", "native checkbox appearance", "verified"))

    on_rule = _class_state_rule(index, classes, r":checked|\[aria-checked=[\"']?true|\[data-state=[\"']?(?:on|checked)")
    if on_rule:
        states.append(StateAssessment("on", "complete", _rule_evidence(on_rule), "verified"))
    elif _class_variant(attrs, "checked") or _class_variant(attrs, "aria-checked"):
        states.append(StateAssessment("on", "complete", "checked utility variant", "verified"))
    elif attrs.get("role") == "switch" or (custom and classes):
        states.append(StateAssessment("on", "missing", "no checked/on rule found"))
    else:
        states.append(StateAssessment("on", "complete", "native checkbox appearance", "verified"))

    focus_rule = _class_state_rule(index, classes, r":focus")
    if focus_rule or evidence.focus_visible:
        states.append(StateAssessment("focus", "complete" if focus_rule else "partial", _rule_evidence(focus_rule) if focus_rule else "project-level focus styling"))
    else:
        states.append(StateAssessment("focus", "missing", "no focus styling found"))

    disabled_rule = _class_state_rule(index, classes, r":disabled|\[disabled\]|\[aria-disabled")
    if disabled_rule:
        states.append(StateAssessment("disabled", "complete", _rule_evidence(disabled_rule), "verified"))
    elif "disabled" in attrs or evidence.disabled_rule:
        states.append(StateAssessment("disabled", "partial", "disabled attribute or generic styling only"))
    else:
        states.append(StateAssessment("disabled", "missing", "no disabled styling found"))

    if custom:
        transition_rule = _class_state_rule(index, classes, r".")
        has_transition = bool(
            transition_rule and re.search(r"transition", transition_rule.body, re.I)
        ) or evidence.transition
        states.append(
            StateAssessment(
                "transition",
                "complete" if has_transition else "missing",
                "transition present" if has_transition else "state changes abruptly",
            )
        )
    else:
        states.append(StateAssessment("transition", "n/a", "native control"))
    return states


def _input_states(
    attrs: dict[str, str],
    index: CSSIndex,
    evidence: Evidence,
    in_form: bool,
    required: bool,
) -> list[StateAssessment]:
    classes = _classes(attrs)
    input_type = attrs.get("type", "text").lower()
    states = [StateAssessment("default", "complete", "element present", "verified")]

    focus_rule = _class_state_rule(index, classes, r":focus-visible") or _class_state_rule(index, classes, r":focus")
    if focus_rule:
        states.append(StateAssessment("focus", "complete", _rule_evidence(focus_rule), "verified"))
    elif evidence.focus_visible:
        states.append(StateAssessment("focus", "partial", "project-level :focus-visible styling"))
    elif evidence.focus_rule:
        states.append(StateAssessment("focus", "partial", "generic :focus styling only"))
    else:
        states.append(StateAssessment("focus", "missing", "no focus styling found"))

    states.append(StateAssessment("filled", "n/a", "text remains legible without separate filled chrome"))

    invalid_relevant = in_form and (required or input_type in {"email", "password", "number", "url", "tel"})
    if invalid_relevant:
        rule = _class_state_rule(index, classes, r":invalid|\[aria-invalid|\.invalid|\.error")
        if rule:
            states.append(StateAssessment("invalid", "complete", _rule_evidence(rule), "verified"))
        elif "aria-invalid" in attrs:
            states.append(StateAssessment("invalid", "partial", "aria-invalid present; no style rule"))
        elif evidence.invalid_rule:
            states.append(StateAssessment("invalid", "partial", "generic invalid styling only"))
        else:
            states.append(StateAssessment("invalid", "missing", "validation exists without error styling"))
    else:
        states.append(StateAssessment("invalid", "n/a", "no validation requirement inferred"))

    rule = _class_state_rule(index, classes, r":disabled|\[disabled\]|\[aria-disabled")
    if rule:
        states.append(StateAssessment("disabled", "complete", _rule_evidence(rule), "verified"))
    elif "disabled" in attrs:
        states.append(StateAssessment("disabled", "partial", "attribute present; no distinct style for this input"))
    elif evidence.disabled_rule:
        states.append(StateAssessment("disabled", "partial", "project-level disabled styling only"))
    else:
        states.append(StateAssessment("disabled", "missing", "no disabled styling found"))

    if "readonly" in attrs:
        rule = _class_state_rule(index, classes, r"\[readonly\]|:read-only|\.readonly")
        states.append(
            StateAssessment("readonly", "complete" if rule else "partial", _rule_evidence(rule) if rule else "native readonly only")
        )
    else:
        states.append(StateAssessment("readonly", "n/a", "readonly not used"))

    states.append(StateAssessment("loading", "n/a", "inputs are not submitted in place"))
    return states


def _form_states(
    attrs: dict[str, str],
    inner: str,
    index: CSSIndex,
    evidence: Evidence,
    is_async: bool,
) -> list[StateAssessment]:
    classes = _classes(attrs)
    states: list[StateAssessment] = []
    has_fields = bool(re.search(r"<(?:input|textarea|select)\b", inner, re.I))

    if not has_fields:
        states.append(StateAssessment("validation", "n/a", "no fields detected"))
    elif evidence.validation:
        rule = _class_state_rule(index, classes, r":invalid|\.error") or index.matching(r":invalid|\.error")
        states.append(
            StateAssessment(
                "validation",
                "complete" if rule else "partial",
                _rule_evidence(rule[0]) if rule else "validation attributes/handlers without styling",
            )
        )
    else:
        states.append(StateAssessment("validation", "missing", "form has no validation evidence"))

    if is_async:
        states.append(
            StateAssessment(
                "pending",
                "complete" if evidence.loading else "missing",
                "async submit with loading UI" if evidence.loading else "async submit without loading UI",
            )
        )
        states.append(
            StateAssessment(
                "success",
                "complete" if evidence.success_feedback else "missing",
                "success feedback present" if evidence.success_feedback else "no success feedback detected",
            )
        )
        states.append(
            StateAssessment(
                "failure",
                "complete" if evidence.error_feedback else "missing",
                "failure feedback present" if evidence.error_feedback else "no failure feedback detected",
            )
        )
    else:
        states.append(StateAssessment("pending", "n/a", "no async submit inferred"))
        states.append(StateAssessment("success", "n/a", "native form submission or redirect"))
        states.append(StateAssessment("failure", "n/a", "native form submission or redirect"))
    return states


def _dialog_states(
    attrs: dict[str, str],
    inner: str,
    evidence: Evidence,
    native_dialog: bool,
) -> list[StateAssessment]:
    states = [StateAssessment("open", "complete", "dialog element present", "verified")]
    close_control = bool(
        re.search(r"<(?:button|a)\b[^>]*(?:aria-label=[\"'][^\"']*close|data-close|class=[\"'][^\"']*close)", inner, re.I)
    )
    states.append(
        StateAssessment(
            "close",
            "complete" if (close_control or native_dialog) else "missing",
            "close control or native dialog close" if (close_control or native_dialog) else "no close control detected",
        )
    )
    states.append(
        StateAssessment(
            "escape",
            "complete" if (evidence.escape_handling or native_dialog) else "missing",
            "Escape handling present" if (evidence.escape_handling or native_dialog) else "no Escape handling detected",
        )
    )
    states.append(
        StateAssessment(
            "focus",
            "complete" if evidence.focus_management else "partial",
            "focus management signals present" if evidence.focus_management else "focus trap/return not evidenced",
        )
    )
    states.append(StateAssessment("confirm", "n/a", "confirmation only where the action is destructive"))
    return states


def _dropdown_states(
    attrs: dict[str, str],
    inner: str,
    evidence: Evidence,
) -> list[StateAssessment]:
    states = [
        StateAssessment("closed", "complete", "closed state is the default", "verified"),
        StateAssessment(
            "open",
            "complete" if re.search(r"aria-expanded|data-state|\.open\b|is-open", attrs.get("class", "") + inner, re.I) else "missing",
            "expanded state hook present" if re.search(r"aria-expanded|data-state|\.open\b|is-open", attrs.get("class", "") + inner, re.I) else "no expanded state hook",
        ),
        StateAssessment(
            "selected",
            "complete" if re.search(r"aria-selected|aria-current|selected", attrs.get("class", "") + inner, re.I) else "missing",
            "selected hook present" if re.search(r"aria-selected|aria-current|selected", attrs.get("class", "") + inner, re.I) else "no selected state hook",
        ),
        StateAssessment(
            "empty/no results",
            "complete" if evidence.empty_state else "missing",
            "no-results copy present" if evidence.empty_state else "no no-results copy detected",
        ),
        StateAssessment(
            "disabled",
            "complete" if re.search(r"disabled|aria-disabled", attrs.get("class", "") + " ".join(attrs), re.I) else "partial",
            "disabled hook present" if re.search(r"disabled|aria-disabled", " ".join(attrs), re.I) else "browser default only",
        ),
    ]
    return states


@dataclass
class ComponentInventory:
    components: list[Component] = field(default_factory=list)

    @property
    def coverage(self) -> int:
        if not self.components:
            return 100
        weights = sum(len([s for s in c.states if s.status != "n/a"]) for c in self.components)
        if not weights:
            return 100
        points = 0.0
        for component in self.components:
            for state in component.states:
                if state.status == "complete":
                    points += 1
                elif state.status == "partial":
                    points += 0.5
        return round(100 * points / weights)

    def counts(self) -> dict[str, int]:
        counts = {"complete": 0, "partial": 0, "missing": 0}
        for component in self.components:
            counts[component.status] = counts.get(component.status, 0) + 1
        return counts

    def by_kind(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for component in self.components:
            counts[component.kind] = counts.get(component.kind, 0) + 1
        return counts


def _mask_non_markup(text: str) -> str:
    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    text = re.sub(r"<script\b[^>]*>.*?</script>", blank, text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", blank, text, flags=re.I | re.S)
    return text


def _find_label(source: SourceFile, attrs: dict[str, str], offset: int) -> str:
    element_id = attrs.get("id", "")
    if element_id:
        for match in re.finditer(r"<label\b[^>]*for\s*=\s*[\"']" + re.escape(element_id) + r"[\"'][^>]*>(.*?)</label>", source.text, re.I | re.S):
            label = strip_tags(match.group(1))
            if label:
                return label
    return ""


def _form_spans(source: SourceFile) -> list[tuple[int, int]]:
    spans = []
    for match in re.finditer(r"<form\b[^>]*>(.*?)</form>", source.text, re.I | re.S):
        spans.append((match.start(), match.end()))
    return spans


def _in_spans(offset: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in spans)


def discover_components(project: Project, index: CSSIndex, evidence: Evidence) -> ComponentInventory:
    inventory = ComponentInventory()
    index_counter = 0
    seen: set[tuple[str, str, int]] = set()

    for source in project.markup_files:
        masked = _mask_non_markup(source.text)
        spans = _form_spans(source)
        for match in re.finditer(r"<([a-zA-Z][\w:-]*)\b([^>]*)>", masked):
            tag_name = match.group(1).lower()
            raw_tag = match.group(0)
            attrs = parse_attributes(raw_tag)
            role = attrs.get("role", "").lower()
            class_blob = attrs.get("class", "")
            offset = match.start()
            line = source.line_at(offset)
            kind = None
            name = ""
            states: list[StateAssessment] = []

            class_tokens = {token.lower() for token in re.split(r"\s+", class_blob) if token}
            toggle_container = tag_name in {"button", "label", "div", "span", "a"} and bool(class_tokens & {"switch", "toggle"})
            nested_switch_input = False
            if toggle_container and tag_name != "button":
                window = masked[match.end() : match.end() + 700]
                nested = re.search(r"<input\b[^>]*>", window, re.I)
                if nested:
                    nested_attrs = parse_attributes(nested.group(0))
                    nested_switch_input = (
                        nested_attrs.get("role", "").lower() == "switch"
                        or nested_attrs.get("type", "").lower() in {"checkbox", "radio"}
                    )
            is_toggle = (
                role == "switch"
                or (tag_name == "input" and attrs.get("type", "").lower() == "checkbox" and bool(class_tokens & {"switch", "toggle", "switch-input", "toggle-input"}))
                or (toggle_container and not nested_switch_input)
            )
            is_dialog = tag_name == "dialog" or role == "dialog" or re.search(r"\bmodal\b", class_blob, re.I)
            is_dropdown = role in {"combobox", "listbox"} or re.search(r"\b(dropdown|combobox|menu)\b", class_blob, re.I)
            is_feedback = role in {"status", "alert"} or "aria-live" in attrs or re.search(r"\b(toast|alert|notification)\b", class_blob, re.I)

            if is_toggle:
                inner = masked[match.end() : match.end() + 400]
                inner = inner.split("</button>")[0] if "</button>" in inner else inner
                kind = "toggle"
                name = _element_name(tag_name, attrs, inner, "Toggle")
                native = tag_name == "input"
                states = _toggle_states(attrs, index, evidence, native_checkbox=native)
            elif tag_name == "button" or role == "button":
                inner = masked[match.end() : match.end() + 500]
                if "</button>" in inner:
                    inner = inner.split("</button>")[0]
                else:
                    inner = re.split(r"<(?!/?(?:span|strong|em|b|i|svg|path|circle|rect|line|polyline))", inner)[0]
                kind = "button"
                name = _element_name(tag_name, attrs, inner, "Button")
                states = _button_states(attrs, name, index, evidence, _in_spans(offset, spans))
            elif tag_name == "input" and attrs.get("type", "text").lower() not in {"hidden", "submit", "button", "reset", "image", "checkbox", "radio", "file"}:
                kind = "input"
                label = _find_label(source, attrs, offset)
                name = label or _element_name(tag_name, attrs, "", "Input")
                required = "required" in attrs or attrs.get("aria-required", "").lower() == "true"
                states = _input_states(attrs, index, evidence, _in_spans(offset, spans), required)
            elif tag_name == "textarea":
                kind = "input"
                label = _find_label(source, attrs, offset)
                name = label or _element_name(tag_name, attrs, "", "Textarea")
                states = _input_states(attrs, index, evidence, _in_spans(offset, spans), "required" in attrs)
            elif tag_name == "select":
                kind = "select"
                name = _find_label(source, attrs, offset) or _element_name(tag_name, attrs, "", "Select")
                states = [
                    StateAssessment("closed", "complete", "native select", "verified"),
                    StateAssessment("selected", "complete", "native select handles selection", "verified"),
                    StateAssessment("empty/no results", "n/a", "native option list"),
                    StateAssessment("disabled", "complete" if evidence.disabled_rule else "partial", "disabled styling present" if evidence.disabled_rule else "browser default only"),
                ]
            elif is_dialog:
                inner = masked[match.end() : match.end() + 2500]
                if "</dialog>" in inner:
                    inner = inner.split("</dialog>")[0]
                kind = "dialog"
                name = _element_name(tag_name, attrs, inner, "Dialog")
                states = _dialog_states(attrs, inner, evidence, native_dialog=tag_name == "dialog")
            elif is_dropdown and tag_name != "select":
                inner = masked[match.end() : match.end() + 900]
                kind = "dropdown"
                name = _element_name(tag_name, attrs, inner, "Dropdown")
                states = _dropdown_states(attrs, inner, evidence)
            elif tag_name == "form":
                inner = masked[match.end() :]
                if "</form>" in inner:
                    inner = inner.split("</form>")[0]
                kind = "form"
                form_name = attrs.get("aria-label") or attrs.get("name") or attrs.get("id") or "Form"
                name = truncate(form_name, 48)
                is_async = evidence.async_flow and (evidence.submit_handler or "onsubmit" in attrs)
                states = _form_states(attrs, inner, index, evidence, is_async)
            elif is_feedback:
                kind = "feedback"
                name = _element_name(tag_name, attrs, masked[match.end() : match.end() + 200], "Feedback region")
                states = [
                    StateAssessment("polite announcement", "complete" if "aria-live" in attrs else "missing", "aria-live present" if "aria-live" in attrs else "no aria-live"),
                    StateAssessment("success", "complete" if evidence.success_feedback else "missing", "success feedback detected" if evidence.success_feedback else "no success feedback detected"),
                    StateAssessment("error", "complete" if evidence.error_feedback else "missing", "error feedback detected" if evidence.error_feedback else "no error feedback detected"),
                ]

            if not kind:
                continue
            signature = (kind, source.rel, line)
            if signature in seen:
                continue
            seen.add(signature)
            index_counter += 1
            component = Component(
                id=f"C-{index_counter:03d}",
                kind=kind,
                name=name or kind.title(),
                file=source.rel,
                line=line,
                states=states,
                element=raw_tag,
            )
            inventory.components.append(component)
            if len(inventory.components) >= 120:
                return inventory

    return inventory
