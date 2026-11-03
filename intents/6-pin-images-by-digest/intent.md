<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §6 — Pin the Docker base images by digest

**Type:** adjustment
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §1 review rounds 1–3 (`intents/1-order-recommendations-service/review.md`)

## Problem

The `Dockerfile` pins `python:3.12-slim` (line 1) and
`ghcr.io/astral-sh/uv:0.6.10` (line 3) by tag. A tag can be re-pointed, so the
same commit can build a different image on another day. §1 review round 1
noted this (finding 18).

## Outcome

- Both images are referenced as `name:tag@sha256:<digest>`, keeping the tag
  for readability.
- `docker build` and `docker run` still pass the §1 live-check steps.

## Constraints

- The `Dockerfile` is a live-check runtime path (`REVIEW-POLICY.md`, rule 1),
  so this change owes the owner's live check.
- Refreshing the digests becomes a deliberate change; a schedule for it is out
  of scope.

## Type-specific questions

### Adjustment
- **Exactly what changes:** the two image references in `Dockerfile`, plus a
  README note on how to refresh the digests.
- **Blast radius:** `Dockerfile` and `README.md`, a few lines, with no core
  code.

## Assumptions I made

- The digests are multi-arch indexes taken from the registry on the day of the change, so arm64 hosts still build.
