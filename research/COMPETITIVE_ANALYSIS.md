# FINISHLINE — Competitive Analysis

**Research window:** 2026-11-04
**Method:** shallow clone of primary repositories, source inspection (not README-only), review of public documentation, licence audit, and hands-on comparison against the failure modes FINISHLINE targets. Commit hashes below identify exactly what was inspected.

## 1. Why this document exists

FINISHLINE is an original synthesis. It does not vendor another project's skill text, prompts, or code. This document records what was studied, what was adopted at the level of ideas, what was deliberately rejected, and how licences were handled. The goal is to make the design lineage auditable.

The central gap found in existing work is consistent across ecosystems:

> Most tools are strong at either **generation guidance** (how to design something) or **rule auditing** (how to grep for known violations). Very few close the loop from *generated UI* → *rendered evidence* → *state completeness* → *targeted repair* → *verification*. FINISHLINE is built around that loop.

## 2. Sources inspected

| Source | What it is | Licence | Stars at inspection | Commit inspected |
|---|---|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) — `frontend-design` | Design-direction skill for distinctive UI and anti-templated aesthetics | Apache-2.0 (`LICENSE.txt` in skill folder) | 187k | `ca45fc496a3436251f191354091d557da31c15b5` |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | Official agent skills; `web-design-guidelines`, React/Next performance, composition patterns | MIT | 33.5k | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | Living interface rulebook + agent install path | MIT | 1.1k | `434b7f91364665f2f733b310ec54809bf8f37937` |
| [radix-ui/primitives](https://github.com/radix-ui/primitives) | Unstyled accessible primitives | MIT | 19.5k | package docs, not cloned |
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Copy-in component source built on Radix patterns | MIT | 127k | README/docs inspected |
| [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | Utility-first CSS | MIT | 98k | docs inspected |
| [material-components/material-web](https://github.com/material-components/material-web) | Material 3 web components + token model | Apache-2.0 | 11.4k | docs inspected |
| [w3c/wcag](https://github.com/w3c/wcag) | Normative WCAG source | W3C document licence | 1.5k | WCAG 2.2 recommendation inspected |
| [dequelabs/axe-core](https://github.com/dequelabs/axe-core) | Automated accessibility engine | MPL-2.0 | 7.7k | integration model inspected |
| [pa11y/pa11y](https://github.com/pa11y/pa11y) | CLI accessibility runner | LGPL-3.0 | 4.6k | model inspected |
| [microsoft/playwright](https://github.com/microsoft/playwright) | Browser automation | Apache-2.0 | 99.2k | API model inspected |
| [GoogleChrome/lighthouse](https://github.com/GoogleChrome/lighthouse) | Performance/a11y/best-practice audits | Apache-2.0 | 31k | audit model inspected |
| [style-dictionary/style-dictionary](https://github.com/style-dictionary/style-dictionary) | Token build system | Apache-2.0 | 4.9k | model inspected |
| [BuilderIO/builder](https://github.com/BuilderIO/builder) | Visual development platform; visual editing, Mitosis | MIT | 8.9k | `0e8dbd9852fb40d720d6a138fd414e52dd2056e5` |
| [BuilderIO/mitosis](https://github.com/BuilderIO/mitosis) | Write once, compile components to many frameworks | MIT | 14.5k | README/docs inspected |
| [opencode.ai/docs/skills](https://opencode.ai/docs/skills/) | OpenCode skill discovery and frontmatter contract | docs | — | fetched 2026-11-04 |

Other public guidance consulted conceptually: WAI-ARIA Authoring Practices, W3C WAI WCAG 2.2 Understanding documents, Material Design 3 state-layer documentation, GOV.UK content design and Shopify Polaris content guidance patterns, and the SIL Open Font License. FINISHLINE contains no text copied from those works.

## 3. Findings by category

### 3.1 Frontend design skills

**Anthropic `frontend-design`** is the strongest public example of *design direction* as a skill. It treats the task as a studio brief, demands a compact token plan before code, names current AI visual clichés, and asks the agent to critique its plan against the brief. Its most valuable ideas are non-mechanical:

- The brief's subject matter, not a generic moodboard, should drive aesthetic choices.
- One memorable element; everything else quiet.
- Two-pass process: plan → self-critique → build.
- Written copy is design material, not filler.

**Limitation:** it is primarily generative. It gives direction but no systematic state matrix, no rendered verification loop, no machine-readable findings, no repair queue, and no workspace. It also cannot guarantee that a generated page implements the states it implies.

**Adopted:** brief-first visual direction, the plan/critique gate, the "one bold move" restraint, and explicit anti-cliché reasoning — re-expressed in original language and connected to measurable checks.

### 3.2 Vercel Web Interface Guidelines + `web-design-guidelines`

This is the best curated public *rulebook* for web UI. The repository is an evolving list of interaction, accessibility, form, animation, content and performance requirements, with an agent command that reviews files and emits terse `file:line` findings. The MIT licence permits reuse; nevertheless FINISHLINE paraphrases rules into its own reference architecture rather than bundling their command file.

**Strengths:** high signal-to-noise; practical edge cases (paste blocking, iOS input zoom, hydration, ellipsis, URL state, safe areas, optimistic UI, double-tap zoom); explicitly tells agents to audit generated interfaces.

**Limits:** code-level review only; it does not render the interface, capture screenshots, infer whether a component's *opposite state* exists, or compute design-system consistency. Many rules require human/rendered judgement, and the skill fetches its rules at runtime, which is unsuitable for offline or reproducible audits.

**Adopted:** the MUST/SHOULD discipline, file:line evidence format, and a large set of verifiable interaction rules. FINISHLINE adds evidence confidence labels, static state inference, rendered capture, and a repair workflow.

### 3.3 Design system engineering

**Radix Primitives** separates behaviour and accessibility from visual styling. Its `data-state`, `data-disabled`, `data-side` attributes and focus-management behaviours are a better contract than ad-hoc class names because state is observable in the DOM and therefore testable. **shadcn/ui** demonstrates the copy-in ownership model: components are project source, not a dependency, which makes repair realistic. **Material 3** contributes a systematic state-layer model (hover 8%, focus 10%, pressed 10%, drag 16% opacity; 48dp interactive target vs 40dp state layer) and a role-based semantic colour system. **Style Dictionary** establishes a source-of-truth token pipeline rather than scattered literals.

**Limits:** Radix and shadcn do not audit the surrounding product; Material is opinionated and heavy; token tooling assumes a build pipeline that many small projects do not need.

**Adopted:** observable state contracts (`data-state`, native attributes, ARIA), semantic token roles over raw hex use, state-layer/size guidance as a baseline, and the principle that components must be owned and editable. FINISHLINE supports but does not require any of these libraries.

### 3.4 Component states and interaction feedback

Most component libraries document their own states; almost no agent skill checks whether the *product* supplies every relevant state. The public discourse over-indexes on hover animations and under-indexes on the states that erode trust: submit pending, auth failure, empty search, disabled distinction, unsaved changes, reveal-secret, destructive confirmation, and recovery.

**Adopted:** a state matrix that distinguishes `complete / partial / missing / n/a`, and an explicit feedback-mechanism selection table (inline, toast, banner, dialog, status region, progress). FINISHLINE's rule: feedback must be attached to the real outcome, never simulated for appearance.

### 3.5 Accessibility auditing

**axe-core** is excellent at deterministic checks (labels, roles, contrast in some cases) and poor at task-level usability. **pa11y** wraps headless browsers and CI-friendly reports but inherits the same limits. **Lighthouse** mixes performance, best practices and a subset of a11y with a weighted score that is easy to misread as compliance. WCAG 2.2 itself is the normative source; target size (2.5.8, 24×24 CSS px), focus appearance (2.4.13, AAA), and error identification/announcement are the details agents most often miss.

**Limits:** automated tools can verify only a minority of WCAG success criteria, and none can certify a product. Screenshots and DOM scans do not prove screen-reader usability.

**Adopted:** WCAG 2.2 AA as a design target (not a claim), automated checks limited to what they can actually prove, mandatory manual verification for keyboard/screen-reader/zoom, and explicit "not verified" reporting. FINISHLINE never emits a "WCAG compliant" badge.

### 3.6 Visual QA and browser automation

Playwright is the strongest general automation substrate; Lighthouse is a page-level audit; Chromium headless is the lowest-dependency way to get real pixels. The gap is workflow: tools exist, but agents often claim visual review without capturing anything. FINISHLINE makes capture an explicit, inspectable artifact (`screenshots.json` + PNGs) and requires the agent to state when it did not capture.

**Adopted:** real screenshots, viewport matrices, screenshot manifests, and a hard rule against pretending to have seen pixels. `scripts/capture.py` uses local Chromium when available and records its limitations.

### 3.7 Responsive design auditing

Public checklists list breakpoints but rarely require evidence. Common failures are not "no media query" but: mobile navigation that does not collapse, dialogs with fixed widths, tables that overflow, and desktop-only hover affordances. FINISHLINE checks structural signals statically and requires rendered viewport inspection for overflow, touch targets and navigation adaptation.

### 3.8 Design tokens

Style Dictionary and Material tokens are mature. The practical lesson: name by role and intent (`surface-raised`, `text-muted`, `danger-strong`) rather than by appearance (`gray-200`), and keep contrast decisions close to the pair of roles. FINISHLINE ships a small Draft-compatible token template and statically measures token adoption (literals vs variables), but does not force a token build system.

### 3.9 UX writing

Anthropic's frontend-design skill and Vercel's guidelines both touch copy, but content design is usually absent from UI skills. The strongest public traditions (GOV.UK content design, Polaris, Mailchimp) converge on: plain verbs, sentence case for most UI, action names that persist through the flow, specific errors, and empty states that offer a next step. FINISHLINE adds a compact UX-writing reference and anti-hype checks because promotional copy is one of the clearest AI-generated tells.

### 3.10 Anti-AI-slop methodology

Anthropic's skill names the current cluster: cream + serif + terracotta, near-black + acid accent, newspaper rules, identical SaaS cards, all-caps eyebrows, monospace micro-labels, and arrow-suffixed buttons. Vercel's rules catch some surface symptoms (gradient banding, `transition: all`). No public tool defines a *repeatable anti-slop review* that distinguishes "deliberate for this brief" from "default for any brief".

**Adopted:** a contextual palette/typography selection process, a cliché audit with low-severity advisory findings, and a hard rule that absence of cliché is not proof of quality. FINISHLINE explicitly allows any style when the brief justifies it.

### 3.11 Interface completeness

This is the largest gap. Design systems document components; QA tools test pages; neither produces a component × state completeness matrix derived from the actual codebase. FINISHLINE's Component State Engine treats "no OFF state" or "form has no failure path" as first-class, reportable defects.

### 3.12 Builder.io

Builder.io is a visual development platform: visual editing, headless CMS integrations, and Mitosis for compiling components across frameworks. It is valuable as an existence proof for visual editing and cross-framework component ownership, but it is not an agent skill and requires a hosted/visual workflow. Its model reinforces two FINISHLINE decisions: keep generated UI editable as source, and treat visual inspection as a distinct input from code inspection. FINISHLINE deliberately does not depend on a hosted visual editor or CMS.

## 4. Gap summary

| Capability | Anthropic frontend-design | Vercel WIG | shadcn/Radix | axe/Pa11y | Playwright/Lighthouse | FINISHLINE |
|---|---|---|---|---|---|---|
| Brief-first visual direction | Strong | Weak | N/A | N/A | N/A | Strong |
| Anti-cliché reasoning | Strong | Partial | N/A | N/A | N/A | Strong |
| Semantic design tokens | Partial | Partial | Strong | N/A | N/A | Strong template + audit |
| Component state matrix | Implied | Partial rules | Per-component docs | N/A | N/A | **Core artifact** |
| Missing UX states (empty/error/recovery) | Weak | Partial | N/A | N/A | N/A | **Core artifact** |
| Static code audit | None | Strong | N/A | DOM runtime | DOM runtime | Strong + confidence labels |
| Rendered screenshot QA | Optional | None | N/A | Partial | Strong | Built-in optional capture |
| Repair queue | None | Findings only | N/A | Findings only | Findings only | **Core artifact** |
| Verification ledger | None | None | N/A | Partial | Scores | **Core artifact** |
| Workspace UI | None | None | Docs | Report | Report | **Included** |
| Works without paid service | Yes | Yes | Yes | Yes | Yes | **Yes** |

## 5. Differentiation

1. **Completeness over polish.** The unit of quality is not a screenshot; it is a component's full relevant state set and a user journey's recovery paths.
2. **Three modes, one contract.** Build, Audit and Repair share the same JSON evidence model, so findings survive from generation through repair to verification.
3. **Evidence confidence is explicit.** Every finding is `verified` (direct source evidence) or `inferred` (absence-based / heuristic). Inferred findings are not presented as proven defects.
4. **Static engine + rendered evidence.** The audit script works offline with the Python standard library; optional Chromium capture adds real pixels without requiring Playwright or a paid browser cloud.
5. **State matrix, not a checklist.** Components are inspected individually, and "n/a" is a valid, important answer. FINISHLINE does not demand loading states on a static label.
6. **Anti-slop as context, not a banned-palette list.** Clichés are advisory findings; the brief always wins.
7. **Repair is minimal and reversible.** Repair mode forbids opportunistic redesign, requires a root-cause note, and verifies after the smallest change.
8. **Honest limits.** The skill and the workspace have first-class "not verified" surfaces; no fake screenshots, fake metrics or compliance badges.
9. **OpenCode-native.** Correct skill discovery, frontmatter, progressive disclosure through references, and no runtime network requirement.
10. **Owned and portable.** MIT, standard-library tooling, no build step for the workspace, no hosted dependency.

## 6. Licence and attribution handling

- No source code, prompt text, or reference document from the inspected projects is vendored.
- Ideas are synthesized and expressed in new prose. Where a specific numeric convention is used (for example Material state-layer opacities or WCAG target-size thresholds), it is attributed in the relevant reference file.
- Vercel's guidelines are MIT; FINISHLINE's paraphrase still credits the source.
- Anthropic's `frontend-design` skill is Apache-2.0; FINISHLINE borrows only high-level process concepts, with attribution in `README.md` and here.
- Radix, shadcn, Tailwind, Playwright, axe-core, Pa11y, Lighthouse and Style Dictionary are referenced as optional ecosystem tools, not bundled.
- Bundled fonts: **Newsreader** and **IBM Plex Sans/Mono**, both under the SIL Open Font License 1.1. The OFL text ships in `ui/workspace/fonts/OFL.txt`.
- FINISHLINE itself is MIT.

## 7. What was deliberately rejected

- Copying a competitor's skill prompt or rule list wholesale.
- Framework-specific mandates (React/Next-only advice is offered as an optional appendix, never a requirement).
- Numeric "design scores" presented as objective quality or accessibility compliance.
- A hosted backend for the workspace, analytics, or telemetry.
- Auto-"fixing" without user intent in Audit mode.
- Mandatory component libraries, animation libraries or build tooling.
- Claims of screenshot review when no screenshot was captured.

## 8. Research limitations

- Repository star counts change continuously; values here are a snapshot.
- Public README claims were not trusted; key implementation files and licence files were opened. Some documentation-only projects (Radix docs, Material guidance) were reviewed through their public docs rather than a full source audit.
- The comparison is qualitative. No benchmark of generated UI quality across tools was run; that would require a controlled study and is out of scope for v1.
