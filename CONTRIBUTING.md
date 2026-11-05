# Contributing to FINISHLINE

## Before you start

- Open an issue for a new audit rule or a behaviour change. Describe the user consequence, not only the code pattern.
- Small documentation and false-positive fixes can go straight to a pull request.
- Never include real credentials, customer data, private paths, or screenshots of unreleased products.

## Development setup

Requires Python 3.11+ and no third-party packages.

```bash
git clone https://github.com/Shataraimut/finishline.git
cd finishline
python3 -m unittest discover -s tests -v
python3 scripts/validate.py --audit /tmp/fixture-audit.json --strict
```

Generate the fixture audit first:

```bash
python3 scripts/audit.py tests/fixtures/defective-ui --out /tmp/fixture-audit.json
python3 scripts/validate.py --audit /tmp/fixture-audit.json --strict
```

## Adding or changing a check

1. Add the check ID to `CHECK_REGISTRY` in `scripts/lib/rules.py`.
2. Implement the rule with:
   - a concrete user consequence in `why`;
   - a repair that names the intended state or system, not just "fix it";
   - a file and line location that points at the actual evidence;
   - the right confidence: `verified` for source facts, `inferred` for heuristics.
3. Add a focused test in `tests/test_engine.py`. Use a minimal temporary project, not a screenshot of a large app.
4. Add the check to the README category table if the count changes.
5. Run the full suite and the package gate.
6. If the check changes an example's result, fix the example or record why the finding is a false positive. Do not delete the check to make the examples green.

## Adding a reference or template

- Keep references focused and operational. Avoid motivational filler.
- Use real examples, not invented product claims.
- Add the file to `scripts/validate.py` and to the routing table in `SKILL.md`.
- Verify every relative Markdown link.

## Code style

- Python 3.11+, standard library only for runtime code.
- Type hints where they clarify public functions.
- No print debugging in library code.
- Keep the scanner conservative and the audit contract stable.
- JSON output must validate against `schemas/audit.schema.json`.
- Use semantic HTML, native controls, visible focus, and real loading/error/empty states in UI contributions.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Add a regression test for every engine bug. A rule that only works on one fixture is not finished.

## Honesty requirements

- Do not claim WCAG certification, visual verification, or interaction coverage that was not performed.
- Do not fabricate screenshots, audit results, metrics, or testimonials.
- Label fixture and sample data clearly.
- If a finding is a false positive, fix the rule or record an exception with evidence. Do not silently suppress it.

## Pull requests

Include:

- what changed and why;
- the user-facing consequence;
- tests run and their result;
- any new limitations or unverified states;
- screenshots only when they are real and relevant, with the capture method stated.

Keep commits focused. Do not commit generated screenshots or audit JSON unless they are intended evidence for the repository.

## Conduct

Be direct, specific, and respectful. Critique the interface and the evidence, not the person. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
