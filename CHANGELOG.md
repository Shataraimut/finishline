# Changelog

All notable changes to FINISHLINE are documented here. The format follows Keep a Changelog; versions use semantic versioning.

## [1.0.0] — 2026-11-05

### Added

- 59-check static UI/UX audit engine for HTML, CSS, JS, Vue, Svelte, and Astro.
- Strict audit JSON schema and dependency-free schema validator.
- Markdown and self-contained HTML report generation.
- Chromium viewport capture with a real manifest and explicit limitations.
- Six-route offline quality workspace with sample audit, component matrix, repairs, visual evidence, and verification.
- Meridian reference pages: login, dashboard, and settings, with demo-only data and full interaction states.
- Eleven progressive-disclosure references covering design principles, typography, colour, component states, interaction feedback, UX writing, accessibility, responsive design, precision, anti-slop, and visual QA.
- Audit brief, state matrix, quality report, and role-based token starter templates.
- Deliberately defective fixture with 32 findings, 3 critical, and 44 missing/partial component states.
- Standard-library test suite covering engine correctness, regression cases, CLIs, schema, reports, workspace data, and package gates.
- Original competitive analysis and rationale in `research/COMPETITIVE_ANALYSIS.md`.

### Notes

- The static engine is heuristic and does not certify WCAG compliance.
- Bundled fonts are used under the SIL Open Font License; attribution is included in both font directories.
- The shipped workspace dataset is a labelled sample audit, not a client result.
