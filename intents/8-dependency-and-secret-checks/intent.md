<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §8 — Add a dependency audit and a secret scan to npm run verify

**Type:** feature
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §2 review round 2 and `docs/sdlc-grid.md` (2026-11-03)

## Problem

The repository is public, and the service has runtime dependencies (FastAPI,
uvicorn, python-multipart, pinned in `uv.lock`). Nothing checks those
dependencies for known vulnerabilities, and nothing stops a token or key from
being committed. The SDLC grid scores Test at "L1, partly" for exactly this
gap, and names it as one of the two moves for Q4 2026.

## Outcome

- `npm run verify` fails when a locked dependency has a known vulnerability
  above an agreed severity, or when a tracked file contains a likely secret.
- Neither check skips silently: without what it needs (for example the
  network), it fails loudly.
- The grid's Test row can move to full L1.

## Constraints

- New tools are new dependencies, and each needs a line in the plan saying
  why.
- `verify` stays one command, and its runtime stays reasonable.
- The checks must not need a paid service or an account.

## Type-specific questions

### Feature
- **Users:** the owner and reviewers, and anyone who clones the public repo.
- **What exists today:** nothing beyond the manual scan before the first
  push.
- **Open design questions:**
  - which tools: for example `pip-audit` against `uv.lock`, and `gitleaks`
    or a small pattern scan;
  - whether the audit may use the network inside `verify`;
  - how to handle a vulnerability with no fix yet, such as an allowlist entry
    with an expiry date.

## Assumptions I made

- A small, in-repo pattern scan is acceptable if a standalone secret scanner is too heavy to require.
