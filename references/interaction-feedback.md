# Interaction feedback

Feedback is how the interface tells the truth about time, state, and consequence. The goal is not more spinners. The goal is to reduce uncertainty without adding noise.

## Time and response

Use rough thresholds as design guidance, not guarantees:

- **Under ~100ms:** feels instant. No loading indicator needed unless the action changes the screen substantially.
- **~100ms–1s:** a subtle pending state is enough. Keep the control stable.
- **Longer than ~1s:** show progress or a specific busy state, preserve layout, and prevent duplicate submission.
- **Longer than ~10s:** offer explanation, cancellation where possible, and a path to leave and return.

Network time is not under your control. Design for the slow case, not the demo case.

## Async buttons

A complete async button:

- keeps a meaningful label;
- adds a spinner or progress word without changing width abruptly;
- sets `aria-busy="true"`;
- disables repeat activation;
- guards the handler against double submits;
- restores itself on failure;
- announces the outcome.

Do not replace the label with a bare spinner. Do not remove the button from the layout. Do not leave the user guessing whether the click registered.

## Loading placeholders

- Skeletons are useful when the final structure is known and stable.
- Do not animate every block. Motion should be gentle and removable.
- Preserve the final layout dimensions to avoid a jump.
- Use a text status for screen readers.
- If loading takes longer than expected, add a message rather than an infinite shimmer.

A skeleton is not an empty state. If the result may be empty, loading must resolve into a designed empty state.

## Success

Success should be:

- specific: what changed, and where;
- proximate: near the action, or in a persistent status area;
- quiet: do not celebrate routine actions;
- durable enough to be read;
- paired with an updated view, not just a toast.

For an edit flow, update the displayed value. For a destructive flow, confirm the new state. For a background job, explain where the result will appear.

## Errors

An error needs four parts:

1. **What happened** — plain language, no error codes as the whole message.
2. **Why** — only if known; do not invent a cause.
3. **What to do** — a recovery action or a concrete next step.
4. **What was preserved** — reassure that the user's work still exists.

Field-level errors belong beside the field. Form-level errors belong at the form summary with links or focus movement to the first invalid field. A toast alone is not enough for a form error.

Do not blame the user. Do not say "Something went wrong" if you know what happened. Do not expose raw stack traces or internal identifiers in user-facing copy.

## Optimistic UI

Optimistic updates are appropriate when:

- the action is low-risk and easy to reverse;
- failure is rare or detectable quickly;
- the user benefits from immediate feedback;
- the interface can reconcile the final server truth.

They are a poor fit for payments, deletions, permissions, or anything where a false success is expensive. If you use optimistic UI, design the rollback and explain the failure.

## Undo versus confirmation

- Prefer undo for reversible actions (archive, remove from list, dismiss).
- Use confirmation for irreversible or high-consequence actions (delete workspace, revoke a key).
- Do not use both for the same action unless the consequence is genuinely severe.
- An undo window should be long enough to notice and act, and it must not be the only record of what happened.

## Toasts

Toasts are transient. Use them for:

- confirmation of a completed action;
- a non-blocking warning;
- a copy success;
- a background refresh.

Do not use them for:

- validation errors that require correction;
- information the user must act on later;
- anything that covers the only close button;
- long explanations.

Make them live-region accessible, avoid auto-dismissing critical messages, and keep them out of the main reading flow.

## Refresh and stale data

- Show when data was last updated.
- Distinguish a manual refresh from a passive poll.
- Keep previous data visible while refreshing when that is safer than a blank screen.
- Explain if a refresh failed and the data may be stale.
- Do not silently replace user-edited values with server data.

## Network failure

Design the failure path before the happy path:

- retry without losing input;
- offline detection where the product depends on connectivity;
- timeout copy that says what to try;
- a fallback for partial data;
- a way to export or copy work if the app cannot save.

## Feedback anti-patterns

- Spinner replaces the whole page for a small action.
- Success toast appears before the server confirms.
- Error toast disappears before it can be read.
- Button changes width and shifts the layout.
- Double-click sends two requests.
- Form clears on failure.
- Infinite skeleton with no timeout.
- "Success" without showing what changed.
- A modal confirmation for a reversible action that already has undo.
