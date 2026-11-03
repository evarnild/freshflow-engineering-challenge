<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §3 — Serve recommended quantities as whole pieces, not JSON floats

**Type:** fix
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §1 review rounds 1–3 (`intents/1-order-recommendations-service/review.md`)

## Problem

The API serves `recommended_quantity` and `source_recommended_quantity` as
JSON floats (`17.0`). The brief says "all quantities are in pieces", and every
recommended quantity in the source data is an integer. A client that types
quantities as integers, or compares them as strings, sees `17.0` where it
expects `17`. §1 review round 1 noted this (finding 16), and §1's Progress
recorded it as a deliberate divergence. The response models declare both
fields as `float` (`src/freshflow/api.py:95-96`, `src/freshflow/query.py:19-20`).

## Outcome

- `recommended_quantity` and `source_recommended_quantity` are JSON integers
  in every response, including for clamped negatives (`0`, not `0.0`).
- `inventory_quantity` stays a number as given: fractional inventory is kept
  on purpose (§1 spec I9).
- A test fails if either field is served as a float.

## Constraints

- A source value that is not integral (none in the provided data) is not
  rounded silently. It is dropped with a counted code, or flagged; the plan
  decides which.
- No change to the cleaning rules or flags beyond the type.
- `src/freshflow/api.py` is a live-check path and Reviewed by meaning, so
  this change owes a live check and a diff read.

## Type-specific questions

### Fix
- **What broke:** quantities in pieces are served as `17.0` instead of `17`.
- **Since when:** §1 (`99e87e8`), by design at the time.
- **Impact:** cosmetic for JSON clients that accept any number; a type
  mismatch for strict ones. No wrong value is served.
- **Reproduction:** `curl "localhost:8000/stores/store_a/recommendations?day=2024-03-05"`
  shows `"recommended_quantity": 18.0`.
- **The test that will fail first:** in `tests/test_api.py`, assert that
  `recommended_quantity` is an `int` in the JSON body.

## Assumptions I made

- Fractional recommended quantities do not occur. If one does, it is a data error to report, not to round.
