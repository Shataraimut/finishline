# Component states

A component is not finished when its default state renders. It is finished when every state a user can reach has a deliberate appearance and behavior.

## The working matrix

For each component, track:

| State | Question |
|---|---|
| Default | What does it look like at rest? |
| Hover | Is there a pointer affordance without layout shift? |
| Focus-visible | Can a keyboard user see where they are? |
| Active/pressed | Does the control acknowledge the press? |
| Disabled | Is it clearly unavailable, and does the user know why? |
| Loading | Is the action in progress, and is duplicate submission blocked? |
| Empty/no results | What happens when there is nothing to show? |
| Invalid | Is the error attached to the right field and announced? |
| Success | Is completion specific and visible? |
| Failure | Is recovery possible without losing work? |
| Read-only | Does it look different from disabled, and can the value be used? |
| Destructive confirm | Is the consequence explicit and reversible where possible? |

Use `templates/state-matrix.md` to record status. A blank is not `n/a`.

## Buttons

- Default label should name the action, not the mechanism ("Save changes", not "Submit").
- Hover and active states must not move surrounding layout.
- Focus-visible needs an outline or equivalent indicator with clear offset.
- Disabled buttons are often a dead end. Prefer an enabled button that explains what is missing, or keep the button enabled and validate on submit. If disabled, provide a reason nearby.
- Async submit: keep the label, add a spinner or progress text, set `aria-busy`, disable repeat activation, and guard the handler. Do not change the button to an unrelated width.
- Destructive buttons need stronger affordance and confirmation proportional to the consequence.
- Icon-only buttons need an accessible name and a visible tooltip where the icon is ambiguous.
- Button groups need clear grouping and keyboard order.

A loading state that replaces text with an unlabeled spinner is not finished. Preserve meaning.

## Text inputs and textareas

- Always have a visible label. Placeholders are examples, not labels.
- Keep the value on validation failure.
- Error text goes next to the field, tied with `aria-describedby`; set `aria-invalid="true"`.
- Do not clear the field to "help" the user.
- Show constraints before submission where possible.
- Autocomplete tokens should match the real purpose.
- Read-only and disabled are different states; do not style them identically.
- Password fields need a reveal control with a proper accessible name and state.
- Textareas need a resize policy that does not break the layout.
- Input font size at or above 16px prevents iOS zoom on focus.

## Selects and comboboxes

- Native selects are often better than custom menus; use them unless the design truly needs search or grouping.
- Custom comboboxes need keyboard support: open, arrow navigation, typeahead, Enter, Escape, and return focus.
- The empty/no-results state needs copy and a way to clear the query.
- The selected state must be visible beyond color.
- Do not hide the label inside the control.
- Multi-select needs a clear summary and a way to remove each item.

## Checkboxes, radios, and switches

- A switch implies an immediate effect; a checkbox can be staged and submitted. Do not use a switch for a value that only applies after Save.
- The on and off states must differ by more than hue: position, shape, icon, or explicit label.
- Keep a visible state word (`On` / `Off`) when the effect is not self-evident.
- Use fieldsets and legends for groups.
- Disabled options need a reason if the user might otherwise try them.
- Ensure the label is clickable and the target is large enough.

## Dialogs

- Prefer native `<dialog>` with `showModal()` for modal behavior.
- Every dialog needs a title and a close path.
- Escape must close the dialog.
- Focus moves into the dialog on open and returns to the trigger on close.
- Focus must not escape into the background while the dialog is modal.
- Destructive dialogs need specific consequences, a safe default, and confirmation proportional to risk.
- A type-to-confirm field must match exactly and explain the expected text.
- Do not stack dialogs.
- Backdrop click closing is a product decision; if enabled, ensure unsaved work is not lost silently.

## Menus and popovers

- Open with Enter/Space, navigate with arrows, select with Enter, close with Escape.
- Return focus to the trigger.
- Do not rely on hover to reveal essential actions.
- Position within the viewport and handle collisions.
- Close on outside click without swallowing the click target.
- Use `aria-expanded` and `aria-controls`.

## Tables

- Use real table semantics: `table`, `thead`, `tbody`, `th scope`.
- Make the table scroll region keyboard-accessible and labelled.
- Do not hide columns without a way to reach their data.
- Row selection needs a persistent indicator and a summary of selected items.
- Sortable headers need a button and `aria-sort`.
- Empty results need a no-results state, not an empty tbody.
- On narrow screens, choose horizontal scroll, priority columns, or stacked records deliberately.
- Keep numeric alignment and tabular figures.

## Toasts and inline feedback

- Toasts are for transient confirmation, not for critical errors that require action.
- Use `role="status"` or `aria-live="polite"`; reserve assertive announcements for urgent failures.
- Do not auto-dismiss an error the user must read.
- Keep the message specific and actionable.
- Avoid covering primary controls or the only close affordance.
- Provide a persistent inline path for anything important.

## Empty states

Distinguish:

- first-run empty: explain the value and offer the first action;
- no-results empty: echo the query and offer a clear reset;
- permission empty: explain who can grant access;
- error empty: explain what failed and how to retry.

An empty state that says "No data" and nothing else is a dead end.

## State coverage test

For every component, ask: "If I could only see this state, would I know what happened and what to do next?" If not, the state is incomplete.
