# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Do **not** open a public issue for a security problem.

Use GitHub's private vulnerability reporting:

1. Open the repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Include the affected file or command, reproduction steps, impact, and any suggested fix.

If private reporting is unavailable, contact the maintainer through the GitHub profile linked to this repository. Do not include live credentials in any report.

You can expect an acknowledgement within seven days. Please allow time for a fix and coordinated disclosure.

## Scope

FINISHLINE is a local, offline analysis tool. Relevant security issues include:

- a crafted source tree causing command execution, path traversal, or writes outside the requested output;
- a schema or report renderer allowing script injection into generated HTML;
- secret material written into audit output, reports, logs, commits, or the workspace;
- the capture server exposing files outside its intended target directory;
- dependency or font supply-chain compromise.

## Out of scope

- Findings about a third-party site scanned by the user.
- The accuracy or completeness of static findings. That is a quality bug, not a security vulnerability; use the issue tracker.
- Denial of service from intentionally enormous repositories beyond the documented 2 MB per-file scan limit.

## Secure usage

- Treat scanned source as untrusted data. The audit does not execute project JavaScript.
- `capture.py` does load pages in Chromium. Do not capture untrusted pages with a browser profile that contains authenticated sessions.
- Reports may include source excerpts. Review them before sharing publicly.
- Only scan projects you are authorised to inspect.
- Never commit tokens, cookies, or private audit output. The repository's `validate.py` scans for common path and secret patterns, but it is not a secret scanner.
