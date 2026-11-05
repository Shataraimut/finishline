---
name: finishline
description: Build, audit, and repair web interfaces to a defensible finish. Use for UI/UX quality reviews, component-state audits, accessibility and responsive checks, design-system cleanup, and any request to make an interface feel truly complete rather than merely styled.
license: MIT
---

# FINISHLINE

**Don't just make it look finished. Make sure it is finished.**

FINISHLINE is an evidence-first interface quality workflow for web UI. It combines a 59-check static audit, a component-state matrix, rendered verification, and a repair loop. It is deliberately skeptical: a clean audit is a hypothesis, not a certificate.

## When to use it

Use this skill when the task is to:

- build a new interface, page, flow, or component system to production quality;
- audit an existing interface before launch, after a redesign, or during a handoff;
- repair a UI that "looks fine" but fails real states, keyboard use, mobile widths, or error paths;
- review generated UI for template defaults, decorative filler, and missing interaction states;
- install a repeatable quality gate in a repository.

Do not treat a static scan as a substitute for using the product. If you cannot render it, say so. If you cannot test it with a keyboard, say so. Never claim visual or accessibility verification you did not perform.

## Non-negotiable evidence rules

1. **Inspect before judging.** Read the source, run the checks, render the page, and exercise the states. Do not infer quality from a screenshot alone.
2. **Every claim needs a location or an observation.** Cite `file:line`, a command, a screenshot, or a test result. "Looks good" is not evidence.
3. **Never fabricate evidence.** No invented screenshots, fake metrics, simulated success logs, or made-up accessibility scores.
4. **Keep confidence honest.** `verified` means directly evidenced in source or a repeatable run. `inferred` means a heuristic found a risk that a human must confirm.
5. **Do not edit the audit to make it green.** Fix the interface, fix a demonstrably wrong rule, or record a reasoned exception. Do not delete inconvenient findings.
6. **A state you did not exercise is not finished.** Hover, focus-visible, active, disabled, loading, empty, error, success, read-only, and destructive confirmation are decisions, not defaults.
7. **Static analysis is not WCAG certification.** Manual keyboard, zoom, screen-reader, and content review still apply.
8. **Preserve the product's actual constraints.** Offline-first, no build step, framework limits, brand rules, and data contracts outrank generic taste.

## Choose the mode

### Build

Use when the interface does not exist yet or is being substantially reworked.

1. Extract the real job: user, task, data, environment, failure modes, and constraints.
2. Define the shell and the design system before decorating screens: type scale, spacing, color roles, focus treatment, motion policy, breakpoints.
3. Inventory every interactive component and write its state matrix before implementation.
4. Build flows end-to-end, including loading, empty, error, success, permission, and recovery paths.
5. Use native semantics first: buttons, links, labels, fieldsets, `dialog`, form validation hooks.
6. Test at 320px, a middle width, and a wide viewport; test keyboard-only and reduced motion.
7. Run the audit, render the result, fix findings, and rerun. Ship with the evidence.

### Audit

Use when the interface exists and the request is to assess it.

1. Confirm scope and run the static audit.
2. Read the report by severity, not by file order.
3. Verify inferred findings in source before repairing them.
4. Capture real viewports and inspect the rendered interface.
5. Exercise the highest-risk flows: auth, destructive actions, async submit, empty search, validation, token/secret reveal.
6. Produce a verdict with limitations, not a score with false confidence.

### Repair

Use when findings exist and the request is to close them.

1. Group findings by root cause, not by rule ID. One missing state system often explains many findings.
2. Repair critical and high first; then medium; then low or explicitly accepted advisories.
3. Re-run the audit after each batch. Add a regression test for every engine bug you fix.
4. Verify the repaired state in the browser, with keyboard and mobile where relevant.
5. Do not lower a severity because it is inconvenient. Lower it only when the evidence changes.

### Verify

Use for a final pass before sign-off or publication.

- Audit JSON validates against `schemas/audit.schema.json`.
- No critical or high findings remain.
- Every medium finding is fixed or recorded as an explicit exception with rationale and owner.
- Screenshots are current, real, and labelled with what they show.
- The workspace report opens offline and its sample/real data status is correct.
- Limitations are stated in the final report.

## Fast path

For a small page with limited time:

```bash
python3 scripts/audit.py path/to/project --out audit.json --fail-on high
python3 scripts/report.py audit.json --format html --out report.html
python3 scripts/capture.py path/to/project --out screenshots --viewports desktop:1440x1000,mobile:390x844
```

Then inspect the top findings, fix the state and accessibility gaps, and rerun until no high findings remain. Do not skip the rendered check if a browser is available.

## Audit workflow

### 1. Scope the evidence

Record:

- the product and the primary task;
- the pages and flows in scope;
- the stack and the files the scanner can see;
- the states that cannot be reached without a backend or credentials;
- the browser, viewport, and assistive technology available.

### 2. Run the static audit

```bash
python3 scripts/audit.py <project> --out audit.json
```

Useful variants:

```bash
python3 scripts/audit.py <project> --include-tests
python3 scripts/audit.py <project> --fail-on high
python3 scripts/audit.py <project> --json
```

The result contains `summary`, `design_system`, `components`, `findings`, and `verification`. Read the summary first. The JSON is the source of truth; the terminal summary is only a triage aid.

### 3. Triage by severity and confidence

- **Critical** blocks a core flow or destroys data.
- **High** makes a primary flow unusable, inaccessible, or deceptive.
- **Medium** creates a real failure or a clearly unfinished state.
- **Low** is drift, polish, or a heuristic worth confirming.

Treat `inferred` findings as questions. Open the cited source. A finding may be a false positive caused by a framework pattern, a nested component, a token alias, or a state expressed in JavaScript rather than CSS.

### 4. Build the component matrix

For every interactive component, record:

`default · hover · focus-visible · active · disabled · loading · empty/no-results · invalid · success · failure · read-only · destructive-confirm`

Not every state applies to every component. Mark `n/a` only when it truly does not apply. Mark `missing` when the state exists conceptually but has no design or implementation. Do not mark a state complete because a browser default exists; state whether that default is acceptable.

Use `templates/state-matrix.md` as the working matrix.

### 5. Render and exercise

```bash
python3 scripts/capture.py <project> --out screenshots \
  --viewports desktop:1440x1000,mobile:390x844
```

`capture.py` records exactly what it captured and what failed. It does not click, type, hover, or validate. If interaction states matter, exercise them with a browser automation tool that is actually available and report the method.

At minimum, check:

- the first screen at desktop and mobile;
- navigation and the current-location cue;
- a form's success and failure path;
- an empty search and a no-results state;
- an async action's pending and completed states;
- a destructive confirmation;
- keyboard focus order and return focus after dialogs;
- 200% zoom and reduced motion if the environment permits.

### 6. Write the report

Use `templates/quality-report.md` or generate one:

```bash
python3 scripts/report.py audit.json --format html --out report.html
python3 scripts/report.py audit.json --format md --out report.md
```

The report must separate evidence from inference and state its limitations. A clean static result is not proof of usability. A screenshot is not proof of interaction.

## Build workflow

### Establish the system

Before the first screen, define:

- semantic color roles and contrast partners;
- one type scale with named steps, not ad-hoc sizes;
- a spacing scale with deliberate optical exceptions;
- radius and elevation rules;
- focus-visible treatment that works on every background;
- motion policy, including a reduced-motion branch;
- breakpoints driven by content, not device brands;
- density and target-size rules for touch.

### Inventory states before styling screens

List the components and the states that can change the user's outcome. Build the state model first. This prevents the common failure where the happy path is polished and every recovery path is absent.

### Build accessible defaults

- One `h1` per page and a logical heading order.
- Landmarks: header, nav, main, complementary where appropriate.
- Visible labels for inputs; placeholders are not labels.
- Error text tied to the field with `aria-describedby`; `aria-invalid` on failure.
- Live regions for asynchronous status and errors.
- Native `dialog` or a tested focus trap; return focus to the trigger.
- Buttons for actions, links for navigation. Do not put click handlers on generic `div`s.
- Text and interactive states that survive forced colors and zoom.
- No motion-only meaning; no color-only state.

### Design the unhappy paths

For every async or data-driven surface, define:

- first load;
- slow load;
- empty collection;
- empty search result;
- partial failure;
- total failure with recovery;
- stale data and refresh;
- permission denied;
- retry and cancellation.

### Anti-template discipline

Reject defaults that signal an unconsidered generated interface: generic purple gradients, glass panels without a product reason, floating cards everywhere, oversized rounded corners, decorative metrics with no meaning, and copy that says nothing specific. These are not banned by taste police; they are suspicious because they usually replace a product decision.

Use `references/anti-slop.md` for the full critique.

## Repair workflow

1. **Reproduce** the finding in the running interface or in source.
2. **Name the root cause.** "The dialog has no focus return" is better than "fix dialog".
3. **Fix the system, not the symptom.** Add the missing state token or primitive, then apply it.
4. **Preserve behavior.** Do not remove a feature to make a check pass.
5. **Verify the state.** Exercise it; do not assume the CSS change works.
6. **Add a regression.** If the bug was in the audit engine, add a fixture or unit test.
7. **Re-run** the audit and compare counts. Explain any movement in severity.

### Exception policy

An exception is acceptable only when:

- the finding is a demonstrated false positive;
- the behavior is intentionally different for a documented product reason;
- the risk is accepted by the owner with a named follow-up.

Record the exception in the report: finding ID, reason, evidence, owner, and expiry or review date. Do not silently suppress it.

## Severity and readiness

| Readiness | Meaning |
|---|---|
| `ready` | No critical, high, or medium static finding; rendered checks still required. |
| `needs-polish` | Medium findings remain; core flows are not blocked. |
| `at-risk` | High findings remain; a primary flow or accessibility path is compromised. |
| `blocked` | Critical findings remain; data, auth, or a core task is broken. |
| `insufficient-evidence` | The scan found nothing it could assess; do not treat this as a pass. |

Severity is about user consequence, not code difficulty. A missing focus ring on the only checkout action is high, not cosmetic. A single off-grid padding is low, even if it is easy to see.

## Definition of finished

An interface is finished only when all of the following are true:

- primary tasks work at mobile and desktop widths without horizontal page overflow;
- keyboard users can reach, operate, and leave every control;
- focus is visible and returns correctly after dialogs and menus;
- loading, empty, error, success, disabled, and destructive states are intentional;
- forms preserve input on failure and explain how to recover;
- async actions prevent duplicate submission and announce status;
- text and controls survive 200% zoom;
- reduced-motion users are not forced through decorative animation;
- no critical or high findings remain;
- medium findings are fixed or explicitly accepted with evidence;
- the report states what was not tested.

## Commands

```bash
# Static audit
python3 scripts/audit.py <project> --out audit.json
python3 scripts/audit.py <project> --fail-on high

# Reports
python3 scripts/report.py audit.json --format md --out report.md
python3 scripts/report.py audit.json --format html --out report.html

# Real viewport screenshots
python3 scripts/capture.py <directory-or-url> --out screenshots \
  --viewports desktop:1440x1000,mobile:390x844

# Load evidence into the offline workspace
python3 scripts/workspace_data.py \
  --audit audit.json \
  --screenshots screenshots/screenshots.json \
  --out ui/workspace/data \
  --label "Project name"

# Validate the package and an audit file
python3 scripts/validate.py --audit audit.json --strict

# Tests
python3 -m unittest discover -s tests -v
```

The workspace is fully static and offline:

```bash
python3 -m http.server 4173 --directory ui/workspace
```

Open `http://127.0.0.1:4173`. It has six routes: overview, findings, components, repairs, visual evidence, verification. The shipped dataset is an explicitly marked sample audit of a deliberately flawed fixture. Do not present it as a real client result.

## File map

```text
finishline/
├── SKILL.md
├── scripts/
│   ├── audit.py              # static audit CLI
│   ├── capture.py            # Chromium viewport capture
│   ├── report.py             # Markdown / self-contained HTML
│   ├── validate.py           # package + audit-schema gate
│   ├── workspace_data.py     # evidence loader for the workspace
│   └── lib/                  # scanner, components, rules, schema check
├── schemas/audit.schema.json
├── references/               # progressive-disclosure guidance
├── templates/                # audit, matrix, report, token starter
├── examples/                 # Meridian: three finished reference pages
├── ui/workspace/             # offline quality workspace
├── tests/                    # fixture + stdlib tests
└── research/                 # competitive analysis and rationale
```

## Reference routing

Read only what the task needs.

| Reference | Read it when |
|---|---|
| `references/design-principles.md` | You need the quality model, hierarchy, composition, or a critique vocabulary. |
| `references/typography.md` | Type scale, line length, line height, font loading, or text hierarchy is in question. |
| `references/color-systems.md` | Defining color roles, fixing contrast, dark mode, or state color. |
| `references/component-states.md` | Building or auditing buttons, inputs, selects, toggles, dialogs, tables, menus, and their state matrices. |
| `references/interaction-feedback.md` | Adding loading, success, failure, empty, optimistic, or undo behavior. |
| `references/ux-writing.md` | Labels, errors, empty states, confirmations, or product voice. |
| `references/accessibility.md` | Keyboard, semantics, focus, live regions, forms, motion, and WCAG 2.2 AA review. |
| `references/responsive-design.md` | Breakpoints, fluid type, tables, touch targets, and small-screen layout. |
| `references/precision.md` | Spacing, alignment, icon scale, z-index, radii, and visual drift. |
| `references/anti-slop.md` | The interface feels generic, overdecorated, or generated. |
| `references/visual-qa.md` | Running the rendered review, capturing evidence, and writing the verdict. |

Templates:

- `templates/design-audit.md` — audit brief and evidence log.
- `templates/state-matrix.md` — component-by-state working matrix.
- `templates/quality-report.md` — final report structure.
- `templates/design-tokens.json` — a sane starting token contract.

## Output contract

A finished audit answers, in this order:

1. **Verdict** — readiness and the single most important reason.
2. **Scope and evidence** — files, routes, viewports, tools, and what was not reached.
3. **Findings** — severity, location, evidence, why it matters, repair.
4. **State coverage** — the component matrix, including missing states.
5. **Repairs** — what changed, what was verified, what remains.
6. **Limitations** — honest gaps in the evidence.
7. **Next action** — the smallest next step that materially reduces risk.

Do not open with a compliment about the design. Do not close with "let me know if you need anything else". Deliver the verdict and the evidence.

## Limits

The static engine cannot see rendered layout, JavaScript-composed states, screen-reader output, or real content. It reads source heuristically and can produce false positives and false negatives. Contrast checks operate on same-block literal pairs; token aliases, alpha compositing, images, and gradients are excluded. Component discovery is heuristic. Screenshots prove pixels existed, not that a flow works.

A clean result means "the static checks found nothing above threshold", not "the product is finished". The rendered and manual steps are part of the method, not optional garnish.
