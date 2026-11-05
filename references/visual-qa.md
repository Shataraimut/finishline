# Visual QA

Visual QA is the discipline of looking at the rendered interface with a specific question, recording what you actually saw, and refusing to generalize beyond the evidence.

## Evidence ladder

1. **Source evidence** — the code contains the state, rule, or markup.
2. **Static audit evidence** — the check found a pattern in source.
3. **Rendered evidence** — a real screenshot or browser run at a known viewport.
4. **Interaction evidence** — the state was exercised and observed.
5. **Assistive evidence** — keyboard, screen reader, zoom, or forced-colors testing.

Do not claim a higher rung than you reached. A screenshot is not interaction evidence. A static audit is not rendered evidence.

## Capture setup

Use a deterministic local server and a known browser. Record:

- URL and page;
- browser and version;
- viewport width × height;
- device pixel ratio;
- theme;
- data state;
- whether fonts finished loading;
- what is visible or intentionally cropped.

`capture.py` records viewport screenshots and a manifest. It does not interact. If you need dialog, error, or hover states, use a browser automation tool and record the exact actions.

## Viewport matrix

At minimum:

| Viewport | Purpose |
|---|---|
| 320×700 | Narrow phone; overflow and reflow. |
| 390×844 | Common phone; touch and stacked layout. |
| 768×1024 | Tablet; intermediate composition. |
| 1440×1000 | Desktop; full composition and density. |

For data-heavy screens, add 1024 and 1920. For fixed sidebars, check the breakpoint edges, not only the extremes.

## What to inspect

### Composition

- Is the main task visible without hunting?
- Does the eye land on the intended focal point?
- Are alignment edges consistent?
- Is the page crowded or empty in a way that weakens hierarchy?
- Does the layout still have a point of view at mobile width?

### Typography

- Is the hierarchy legible at a glance?
- Are line lengths controlled?
- Do labels sit closer to their controls than to neighbors?
- Are small labels still readable?
- Do headings wrap acceptably?
- Do numerals align?

### Color and contrast

- Is text legible on every surface?
- Do focus, hover, selected, disabled, and error states read?
- Is meaning conveyed by more than color?
- Does the chart survive grayscale?
- Does forced-colors mode remain usable?

### Spacing and precision

- Are similar components the same height and padding?
- Are icons aligned to text?
- Are borders and shadows consistent?
- Are there accidental 1px gaps or clipped focus rings?
- Does anything shift on hover or load?

### States and flows

- Loading, empty, error, success.
- Form invalid and preserved input.
- Async submit pending and duplicate guard.
- Dialog open, Escape, focus return.
- Destructive confirmation.
- Mobile navigation open, close, and route change.
- Search no-results and reset.

## Interaction test script

Write the steps before running them:

1. Load the page at the target viewport.
2. Tab through the primary flow. Record focus order and visibility.
3. Submit an empty form. Check inline errors, focus movement, and preserved input.
4. Submit valid data with a slow response. Check pending state and duplicate prevention.
5. Force a failure. Check recovery and data preservation.
6. Open a dialog. Check focus entry, Escape, backdrop, and focus return.
7. Open the mobile menu. Check `aria-expanded`, scroll lock, Escape, and route change.
8. Trigger an empty search. Check the no-results copy and reset.
9. Check 200% zoom.
10. Enable reduced motion. Check that non-essential motion is removed.

Record the result of each step, not just "looks good".

## Screenshot review method

- Compare against the intended hierarchy, not your memory of the previous screenshot.
- Inspect at 100% zoom; do not judge from a downscaled chat preview.
- Crop and zoom into dense areas.
- Check the edges: clipping, overflow, fixed elements, and scrollbars.
- Look at the longest content, not the happy-path sample.
- Inspect the empty and error states with the same care as the hero.
- Compare desktop and mobile for loss of meaning, not pixel equality.

## Writing the verdict

Use this shape:

- **Verdict:** readiness and the most important reason.
- **Verified:** what you directly observed, with method and viewport.
- **Inferred:** what the source suggests but you did not exercise.
- **Defects:** severity, location, evidence, repair.
- **Not tested:** the honest gaps.
- **Next action:** the smallest high-value step.

Bad:

> The UI looks great and is fully accessible.

Good:

> Static audit: 0 critical/high. Rendered: 1440 and 390 reviewed; login, dashboard, and settings exercised. The settings delete dialog returns focus to the trigger. Not tested: screen reader, forced-colors mode, 200% zoom. Two low-severity spacing advisories remain.

## Evidence hygiene

- Do not use a screenshot from an old build.
- Do not crop out a failure.
- Do not claim a state was tested because it exists in code.
- Do not use fake data in a screenshot and present it as production evidence.
- Label sample and fixture data clearly.
- Keep the audit JSON that produced the report.
- If the capture manifest records skipped pages, include them in limitations.

## Red flags in your own review

- You only looked at the first viewport.
- You did not open the empty or error state.
- You did not use the keyboard.
- You judged contrast by eye.
- You treated a clean static scan as a pass.
- You wrote "fully accessible".
- You ignored a warning because it was "just low".
- You changed the audit data instead of the interface.
