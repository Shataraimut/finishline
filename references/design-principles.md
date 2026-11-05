# Design principles

A finished interface is not a collection of attractive screens. It is a system that makes the next action obvious, keeps the user oriented when something goes wrong, and remains coherent under real content and real constraints.

## The quality model

Use five tests, in order:

1. **Legible** — can the user read the hierarchy without effort?
2. **Operable** — can the user act with pointer, keyboard, and touch?
3. **Resilient** — does the interface survive empty, slow, invalid, and failed states?
4. **Honest** — does it say what it will do, and show what actually happened?
5. **Composed** — does the visual system hold together at every density and viewport?

Beauty matters, but it cannot compensate for a missing recovery path. A single missing focus ring on the only primary action is more serious than a slightly imperfect rhythm in a decorative section.

## Hierarchy

Hierarchy is the order in which the eye and the task move. It is produced by position, scale, weight, contrast, and space — not by adding decoration.

- One primary action per decision area. Secondary actions recede.
- Page title, section title, and component title must be distinguishable at a glance.
- Labels belong closer to their controls than to the previous control.
- Error text belongs to the field it describes, not in a distant banner.
- If everything is emphasized, nothing is.

A useful test: blur the interface. Can you still identify the main task, the current location, and the primary action? If not, the hierarchy is relying on fine detail rather than structure.

## Composition

- Use a consistent alignment spine. Decide where content starts and let it hold.
- Prefer a few strong alignments to many local ones.
- Give dense operational screens a calm frame: subdued chrome, strong data, restrained color.
- Do not wrap every section in a card. Cards create boundaries; use them when the boundary means something.
- Whitespace is structural. It should separate groups, not merely distribute emptiness.
- Asymmetry is fine when it reflects task weight. Do not center everything to avoid deciding.

## Density

Density is a product decision. Operational tools often need more information per screen than marketing pages, but density without hierarchy becomes noise.

- Increase density through alignment and type discipline, not by shrinking hit targets.
- Keep touch targets usable when reducing visual weight.
- At high density, reduce decorative borders and shadows before reducing text size.
- At low density, do not hide essential controls behind excessive scroll or oversized hero sections.

## Orientation

The user should always be able to answer:

- Where am I?
- What is this data?
- What changed?
- What can I do next?
- How do I get back?

Use a current-location cue in navigation, a specific page title, and breadcrumbs only when the hierarchy is genuinely deep. Do not use a breadcrumb as decoration for a one-level page.

## Interaction character

- Controls should respond immediately, even when the server cannot.
- Destructive actions should feel deliberate without becoming hostile.
- Loading states should preserve layout and explain what is happening.
- Success should be quiet and specific. Failure should be plain and actionable.
- Motion should clarify a change in state, not perform personality.

## Originality

Originality is not a weird font and a gradient. It comes from a specific product argument: what this tool believes about the work, expressed through structure, language, and restraint.

Ask:

- What would this interface look like if it took the user's actual job seriously?
- Which decisions are here because the product needs them, and which are here because a template had them?
- If the brand were removed, would this still be recognizable as this product?

## Review questions

Use these when a screen feels unfinished but the defect is hard to name:

1. What is the one thing this screen wants me to do?
2. What happens when the data is empty, late, partial, or wrong?
3. Can I recover from a mistake without losing my work?
4. Does the interface explain itself in plain language?
5. Is any state communicated by color alone?
6. Does the layout still work when the text is 200% larger?
7. Are the focal point and the primary action the same thing?
8. Is anything present only to fill space?
9. Does the empty state offer a next step rather than an apology?
10. Would a keyboard user experience the same flow as a pointer user?

## What "finished" does not mean

- It does not mean every surface has a shadow.
- It does not mean every state has an illustration.
- It does not mean the audit count is zero.
- It does not mean the screenshot looks impressive at one viewport.

Finished means the decisions are made, the failure paths are owned, and the evidence supports the claim.
