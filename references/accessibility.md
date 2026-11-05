# Accessibility

Accessibility is a property of the finished interface, not a post-launch patch. The static audit catches source-level risks; only rendered and assistive-technology testing can confirm usability.

This reference targets WCAG 2.2 AA as a baseline. It is not a certification checklist and does not replace a full audit.

## Semantics

- Use native elements for their meaning: `button`, `a`, `input`, `select`, `textarea`, `dialog`, `table`.
- A clickable `div` needs `role`, `tabindex`, keyboard handling, and focus styles — at which point it should usually be a button.
- One `h1` per page; heading levels should not skip for visual convenience.
- Use landmarks: `header`, `nav`, `main`, `aside` or labelled `section`.
- Label every navigation region when there is more than one.
- Use lists for lists, tables for tabular data, and fieldsets for grouped controls.
- Do not use ARIA to paper over incorrect semantics. The first rule of ARIA is to use native HTML.

## Keyboard

Every interactive element must be reachable and operable:

- `Tab` / `Shift+Tab` move focus;
- `Enter` activates links and buttons;
- `Space` activates buttons and toggles checkboxes;
- arrow keys navigate menus, tabs, radios, and grids where expected;
- `Escape` closes dialogs, menus, and popovers;
- focus is visible at all times;
- focus order follows the visual/task order;
- no keyboard trap outside a modal dialog.

Test with the pointer hidden. If you cannot complete the task with the keyboard, the flow is not finished.

## Focus

- Use `:focus-visible` for keyboard focus, with a strong outline and offset.
- Do not remove outlines globally without a replacement.
- Ensure contrast against the component and the surrounding surface.
- On dialog open, move focus to the dialog title or first meaningful control.
- On dialog close, return focus to the trigger.
- When content is removed, move focus to a sensible surviving element.
- Do not auto-focus a field that causes the page to jump unexpectedly.

## Forms

- Visible labels, programmatically associated.
- Required fields marked in text, not only with an asterisk or color.
- Instructions before the field, not only after failure.
- `aria-describedby` for hints and errors.
- `aria-invalid="true"` on invalid fields.
- Error summary at the top of long forms, with links or focus movement to the first error.
- Preserve values after validation failure.
- Group related controls with `fieldset` and `legend`.
- Autocomplete tokens for identity, address, and payment fields where appropriate.
- Do not use placeholder as the only label.
- Avoid custom controls when native ones suffice.

## Images and icons

- Informative images need meaningful `alt`.
- Decorative images use `alt=""`.
- Icon-only buttons need an accessible name.
- Inline SVG icons next to text are usually decorative and should be hidden from assistive technology.
- Complex charts need a text summary or data table.
- Do not put essential text in an image.

## Dynamic content

- Use `aria-live="polite"` for status updates that do not require interruption.
- Use `aria-live="assertive"` or `role="alert"` only for urgent errors.
- Keep live regions in the DOM before updating them.
- Do not announce every keystroke or every polling update.
- Give loading states an accessible status.
- Announce the outcome of async actions, including failure.
- When a dialog opens, announce its title via the accessible name.

## Dialogs

- Native `<dialog>` with `showModal()` is the safest default.
- Provide an accessible name via `aria-labelledby`.
- Move focus inside on open.
- Trap focus while modal (native dialog does this).
- Close on Escape.
- Return focus to the trigger.
- Do not make the backdrop the only close affordance.
- Destructive confirmation needs a safe default and explicit consequence.

## Color and contrast

- Normal text: 4.5:1; large text: 3:1 under WCAG 2.2 AA.
- UI components and meaningful graphics: 3:1 against adjacent colors.
- Do not use color alone to convey state.
- Check hover, focus, selected, disabled, and error states.
- Check placeholder and helper text.
- Check charts in grayscale.
- Test forced-colors mode where possible.

## Motion

- Respect `prefers-reduced-motion: reduce`.
- Remove non-essential animation, parallax, and autoplay.
- Avoid flashing more than three times per second.
- Do not make motion the only signal of a state change.
- Keep loading animations subtle and pausable where they are decorative.
- Ensure content remains usable if animation fails.

## Zoom and reflow

- Content must remain usable at 200% zoom.
- At 320 CSS pixels wide, avoid two-dimensional page scrolling for ordinary content.
- Do not use `user-scalable=no` or `maximum-scale=1` to prevent zoom.
- Text must not clip when enlarged.
- Tables and code blocks may scroll in a labelled region, but the page itself should not overflow.

## Target size

WCAG 2.2 AA includes a minimum target size requirement (24×24 CSS pixels, with exceptions). Treat 44×44 as a comfortable touch target where space permits. Small icon buttons need padding, not just a small visual glyph.

## Screen reader review

At minimum:

- navigate by headings and landmarks;
- read the form labels and error messages;
- operate the primary flow without a pointer;
- confirm dialog title, description, and focus return;
- confirm live announcements are useful, not noisy;
- check that hidden content is actually hidden.

Automated tools cannot confirm any of this.

## WCAG 2.2 AA spot checks

- [ ] Page has a language and a descriptive title.
- [ ] Viewport allows zoom.
- [ ] Images have appropriate alternatives.
- [ ] Inputs have labels.
- [ ] Icon-only controls have names.
- [ ] Focus is visible and logical.
- [ ] Keyboard can complete the primary task.
- [ ] Dialogs have names, Escape, focus entry, and focus return.
- [ ] Errors are identified in text and tied to fields.
- [ ] Status messages are announced.
- [ ] Text and UI contrast pass.
- [ ] Reduced motion is respected.
- [ ] Content reflows at 320px and 200% zoom.
- [ ] Target sizes are usable.
- [ ] No content relies on color alone.

## Honesty

Do not claim "WCAG compliant" from a static scan, a checklist, or one browser pass. Say what you tested, how, and what remains unverified.
