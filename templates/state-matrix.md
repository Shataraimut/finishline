# Component state matrix

Status values: `complete`, `partial`, `missing`, `n/a`.
Evidence should cite a selector, file:line, test step, or screenshot.

| Component | Variant | Default | Hover | Focus | Active | Disabled | Loading | Empty | Invalid | Success | Failure | Read-only | Confirm | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary button | default | | | | | | | n/a | n/a | | | n/a | n/a | |
| Secondary button | default | | | | | | | n/a | n/a | | | n/a | n/a | |
| Danger button | destructive | | | | | | | n/a | n/a | n/a | | n/a | | |
| Text input | required | | | | n/a | | n/a | n/a | | n/a | n/a | | n/a | |
| Password input | reveal | | | | n/a | | n/a | n/a | | n/a | n/a | | n/a | |
| Select | native | | | | n/a | | n/a | | | n/a | n/a | | n/a | |
| Switch | immediate | | | | n/a | | | n/a | n/a | n/a | n/a | n/a | n/a | |
| Search field | filter | | | | n/a | | | | n/a | n/a | n/a | | n/a | |
| Dialog | info | | n/a | | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | |
| Dialog | destructive | | n/a | | n/a | n/a | | n/a | | n/a | | n/a | | |
| Table | default | | | | n/a | n/a | | | n/a | n/a | | n/a | n/a | |
| Mobile nav | drawer | | | | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | |
| Toast | status | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | | | n/a | n/a | |

## Missing-state notes

Record the highest-risk gaps here. For each, name the user consequence and the intended repair.

| Component | Missing state | User consequence | Repair | Verified |
|---|---|---|---|---|
| | | | | |

## State rules

- A browser default is only `complete` if it is intentionally acceptable.
- A state is not `n/a` merely because it is hard to build.
- Loading must prevent duplicate submission.
- Focus must be visible and return correctly from overlays.
- Empty states need a next action or a clear explanation.
- Destructive confirmation must name the consequence.
