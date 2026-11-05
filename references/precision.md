# Precision

Precision is not pixel perfection. It is the absence of accidental variation. A deliberate 3px optical adjustment is precision; eleven different gaps that all mean "a little space" is drift.

## Spacing

- Choose a base unit, usually 4px or 8px.
- Use it for layout rhythm, component padding, and gaps.
- Allow optical exceptions for type, icons, and alignment — then document or tokenize them.
- Avoid near-neighbors: 13px, 14px, 15px, and 17px in the same role usually indicate indecision.
- Spacing should express grouping: tighter inside a group, looser between groups.
- Check vertical rhythm across sections, not just inside one card.
- Do not use margin on both the parent and the child to create the same gap.

A useful rule: if two values differ by 1–2px and do not solve a visible optical problem, consolidate them.

## Alignment

- Pick an alignment spine and keep it.
- Labels, values, and actions should align to a small number of edges.
- Optical alignment can differ from mathematical alignment for icons, punctuation, and display type.
- Center alignment is appropriate for short isolated statements; it is usually wrong for forms and lists.
- Baseline alignment matters in mixed type and icon rows.
- Do not align a button's text to an edge if the button has a border that changes the optical center.

## Icons

- Define a small size scale: commonly 16, 20, and 24.
- Match icon weight to text weight.
- Keep icon optical size consistent even when the bounding boxes differ.
- Decorative icons should be hidden from assistive technology.
- Icon-only controls need a name and a comfortable target.
- Do not mix outlined and filled icons without a semantic rule.
- Align icons to the text baseline or cap height deliberately.

## Radii

- Radius should follow a role system: sharp for utility, moderate for panels, pill only for tags or chips.
- Nested radii should be concentric when the inner element sits inside a rounded parent.
- Very large radii on every card makes hierarchy mushy.
- Radius is not a substitute for spacing.
- Check how backgrounds, borders, and focus rings interact at the corners.

## Shadows and elevation

- Use shadows to express layering, not to decorate every surface.
- Prefer borders in dense operational UI; shadows can become noisy.
- Keep a small elevation scale.
- Shadows need a light-direction assumption. Do not mix directions.
- Do not rely on shadow alone to indicate focus or selection.
- Check shadows on dark and tinted surfaces.

## Borders

- Define default, strong, and focus boundaries.
- 1px borders can disappear on high-DPI displays or in forced-colors mode; verify.
- Do not use a border and a shadow for the same boundary without a reason.
- Table borders should clarify reading, not create a grid cage.
- Dividers should be quieter than component boundaries.

## Z-index

Define a small layer scale:

```css
--z-base: 0;
--z-sticky: 10;
--z-dropdown: 20;
--z-overlay: 30;
--z-modal: 40;
--z-toast: 50;
```

- Do not invent a new large number for each component.
- Avoid z-index conflicts by creating stacking contexts intentionally.
- Test dialogs, menus, toasts, and sticky headers together.
- A high z-index does not fix a DOM-order or portal problem.

## Motion

- Define durations and easings by role: fast feedback, standard transition, deliberate entrance.
- Prefer short durations for state changes and longer for larger spatial moves.
- Do not use `transition: all`.
- Animate transform and opacity where possible; avoid layout properties.
- Respect reduced motion.
- Keep motion consistent across similar interactions.

## Density

- Precision at high density requires stronger hierarchy, not smaller everything.
- Reduce decorative borders before reducing text size.
- Keep target sizes usable.
- Use consistent row heights within a table or list.
- Align numeric columns and action columns.
- Check the table at its narrow and wide states.

## Tokenization

Tokens are useful when they encode decisions:

- color role;
- type role;
- spacing step;
- radius role;
- elevation;
- layer;
- duration.

Tokens are not useful when they merely rename every arbitrary value. A token set with 28 type sizes has not solved the scale problem.

## Pixel review

At 100% zoom, inspect:

- icon and text baselines;
- border alignment at corners;
- 1px gaps between adjacent surfaces;
- inconsistent padding across similar components;
- table cell alignment;
- focus ring clipping;
- dialog edge alignment;
- sticky header overlap.

At 200% zoom, inspect overflow, clipping, and focus visibility.

## Practical audit

- [ ] Layout spacing uses a small scale with documented exceptions.
- [ ] Similar components share padding and height.
- [ ] Icons use a defined size scale.
- [ ] Radii and shadows express a small number of roles.
- [ ] Z-index values are layered by role.
- [ ] Borders and dividers do not compete.
- [ ] No `transition: all`.
- [ ] Tabular numbers align in comparative contexts.
- [ ] Focus rings are not clipped by overflow.
- [ ] The visual system holds at mobile, desktop, and 200% zoom.
