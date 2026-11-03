<!-- generated-by: freshflow-engineering-challenge/intent@0.1.0 -->
# §1 plan — Stack, skeleton and the order-recommendations service

Intent: [intent.md](intent.md) · Spec: [spec.md](spec.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A FastAPI service in `src/freshflow/`, packaged by a Dockerfile, that loads
the four CSVs through explicit and tested cleaning rules (spec I1–I10) and
serves recommendations per store and ordering day with flags (B1–B9). It
also wires the Python checks into `npm run verify` and fills in the
repository's stack-dependent sections.

## Stack and dependencies

| Dependency | Why |
| --- | --- |
| Python 3.12 (image `python:3.12-slim`) | the brief requires Python. 3.12 is the stable slim image with the widest wheel coverage. The code also runs on the local 3.14 |
| `fastapi` | typed request validation, multipart, and OpenAPI docs at `/docs` for free, which helps reviewers |
| `uvicorn` | the ASGI server FastAPI needs |
| `python-multipart` | FastAPI requires it for `UploadFile` |
| dev: `pytest` | tests |
| dev: `httpx` | FastAPI's `TestClient` needs it |
| dev: `ruff` | lint and format in one tool |
| `uv` (tool, not a runtime dep) | a lockfile (`uv.lock`) for reproducible installs locally and in the Dockerfile. It is already installed here |

CSV parsing uses the stdlib `csv` module, not pandas. The cleaning rules are
row-level and need exact control over malformed rows (extra fields, mixed
date formats), which pandas would coerce silently. It also keeps the image
small.

## Risks

- **Rules that pass tests but not the real data:** synthetic fixtures may
  miss a variant. AC5 runs the real `data/` once and asserts the profiled
  counts, so the fixtures and reality cannot drift apart unnoticed.
- **The dedupe order matters:** dedupe must run *after* normalisation, or
  `STORE_A` and `store_a` copies survive as two rows. Test with a pair that
  differs only in case.
- **Flags computed on dirty data:** outlier medians must be computed on
  cleaned, deduplicated rows. Clamped negatives count as 0, not as their
  source values.
- **Atomic swap:** a failed `POST /data` must not leave a half-loaded state.
  Build the new dataset fully, then assign it once.
- **The Docker build context drags in `node_modules`, `.git` or the zip:**
  add a `.dockerignore`.
- **`npm run verify` on a machine without uv:** verify calls `uv run`. The
  README states the prerequisite, and verify fails loudly rather than
  skipping.

## Verified against the codebase

- `package.json:11` — `"verify": "npm run test:kit"`, to be extended.
- `scripts/intent-check-lib.mjs:106` — `export const CORE_CODE = [/^src\//];`,
  to be narrowed.
- `REVIEW-POLICY.md:30` — the Reviewed tier's "by meaning until §1 names
  the paths" list.
- `REVIEW-POLICY.md:70-72` — Live checks rule 1, "§1 adds the product's
  entry points".
- `CLAUDE.md` → "Architecture" — "None yet. §1 writes this section".
- `.gitignore` — does not yet ignore `.venv/`, `__pycache__/` or
  `engineering-challenge.zip`.

## Subtasks

1. **Skeleton:** `pyproject.toml` (project `freshflow`, src layout,
   dependencies as above, ruff config, pytest config), `uv.lock`, and
   `.gitignore` additions (`.venv/`, `__pycache__/`, `.pytest_cache/`,
   `.ruff_cache/`, `engineering-challenge.zip`). Copy the four CSVs into
   `data/`.
2. **`ingest.py` (pure):** `load_dataset(files: Mapping[str, str]) ->
   tuple[Dataset, LoadReport]`. It parses each file, applies I1–I4 and
   I6–I9 in the order normalise → validate → dedupe → cross-file checks,
   and records the rule codes. A required-column or decode error raises
   `LoadError(file, message)`. The immutable `Dataset` holds the items by
   number, the orderable items, the inventory by key, and the
   recommendations indexed by `(store, ordering_day)`.
3. **`flags.py` (pure):** I5 clamping, `quantity_outlier`,
   `inventory_suspect`, `missing_catalog_entry` and `inventory_missing`,
   with thresholds as named constants.
4. **`query.py` (pure):** `recommendations_for(dataset, store, day) ->
   list[RecommendationView]`, plus `stores(dataset)`.
5. **`api.py` (I/O):** the FastAPI app; the current dataset held in a
   module-level holder, swapped under a lock; the endpoints B3–B6; startup
   autoload B2 via lifespan; and the error mapping LoadError → 422,
   unknown store → 404, empty → 503.
6. **Docker:** a `Dockerfile` (`python:3.12-slim`; install from `uv.lock`
   with `uv sync --frozen --no-dev`; copy `src/` and `data/`; non-root
   user; `CMD uvicorn freshflow.api:app --host 0.0.0.0 --port 8000`) and a
   `.dockerignore`.
7. **Repo wiring:**
   - `package.json` → `"verify": "npm run test:kit && npm run verify:py"`,
     with `"verify:py": "uv run ruff check && uv run ruff format --check &&
     uv run pytest -q"`.
   - `CORE_CODE` → `[/^src\/freshflow\/(ingest|flags|query)\.py$/]`.
   - `REVIEW-POLICY.md`: live-check rule 1 names `src/freshflow/api.py`,
     `Dockerfile` and `pyproject.toml`/`uv.lock`; the Reviewed tier's "by
     meaning" list names `src/freshflow/api.py` (it sends output to an
     external system) and records that there are no prompts, credentials or
     personal data yet.
   - `CLAUDE.md` → "Architecture" and "Commands".
   - `README.md`: what it is, how to build, run and call it (curl
     examples), the endpoint list, the data-rule codes table, and design
     decisions and trade-offs.

## Tests

Synthetic CSV strings live in `tests/fixtures.py` (builders, not files), so
each test states the rows it is about.

- `tests/test_ingest.py`: one test per I1–I4, I6–I9, including case-only
  duplicates, a same-key conflict, `1029.0`, `abc` as an item number,
  `23/01/2024`, `2024-13-01`, a trailing empty field versus a non-empty
  extra field, a missing price, a rec without an orderable row, and a rec
  whose delivery day differs. Also a missing column → `LoadError` naming
  the file. Each test would fail if its rule line were deleted.
- `tests/test_flags.py`: one test per flag, plus the boundary at exactly
  10× (not flagged) versus just above it, medians computed after clamping,
  and a store-item with all-zero recs (no division by zero, no flag).
- `tests/test_query.py`: sort order, inventory joined on the ordering day,
  empty day.
- `tests/test_api.py` (TestClient, no network): B3 success swaps the
  dataset, B3 422 keeps the old one, B5's status codes, `GET /stores`,
  `/health` before and after a load, path store id `STORE_A` → found.
  Autoload is driven by a tmp `DATA_DIR`; an empty `DATA_DIR` disables it.
- `tests/test_provided_data.py`: AC5 against `data/`, about 1 s.

## Validation

- `npm run verify` green.
- `npm run check:intent` PASS.
- Live check (owed, rule 1: new entry point and Dockerfile). The owner runs
  `docker build -t freshflow .` and `docker run --rm -p 8000:8000
  freshflow`, then:
  - `curl localhost:8000/health` should report a dataset loaded;
  - `curl "localhost:8000/stores/store_a/recommendations?day=2024-03-05"`
    should return rows with names and no negative quantities;
  - `curl -F items=@data/items.csv -F orderable_items=@data/orderable_items.csv
    -F inventory=@data/inventory.csv -F order_recommendations=@data/order_recommendations.csv
    localhost:8000/data` should return the load report;
  - `/docs` should open in a browser.

## Assumptions I made

- uv is acceptable as the Python toolchain. The fallback is a
  `requirements.txt` with pip, at the cost of a weaker lockfile.
- One feature intent covers both the skeleton and the service, rather than
  a separate skeleton intent first. The service is small, and the skeleton
  only means something once it carries the service.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->

### 2026-11-03: subtasks 1-7 (implementer)

Commits: 982f82a skeleton, 67f851d ingest + flags, 4ad1fb7 query, then api,
AC5 test, Docker and repo wiring (see `git log`). All on
`feat/1-order-recommendations-service`.

Shipped: everything in the plan. Tests: 83 pytest (ingest, flags, query, api,
provided data) plus the kit's node tests, all green under `npm run verify`.
`docker build -t freshflow .` succeeded; `docker run` answered `/health`
(`data_loaded: true`), `/stores/store_a/recommendations?day=2024-03-05`
(51 rows, minimum quantity 0.0, names present), a `POST /data` re-upload of
the four files (200), an empty-day query for `STORE_B` (200, empty list) and
`/docs` (200), running as the non-root user `app`. This is evidence only, not
the owner's live check.

Re-measured on the real data (profiling matched, with these refinements):
- `not_orderable` drops 327 rows, all in items 9901-9903 (332 raw rows, 5 of
  them duplicates). No Sunday recommendation survives.
- After dedupe: 509 negatives clamped (515 raw), 7 `quantity_outlier` rows,
  1,523 `inventory_suspect` rows (items 1004, 1033, 1050 at least),
  606 `missing_catalog_entry` rows (item 1099), 0 `inventory_missing`.
- 464 of 803 slash dates have first field > 12, 0 have second field > 12.
- No `conflicting_duplicate` anywhere in the provided data.

Divergences from the plan:
- `scripts/intent-check-lib.test.mjs` lines 122 and 161: two kit tests used
  `src/core/...` as a stand-in for core code; with `CORE_CODE` narrowed they
  failed, so their paths now name `src/freshflow/ingest.py` and `query.py`.
- Added a `create_app()` factory (with `app = create_app()` at module level
  for uvicorn) so each test gets its own dataset holder, instead of one
  module-level holder.
- `pyproject.toml` registers a `provided_data` pytest marker; `Dockerfile`
  copies the `uv` binary from the pinned `ghcr.io/astral-sh/uv:0.6.10` image.
- `REVIEW-POLICY.md` also got a one-sentence update to the Attested-tier
  prerequisites (the product's test suite now exists).
- Served quantities are JSON floats (`17.0`) because the response model types
  them as float.
- A missing multipart field gives FastAPI's own 422 (naming the field), not
  our `LoadError` wording.

### 2026-11-03: review round 1 rework (implementer)

Commits (review.md itself was committed first, unedited, as "§1: review round 1 (rework)"):
- "findings 1, 5, 6, 13, 15, 17": `csv.Error` now becomes `LoadError("not valid
  CSV")` (422 on POST, empty-but-up on autoload); autoload also catches
  `OSError`; strict `YYYY-MM-DD` day (pattern plus `date.fromisoformat`, 422);
  per-file upload cap `MAX_UPLOAD_BYTES` (default 50 MB); the `freshflow`
  logger gets a stderr handler at INFO so the autoload line shows in container
  logs; tests for autoload switch, partial directory, UTF-8 detail, and
  nan/inf quantities (already rejected as `bad_number`, now tested) and the BOM
  (literal replaced by the `"\ufeff"` escape).
- "findings 2, 3, 4, 7, 8, 9": tests only. Outlier median fixtures that change
  the verdict, varying-series and per-store `inventory_suspect` cases, AC5
  asserts `rows_accepted == 25000` and `missing_catalog_entry == 606`, a
  synthetic flag-tally test, catalog prices that differ from orderable ones,
  `"VEGETABLES "` and empty tags, and two kit tests for `CORE_CODE` (`flags.py`
  is core, `api.py` and look-alike paths are not). Checked by hand against two
  mutants (`q >= 0`, median to max): both now fail.
- "findings 10, 11, 14": README numbers (509 after dedupe, medians 18 and 9,
  store_b 1009 in the suspect list, what a known store means), plus the new
  cap and 413 documented.

Needs a spec/plan note: the upload cap answers 413, which spec B3 (422 only)
does not list; left for the owner to fold into the spec. Skipped: 12 (stale
text in `intents/README.md` and `docs/sdlc-grid.md`, `/grid` refreshes it),
16 (float quantities), 18 (image digests), 19 (hatchling in the dependency
table). The other edge gaps in 13 (`_day` whitespace, loose ISO regex,
`bad_bool`, blank rows, header strip, whitespace-only extra field) were not
touched.
