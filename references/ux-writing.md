# UX writing

Interface copy is part of the interaction. A vague label creates a wrong click; a vague error creates a support ticket; a vague empty state creates abandonment.

## Principles

1. **Name the user's object and action.** "Delete API token" is clearer than "Remove".
2. **Be specific.** "Exported 12 requests" beats "Success".
3. **Say what happens next.** "We will email the recovery link" beats "Request received".
4. **Do not blame.** "That password does not match" beats "Invalid input".
5. **Keep the user's work visible.** Say what was preserved after a failure.
6. **Use the product's real vocabulary.** If the product calls it a workspace, do not switch to "project" in the error state.
7. **Prefer plain verbs.** "Save", "Retry", "Copy", "Revoke". Avoid "Utilize", "Leverage", "Proceed".

## Labels

- A label names the value or action, not the implementation.
- Do not use punctuation in button labels unless it is part of the action.
- Keep parallel structure in a group: "Add member", "Remove member", "Resend invite".
- Avoid "OK" and "Submit" when a specific verb exists.
- Icon-only controls need an accessible name and, where ambiguous, a visible tooltip.

## Helper text

Helper text answers a question the user is likely to have before acting:

- format or constraints;
- where the value is used;
- whether it can be changed later;
- what happens on save.

Do not repeat the label. Do not use helper text as a place to hide required information.

## Errors

A useful error has:

- a plain description of the problem;
- the field or object it concerns;
- a recovery action;
- preservation of entered data.

Examples:

| Weak | Better |
|---|---|
| Invalid email | Enter an email in the format name@company.com. |
| Something went wrong | We could not save the workspace. Your changes are still here. Retry. |
| Unauthorized | Your session expired. Sign in again to continue. |
| No results | No requests match "usage". Clear the search or change the status filter. |
| Delete failed | The token was not revoked. Check your connection and try again. |

Do not put raw exception text in the interface. Log it; translate it.

## Empty states

Every empty state should answer:

- Why is this empty?
- Is that expected?
- What can I do next?

Examples:

- First run: "No API keys yet. Create a key to connect your first service."
- No search results: "No requests match 'checkout'. Clear the search or widen the status filter."
- Permission: "You do not have access to this workspace. Ask an owner to invite you."
- Error: "Usage data could not load. Retry, or check the status page."

A decorative illustration without a next action is not an empty state.

## Destructive confirmation

A destructive dialog should:

- name the object;
- state the consequence;
- state what cannot be undone;
- make the safe action the default focus;
- require deliberate confirmation proportional to risk;
- avoid euphemisms.

"Delete Northstar Labs?" is better than "Are you sure?".

For high-consequence actions, type-to-confirm is appropriate. Explain the exact text and keep the confirm control disabled until it matches.

## Success messages

Specific, calm, and connected to the result:

- "Workspace settings saved."
- "API token copied."
- "12 requests exported as CSV."
- "Invite sent to sam@company.com."

Avoid confetti for routine saves. Avoid "Success!" with no object. Do not claim an email was delivered when the product only queued it.

## Voice and tone

- Calm, direct, and human.
- Match the product's domain. An operations console can be precise and dry; a consumer app can be warmer.
- Do not use hype as a substitute for explanation.
- Do not use cuteness in failure states.
- Keep one voice across marketing, empty states, and errors.

## Anti-slop copy test

Reject copy that could belong to any product:

- "Unlock seamless workflows."
- "Elevate your experience."
- "Next-generation insights."
- "Effortless collaboration."
- "Revolutionize the way you work."

Replace with the specific object, action, and outcome. If the sentence still works after removing the product name, it probably says nothing.

## Copy review checklist

- [ ] The primary action uses a specific verb.
- [ ] Error messages explain recovery, not just failure.
- [ ] Empty states offer a next step.
- [ ] Confirmation copy names the consequence.
- [ ] Success copy names what changed.
- [ ] Units, dates, and numbers are unambiguous.
- [ ] The same object keeps the same name across the flow.
- [ ] No placeholder text remains.
- [ ] No hype stands in for a product claim.
- [ ] Copy survives narrow widths and 200% zoom.
