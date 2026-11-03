<!-- generated-by: freshflow-engineering-challenge/intent@0.1.0 -->
# §1 — Stack, skeleton and the order-recommendations service

**Type:** feature
**Originator:** me (FreshFlow's software-engineer case study, the second, engineering one)
**Source:** `engineering-challenge.zip` → `README.md` and `data/*.csv`; `plan.md` → Backlog "§1: choose the stack"

## Problem

FreshFlow tells grocery stores how much of each fresh item to order each
day. The order recommendations are already computed and exist only as CSV
files for two stores. Nothing can serve them. The brief asks for a
containerized Python service with API endpoints that:

1. **load data**: accept the CSV files and ingest them;
2. **retrieve recommendations**: return the order recommendations for a
   given store and day.

The data is not clean, and that is evidently part of the exercise.
Profiling the files as received (2026-11-03) found:

- store ids in mixed case with stray spaces (`STORE_A`, ` store_a`,
  `store_b `) in every per-store file;
- exact duplicate rows: inventory 120, recommendations 300, orderable items
  some of its 195 duplicate keys;
- 515 negative `recommended_quantity` values (down to −5);
- item numbers written as floats (`1029.0`) in recommendations;
- items `9901`–`9903` that are recommended (332 rows, 42 of them on
  Sundays, when nothing is orderable) but are neither in the catalog nor
  ever orderable;
- item `1099`, which is orderable and stocked but missing from the catalog;
- 803 inventory dates in `dd/mm/yyyy` instead of ISO;
- 240 orderable-item rows with a trailing extra empty column, 1,299 with no
  purchase price or margin, and tags and categories in mixed case with
  trailing spaces;
- implausible magnitudes: items 1004, 1033 and 1050 show inventory in the
  thousands (median per item ≈ 25 elsewhere), rising through the year, and
  item 1009 has recommendations of up to 1,939 against a typical 10–20;
- inventory in fractional "pieces" (22,407 of 25,868 rows).

A service that ingests this naively returns wrong orders (negative or
absurd quantities, phantom items) or splits one store into several.

## Outcome

- `docker build` then `docker run` gives a service. One endpoint loads the
  four CSV files. Another returns the recommendations for a given store and
  ordering day. A reviewer can run both with `curl` against the provided
  data.
- Every data-quality rule the service applies is named, tested, and visible
  to the caller. The load response reports what was normalised, dropped or
  flagged and why. Nothing is silently fixed or silently dropped.
- `npm run verify` is still the one check: the kit's tests plus the
  service's lint and tests. `CLAUDE.md` → "Architecture", `CORE_CODE` and
  the live-check and Reviewed-tier paths are filled in for this stack.

## Constraints

- Python, any web framework. It must run with plain `docker build` and
  `docker run`.
- The recommendations are given. Computing or re-forecasting them is out of
  scope. The service serves them, cleaned and annotated.
- The data contains no personal data. It is the challenge's sample data and
  may be committed so that the container works out of the box (see
  Assumptions).
- Tests use small synthetic fixtures, not the full CSVs, and call no
  external service.
- Every new dependency is named in `plan.md` with a reason.
- Submission is a link to a git repository, so the README must let a
  stranger build, run and call the service in a few minutes.

## Type-specific questions

### Feature
- **Users:** the FreshFlow reviewers of this challenge, who will build and
  call it; in the story, store staff or an ordering system asking "what do
  I order today?".
- **What exists today:** nothing, only the SDLC kit.
- **Open design questions** (for the spec):
  - Is the load endpoint a multipart upload of all four files as one
    atomic snapshot, or per-file?
  - Does the container load the bundled data at startup, so it is usable
    immediately?
  - For each anomaly class: normalise, drop, or keep with a flag? In
    particular, are negative quantities clamped to 0 or dropped, and are
    outliers flagged or left alone?
  - Storage: in-memory (rebuilt on load) or SQLite?
  - What does "day" mean in the query: the ordering day or the delivery
    day?

## Assumptions I made

- "Day" in "for a given store and day" means the **ordering day**: the
  store asks what to order today. The delivery day is returned alongside.
- The four CSVs are loaded together as one consistent snapshot.
- Committing the provided CSVs under `data/` is acceptable. They contain no
  personal data, and the reviewers already have them. The zip itself stays
  out of git.
- The anomalies listed above are deliberate test material, not noise to be
  ignored. Handling them explicitly is part of what is being assessed.
