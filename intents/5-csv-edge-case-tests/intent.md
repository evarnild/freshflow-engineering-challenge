<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §5 — Prove the CSV parser's remaining edge rules with tests

**Type:** refactor
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §1 review rounds 1–3 (`intents/1-order-recommendations-service/review.md`)

## Problem

§1's mutation testing left six surviving mutants in
`src/freshflow/ingest.py`. The behaviour is believed correct, but no test fails
if any of it changes:
- a date with surrounding whitespace (`_day`, around line 191);
- a loose ISO date such as `2024-3-5` (`_ISO`, line 161);
- an unrecognised boolean in `is_bio` (`_bool`, line 220);
- blank rows inside a file;
- whitespace around header names (line 245);
- a whitespace-only extra field in orderable items.

## Outcome

- Each of the six rules has a test that fails when the rule is changed. The
  coordinator re-runs the six mutants to show this.
- No behaviour changes.

## Constraints

- Tests only. If a test reveals a real defect, stop and open a fix intent;
  don't change behaviour here.

## Type-specific questions

### Refactor
- **What is restructured:** nothing in `src/`. New tests in
  `tests/test_ingest.py`.
- **How behaviour is held constant:** every existing test stays green and
  untouched, and `src/` doesn't change.
- **Why now:** `ingest.py` is core code (`CORE_CODE`). Unproven rules there
  are the most expensive kind of gap.

## Assumptions I made

- Refactor is the closest type for a tests-only change. `check:intent` should PASS, because no test lines are removed.
