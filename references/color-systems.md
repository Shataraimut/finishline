# Color systems

Color is a role system before it is a palette. A screen that uses twenty unrelated hex values is not colorful; it is undecided.

## Define roles

At minimum:

| Role | Purpose |
|---|---|
| Canvas | The page background. |
| Surface | Cards, panels, dialogs. |
| Surface raised | Menus, popovers, nested panels. |
| Ink | Primary text. |
| Ink muted | Secondary text. |
| Ink faint | Non-essential metadata, if contrast allows. |
| Line | Default borders and dividers. |
| Line strong | Emphasized boundaries and input borders. |
| Brand | Primary action and identity. |
| Brand strong | Hover/pressed states and high-emphasis brand surfaces. |
| Brand soft | Selected backgrounds and quiet brand tint. |
| Accent | A second, intentional emphasis; not a second primary. |
| Success / warning / danger / info | Semantic states, each with a soft background and a readable foreground. |
| Focus | A focus indicator that works on every surface. |

Name roles by purpose, not by hue. `--ink-muted` survives a rebrand; `--gray-500` does not explain its job.

## Contrast

Under WCAG 2.2 AA:

- normal text: at least 4.5:1;
- large text: at least 3:1 (with the standard's size definition);
- UI components and graphical objects needed to understand content: at least 3:1 against adjacent colors;
- focus indicators: visible and sufficiently contrasting.

Do not rely on a contrast checker that only reads one theme. Check the actual rendered pair.

Common failures:

- muted text on a warm paper background (often just under 4.5:1);
- placeholder text at 2.5–3:1;
- white text on a mid-tone brand color;
- disabled text that is technically exempt but functionally invisible;
- state colors used as the only signal;
- text over an image or gradient without a stable backing surface;
- borders that disappear in forced-colors mode.

## Semantic color is not decoration

Success, warning, danger, and info should mean the same thing everywhere. Do not use red for a decorative accent and then expect users to read red as "error".

Pair color with at least one other signal:

- icon or shape;
- text label;
- position;
- pattern or border style;
- an explicit state word.

A green dot alone is not a status. A green dot plus the word "Operational" is.

## State color

- Hover: a small shift in surface, border, or text; do not rely on hue alone.
- Focus-visible: a distinct outline with offset, not the same color as the border.
- Active/pressed: a deeper surface or a small displacement; avoid layout shift.
- Selected: background plus a persistent marker (check, bar, label).
- Disabled: reduced emphasis, still legible, and clearly non-interactive.
- Invalid: border plus message plus `aria-invalid`; do not turn the entire form red.
- Loading: neutral motion or text, not a success color.

## Dark mode

Dark mode is a second role mapping, not an inversion of the light palette.

- Reduce pure-white text to avoid halation.
- Do not reuse light-mode shadows; use borders and surface elevation.
- Check semantic colors again; saturated brand colors often fail on dark surfaces.
- Keep photographs and illustrations from glowing.
- Ensure charts remain distinguishable without relying on hue alone.
- Test focus rings on both the canvas and raised surfaces.

If dark mode is not a real product requirement, do not add a half-finished toggle. A broken theme is worse than no theme.

## Charts and data color

- Use a restrained categorical palette with distinguishable lightness as well as hue.
- Do not encode meaning by color alone; add labels, patterns, or direct annotation.
- Provide a table or summary for users who cannot read the chart.
- Ensure grid lines and axis labels are visible but subordinate.
- Do not use red/green as the only distinction for gain/loss.
- Check the chart in grayscale and with reduced contrast.

## Tokens and literals

- Keep color literals in the token layer.
- Reference roles in components.
- If a color appears in more than one place, it is a token candidate.
- Avoid scattering `rgba()` values for borders and shadows; define them.
- When exceptions are needed, name them and document why.

The audit's `precision.color-tokens` finding is a signal, not a mandate. A few literals in a self-contained demo can be fine; dozens of near-duplicate grays usually are not.

## Accessibility checks

- [ ] Text and background pairs meet the relevant contrast threshold.
- [ ] Placeholder and hint text meet contrast.
- [ ] Focus indicator is visible on every surface.
- [ ] State is not conveyed by color alone.
- [ ] Links are distinguishable from body text without relying only on color, or are otherwise identifiable.
- [ ] Charts have a non-color reading path.
- [ ] Forced-colors mode leaves controls and boundaries visible.
- [ ] Disabled controls remain understandable.
- [ ] Hover and selected rows are distinguishable from default rows.
- [ ] The palette survives the rendered check, not just the token file.
