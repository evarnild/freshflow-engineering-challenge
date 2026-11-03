<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §4 — Record the 413 upload cap and MAX_UPLOAD_BYTES as accepted behaviour

**Type:** adjustment
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §1 review rounds 1–3 (`intents/1-order-recommendations-service/review.md`)

## Problem

§1 added a per-file upload cap (`MAX_UPLOAD_BYTES`, default 50 MB) that
answers 413. Spec B3 lists only 422, so the shipped behaviour has no accepted
spec line. §1's folder is closed (a shipped intent is forward-fixed, not
rewritten), so the decision needs a home of its own. The README already
documents the cap.

## Outcome

- This intent, once accepted, is the record that 413 with `MAX_UPLOAD_BYTES`
  is intended behaviour. It also records the cap's known limit: Starlette
  spools the multipart body to disk before the handler runs, so the cap
  bounds only the in-memory read.
- The README's upload-cap paragraph links here.

## Constraints

- No code change. If the cap's limit matters, that is a separate feature
  intent (for example a request-size limit in front of the app).

## Type-specific questions

### Adjustment
- **Exactly what changes:** one line in `README.md` that links the upload-cap
  paragraph to this intent.
- **Blast radius:** `README.md` and this folder. Well within 5 files and 60
  lines, with no core code.

## Assumptions I made

- You accept the cap as it is. The round-2 review judged 413 the right status (RFC 9110).
