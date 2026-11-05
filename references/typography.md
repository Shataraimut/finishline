# Typography

Typography is the interface's default medium. Most UI quality problems that look like spacing problems are actually type problems: unclear hierarchy, cramped line height, excessive measure, or too many near-neighbor sizes.

## Start with roles, not sizes

Define type by job:

| Role | Typical job | Notes |
|---|---|---|
| Display | Brand or page statement | Use sparingly; one per screen at most. |
| Page title | The page's subject | Should be unmistakable at a glance. |
| Section title | A group within the page | Stronger than body, weaker than page title. |
| Component title | Card, panel, dialog heading | Keep the same rank across the product. |
| Body | Reading and description | Optimize for comfort, not compactness. |
| UI label | Controls and dense metadata | Can be smaller; must remain readable. |
| Microcopy | Captions, timestamps, units | Never use as a hiding place for essential content. |
| Code/data | Identifiers, values, paths | Use tabular figures where comparison matters. |

A named scale prevents the slow drift toward 8.5px, 9px, 9.5px, 10px, 10.5px all existing in one product. Six to eight steps are usually enough. If you need more, name the reason.

## Scale construction

- Choose a base body size from the content and the viewport, not from a trend.
- Use a modular ratio only as a starting point; adjust for optical size.
- Keep small text from becoming decorative dust. Below roughly 12px, readability and contrast become fragile, especially for dense UI.
- Ensure at least a clear step between adjacent ranks. A 13.5px section title over 13px body is not hierarchy.
- Use `rem` for type so browser zoom and user preferences work.
- Use `clamp()` for display type when it prevents awkward wrapping, not for every text element.

## Line height

- Body: usually 1.5–1.7 depending on measure and x-height.
- Dense UI labels: 1.3–1.5.
- Display/headlines: 0.95–1.15, tightened as size increases.
- Multi-line buttons and labels need enough line height to avoid collisions.

Line height is not a universal constant. A 16px body at 70 characters per line needs more leading than a 12px table label.

## Measure

- Reading text: roughly 45–75 characters per line. Around 60–70 is a reliable default.
- Dense data descriptions: shorter is usually better.
- Do not let paragraphs stretch to a 1440px container because the grid allows it.
- Constrain prose separately from layout width.

## Alignment

- Left-align body and labels in left-to-right interfaces.
- Avoid justified text: it creates rivers and uneven word spacing.
- Center only short headings or isolated statements. Centered paragraphs are hard to scan.
- Align numerals for comparison. Use `font-variant-numeric: tabular-nums` for tables, timers, and financial or operational values.
- Do not use letter-spacing to fix a weak typeface at body size. Reserve tracking for uppercase micro-labels and display adjustments.

## Font pairing

- One UI family plus one display or mono companion is usually enough.
- Pair by contrast in role, not by novelty. A serif display with a sans UI and a mono data face can work; three competing sans faces usually do not.
- Check that the families have the weights you actually use. A faux-bold fallback is a defect.
- Use system fallbacks with similar metrics to reduce layout shift.

## Font loading

- Self-host when possible; avoid third-party requests that can fail silently.
- Use `font-display: swap` for text that must remain readable during loading.
- Preload only the fonts needed for the first screen. Preloading everything delays other work.
- Subset fonts when the toolchain supports it, and keep the licence with the files.
- Test the fallback state: layout should not collapse or overflow before the web font arrives.
- Avoid using a webfont for a single decorative glyph.

## Contrast and size

Small type does not get a lower contrast exemption in WCAG. Normal text generally needs 4.5:1; large text can use 3:1 under WCAG 2.2 AA, but "large" has a specific definition (roughly 18pt or 14pt bold). Do not use 11px gray text and call it large.

Check:

- placeholder text (often the worst offender);
- disabled labels (still need to be discernible);
- chart axis labels;
- timestamps and units;
- text over tinted backgrounds;
- secondary text on hover/selected rows.

## Wrapping and truncation

- Prefer wrapping for labels and prose.
- Truncate only when the full value is available on demand (tooltip, detail view, copy).
- Never truncate the only identifier in a table without a way to inspect it.
- Test long words, long names, localization expansion, and URLs.
- Avoid `white-space: nowrap` on anything that can contain user data unless overflow is deliberate.

## Numbers

- Use tabular figures for columns that users compare.
- Align decimal points or use consistent precision.
- Do not mix units in one column without a unit label.
- Format large numbers consistently (1.82M vs 1,820,000) and explain abbreviations.
- In charts, label units clearly and avoid implying precision the data does not have.

## Typography audit checklist

- [ ] Every size belongs to a named role or scale step.
- [ ] Body measure is constrained.
- [ ] Adjacent hierarchy levels are visibly distinct.
- [ ] Line heights match density and measure.
- [ ] Labels are closer to their controls than to neighbors.
- [ ] Placeholder, hint, error, and disabled text meet contrast.
- [ ] Numbers align in comparative contexts.
- [ ] Font fallback does not break layout.
- [ ] No essential content is hidden in tiny or low-contrast text.
- [ ] Text survives 200% zoom without clipping or horizontal page scroll.
