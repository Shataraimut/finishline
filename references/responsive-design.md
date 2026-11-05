# Responsive design

Responsive design is not a set of device sizes. It is the interface's ability to keep its hierarchy and tasks intact as space changes.

## Set breakpoints from content

Choose breakpoints where the layout actually breaks:

- navigation no longer fits;
- a table's priority columns become unreadable;
- a form's labels and fields collide;
- a chart's labels overlap;
- a two-column composition loses its reading order.

Do not copy device brand widths. Test at 320, 360, 390, 768, 1024, 1280, and a wide desktop. Use the widths that matter to the content.

## Mobile-first or desktop-first?

Either can work. What matters is that the base layout is coherent, not that one direction is morally superior. Avoid desktop CSS with a pile of emergency overrides at the bottom.

## Navigation

- On small screens, a labelled menu button with `aria-expanded` and `aria-controls`.
- The drawer or menu must close on navigation, Escape, and outside activation.
- Focus should move into the menu when it opens and return to the trigger when it closes.
- Lock background scroll while a full-screen drawer is open, and restore it on close.
- Keep the current-location cue visible.
- Do not hide primary navigation behind a hamburger on a wide screen where it fits.

## Forms

- Single column on narrow screens.
- Inputs at 16px or larger to avoid iOS focus zoom.
- Labels above fields or clearly associated; do not rely on floating labels.
- Keep error text adjacent.
- Make submit actions full width when the form is narrow, but do not make every button full width by reflex.
- Avoid multi-column forms that force a horizontal scroll.

## Tables

Choose a strategy:

1. **Horizontal scroll** in a labelled, keyboard-accessible region. Good for dense operational data where columns must stay comparable.
2. **Priority columns.** Hide low-priority columns and provide a detail view.
3. **Stacked records.** Turn each row into a labelled block. Good for small datasets and simple content.
4. **Responsive table component.** More complexity; verify semantics and keyboard support.

Never let the page itself scroll horizontally because a table is too wide. Do not clip columns without a path to the data.

## Charts

- Provide a responsive viewBox and preserve the aspect ratio where labels need to remain readable.
- At narrow widths, reduce label density rather than shrinking text below legibility.
- Add a text summary or data table for screen readers.
- Do not rely on hover-only tooltips for essential values.
- Ensure the chart does not overflow its card.

## Touch and target size

- Minimum 24×24 CSS pixels under WCAG 2.2 AA; 44×44 is a better comfort target.
- Space targets so adjacent actions are not easy to hit by mistake.
- Do not rely on hover for touch users.
- Avoid tiny close buttons and dense icon clusters.
- Provide enough padding around inline text actions.

## Fluid type and space

- `clamp()` works well for display type and section spacing.
- Do not fluid-size body text so small that it becomes unreadable on phones.
- Use `min()`, `max()`, and `clamp()` for containers rather than fixed widths.
- Avoid fixed pixel widths above the smallest supported viewport unless they have a fluid override.

## Overflow

- Find the element causing horizontal overflow; do not hide it with `overflow-x: hidden` as a first response.
- Code blocks, tables, and long identifiers may scroll inside a labelled container.
- Break long words where appropriate: `overflow-wrap: anywhere` for identifiers, not for prose.
- Test with long localized strings and user-generated names.

## Safe areas and viewport units

- Use `dvh`/`svh` with fallbacks when mobile browser chrome changes.
- Respect `env(safe-area-inset-*)` for fixed bottom bars on notched devices.
- Do not put essential actions under the home indicator.

## Images and media

- Use responsive images with `srcset`/`sizes` where the format supports it.
- Reserve intrinsic dimensions to prevent layout shift.
- Provide a meaningful crop at small sizes, not just a scaled-down desktop image.
- Test dark mode and contrast for images with overlaid text.

## Responsive review matrix

| Surface | 320 | 390 | 768 | 1024 | 1440 |
|---|---|---|---|---|---|
| Header/nav | | | | | |
| Hero/page head | | | | | |
| Forms | | | | | |
| Tables | | | | | |
| Charts | | | | | |
| Dialogs | | | | | |
| Empty/error states | | | | | |
| Long content | | | | | |

Record what you actually checked. A screenshot at 1440 does not prove the 320 layout.

## Common failures

- Desktop nav collapsed too early or too late.
- Table clipped instead of scrolled.
- 14px inputs causing iOS zoom.
- Hero text that wraps into a single word per line.
- Fixed-width dialogs wider than the viewport.
- Sticky elements covering the focused field.
- Horizontal page scroll from a decorative element.
- Tap targets smaller than the visual button.
- Toast covering the only action.
- Charts with unreadable axis labels at 390px.
