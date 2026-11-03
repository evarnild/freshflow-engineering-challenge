<!-- generated-by: freshflow-engineering-challenge/review@0.1.0 -->
# §1 review: Stack, skeleton and the order-recommendations service

verdict: escalate
tier: reviewed
reviewed-commit: 618b1d6
round: 3
sampled: no
live-check: owed

**Tier and what set it:** unchanged from round 2. The path table sets
Reviewed, and `review_tier: reviewed` agrees.

**Verdict in short:**
- **No finding needs rework.**
- **What this round covers:** the owner's decision on round-2 MEDIUM 1
  (refuse a file with zero accepted rows, spec B3 as amended), plus round-2
  LOWs 3 and 4. All three are done and their new lines are proven by
  mutants.
- **Still owed:** the owner's diff read and live check.

Scope: a small re-review of the round-3 commits 1cf89c5 and 618b1d6 (the
diff from 47d7edd). The coordinator did it inline; no reviewer agent ran.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. The change implements the amended B3, which the owner asked for |
| 2 | Type check | FAIL. Its only error is the owed live check, the owner's to clear |
| 3 | Behaviour against the spec | pass. A zero-accepted file gives 422 and keeps the old dataset (the reviewer's broken-items case is tested). Autoload stays empty. For recommendations the count is taken after I6. The provided data still loads (AC5) |
| 4 | Tests prove the behaviour | pass. 7 mutants: 6 killed and 1 equivalent (below) |
| 5 | Conventions | pass. The refusal lives in the pure `load_dataset` |
| 6 | Numbers in prose | pass. The BOM claim in Progress is now true: `ingest.py:240` holds the `﻿` escape (checked with `od`) |
| 7 | Documentation | pass. The README error list and `MAX_UPLOAD_BYTES` text are updated |
| 8 | Guardrails and hygiene | pass. ruff is clean |
| 9 | Repository-specific footguns | pass |

## Findings

### LOW (worth a look)
1. **Process: not tests-first.**
   - **What's wrong:** the implementer says it wrote the refusal code before
     its tests, so the new tests were never seen failing. The coordinator
     covered the gap with mutants: removing the refusal, `== 0 → < 0`, and
     skipping the last file are all killed.
   - **Side effect:** about 22 existing tests had to add a valid "spare"
     row, because a file holding only one bad row is now refused. They
     still assert their drop counts (`bad_item_number`, `bad_date`, …), so
     each still proves its rule.
2. **Carried over:**
   - finding 12, the stale kit text;
   - finding 16, quantities served as floats;
   - finding 18, image tags pinned instead of digests;
   - finding 19, `hatchling` missing from the dependency table;
   - the minor edge cases in finding 13;
   - the 413 status, still missing from spec B3 (the owner's call).

### Equivalent mutant
- `api.py`: `value = 0 → -1` on a parse failure. Any non-positive value
  takes the same fallback.

## Not checked
- **Docker:** this round wasn't re-run in Docker by anyone. Round 2's
  container evidence predates the change.
- **The under-2 s load:** still unmeasured on an idle machine.
- **Concurrent POST and GET under load.**
- **The owner's AC6 run.**

## Live check
- **owed:** rule 1. The steps and expected results are the same as round
  2's (below).
- **Addition:** re-upload with a header-only items file:
  ```
  head -1 data/items.csv > /tmp/empty_items.csv
  curl -F items=@/tmp/empty_items.csv -F orderable_items=@data/orderable_items.csv -F inventory=@data/inventory.csv -F order_recommendations=@data/order_recommendations.csv localhost:8000/data
  ```
  You should see 422 with `"no rows accepted after cleaning"` naming
  `items`. The store_a query afterwards should still return 51 named rows.

## Verified myself vs. taken on trust

**Coordinator:**
- `git diff 47d7edd..HEAD`: read for `src/` and `tests/test_ingest.py`.
- `npm run verify`: green (kit 60, ruff clean, "122 passed, 1 warning").
- `npm run check:intent`: FAIL, and its only error is the owed live check.
- **Mutants,** each with a byte backup and restore and `pytest -x`:
  - **Killed:**
    - the refusal → `if False`;
    - `== 0 → < 0`;
    - only the first 3 files checked;
    - `value <= 0 → < 0`;
    - the warning log removed;
    - the BOM `lstrip` removed (1 failed).
  - **Equivalent:** `value = 0 → -1`.
- `od` on the BOM line: the escape is present, not the literal.
- `git status --short`: clean afterwards.

**Taken on trust:** the implementer's report that only the listed tests
changed. Spot-checked in the diff.

# Round 2 (history)

- verdict: escalate
- tier: reviewed
- reviewed-commit: 47d7edd45391119a85ea9a77bb7a2e084b8a6083
- round: 2
- sampled: no
- live-check: owed

MEDIUM 1, LOW 3 and LOW 4 are resolved in round 3 above.

**Tier and what set it:** the path table sets Reviewed (the change touches
`REVIEW-POLICY.md`, `scripts/intent-check-lib.mjs` and
`src/freshflow/api.py`), and `review_tier: reviewed` in `metadata.yml`
agrees.

**Verdict in short:**
- **No finding needs rework.** Every round-1 HIGH and MEDIUM is resolved,
  and so are the requested LOWs: 10, 11, 13 (nan/inf), 14, 15 and 17.
- **Escalate:** you read the diff, do the live check, then merge.
- **Your decisions:** one new MEDIUM (an upload whose rows are all dropped
  still replaces the data) and one spec amendment (the 413 response).

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | findings (1). The 413 status is not in spec B3; it needs an owner amendment |
| 2 | Type check | FAIL. Its only error is the owed live check, which is the owner's to clear, not rework |
| 3 | Behaviour against the spec | findings (1, MEDIUM, an owner decision) |
| 4 | Tests prove the behaviour | findings (1, LOW). 43 mutants: 31 killed, 12 survived. Of the survivors, 3 are equivalent, 6 are round-1 edge cases left unfixed on purpose, and 3 are at the new upload cap |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1, LOW). Progress claims a BOM edit that isn't there. The README numbers all reproduce |
| 7 | Documentation | pass. Finding 12 (stale text) was skipped on purpose |
| 8 | Guardrails and hygiene | pass. ruff is clean and no dependency was added |
| 9 | Repository-specific footguns | pass. The list is still empty; the two round-1 proposals stand |

### Type check
```
type-check: FAIL (intent 1, feature)
  error: A live check is owed and not recorded. Do the steps in intents/1-order-recommendations-service/review.md → ## Live check, then set live_checked: <date> in intents/1-order-recommendations-service/metadata.yml.
  note:  26 file(s), 79196 line(s) changed outside intents/.
```

### Round-1 findings: resolution

The reviewer re-ran every round-1 surviving mutant at the same lines as
they now stand:

| # | Status | Evidence |
| --- | --- | --- |
| 1 | resolved | `ingest.py:241` wraps the error in `LoadError`, and `api.py:78` catches `OSError`. Both catch-removal mutants are killed, and a >128 KB field gives 422 |
| 2 | resolved | both `flags:53` mutants are killed |
| 3 | resolved | `flags:60` (median → max) and `flags:66` (global median) are killed |
| 4 | resolved | `ingest:385`, `:410` and `:411` are killed. AC5 asserts 25000, 606 and 0 |
| 5 | resolved | `api:43`, `:47`, `:48` and `:55` are killed |
| 6 | resolved | `1709596800`, `2024-03-05T00:00:00` and `2024-02-30` give 422 in the container. The new mutants are killed |
| 7 | resolved | `query:47`, `:48` and `:49` are killed |
| 8 | resolved | `ingest:309` and `:319` are killed |
| 9 | resolved | all 3 kit mutants are killed, each on the intended assertion |
| 10, 11 | resolved | README numbers re-measured: 509, medians 18 and 9, store_b/1009 = 305 of 1,523 |
| 13 (nan/inf, BOM) | resolved | `ingest:215` and `:239` are killed. The literal-BOM claim is wrong; see finding 4 below |
| 14 | resolved | the README states it, and it matches `api.py` |
| 15 | resolved, partly | a per-file cap with 413; see findings 2 and 3 |
| 17 | resolved | the container log shows `INFO:freshflow:autoloaded dataset from /app/data` |

**Not fixed, by choice** (listed in Progress): 12, 16, 18 and 19, and the
remaining edges in 13. The surviving mutants for those edges are
`ingest:161`, `:192`, `:226`, `:239` (blank rows), `:242` and `:266`.

### Findings

### MEDIUM
1. **`src/freshflow/api.py:158` / `load_dataset`: a structurally valid upload
   whose rows are all dropped still replaces the dataset.**
   - **Seen live:** `items.csv` with only a header and one broken row
     returned 200 with `items rows_accepted: 0` and
     `missing_catalog_entry: 25000`. Every recommendation is then served
     with a null name, category and `is_bio`.
   - This matches spec B3 as written, but one bad file silently wipes the
     catalog for every caller.
   - **Owner decision:** either refuse to swap (422) when a file accepts 0
     rows, or accept the risk in the spec. If refusing, it is a small fix:
     a fix intent, or a round-3 rework.

### LOW (worth a look)
2. **`spec.md` B3:** the 413 response and `MAX_UPLOAD_BYTES` are missing
   from the spec. 413 is the right code (RFC 9110), and it fires before the
   swap.
   - **Limit:** Starlette spools the multipart body to disk before the
     handler runs. So the cap bounds only the in-memory read, not bandwidth
     or disk.
   - **Owner decision:** amend the spec.
3. **`src/freshflow/api.py:38,152`: the edges of the upload cap are
   untested.** Two mutants survive:
   - an invalid `MAX_UPLOAD_BYTES` silently falls back to 50 MB;
   - `>` changed to `>=`.

   A negative cap makes every upload 413. Add a test for an invalid value
   and one at exactly the limit, and reject a non-positive cap.
4. **The round-1 rework entry in `plan.md`'s Progress against
   `src/freshflow/ingest.py:240`:** Progress says the BOM literal became
   `"﻿"`, but the source still holds the literal U+FEFF bytes. I
   confirmed this myself with `od`. Make the edit, or correct the claim.
5. **Carried over:** findings 12, 16, 18 and 19, and the edges in 13, from
   round 1.

### Not checked
- **The spec's full load in under 2 s:** not measurable this round. An
  unrelated transcription job (PID 21260, started 21:27) holds the CPU at
  100%. Under that load, `load_dataset` takes about 8 s both at 41b91d7 and
  at HEAD (an A/B test, 3 rounds each), so the slowdown from 2.5 s to 20 s
  in pytest is load, not a code regression. The round-1 figure, taken
  before the job started, was 1.33 s.
- **The 413 in the container:** proven only through TestClient and mutants.
- **Concurrent POST and GET under load:** not stress-tested.
- **Duplicate log lines:** not checked for the case where a deployment also
  configures the root logger.
- **The owner's run of AC6 on their own machine.**

### Live check
- **owed:** rule 1. The diff touches `src/freshflow/api.py`, `Dockerfile`,
  `pyproject.toml` and `uv.lock`.
- **steps:** run these from the repository root on the branch (the
  worktree), on an idle machine.
  1. `docker build -t freshflow .`
  2. `docker run --rm --name ff -p 8000:8000 freshflow`
  3. In a second shell:
     - `docker logs ff`
     - `curl localhost:8000/health`
     - `curl localhost:8000/stores`
     - `curl "localhost:8000/stores/store_a/recommendations?day=2024-03-05"`
     - `curl "localhost:8000/stores/STORE_B/recommendations?day=2024-03-03"`
     - `curl -i "localhost:8000/stores/store_z/recommendations?day=2024-03-05"`
     - `curl -s -o /dev/null -w "%{http_code}\n" "localhost:8000/stores/store_a/recommendations?day=1709596800"`
     - `time curl -F items=@data/items.csv -F orderable_items=@data/orderable_items.csv -F inventory=@data/inventory.csv -F order_recommendations=@data/order_recommendations.csv localhost:8000/data`
     - a bad re-upload: the same command with `-F inventory=@data/items.csv`
       in place of the inventory file
  4. Re-run the store_a query.
  5. Open <http://localhost:8000/docs>.
- **you should see:**
  - the logs show `INFO:freshflow:autoloaded dataset from /app/data`;
  - `/health` returns `{"status":"ok","data_loaded":true}`;
  - `/stores` lists `store_a` and `store_b`, both 2024-01-01 to 2024-12-31;
  - the store_a query returns `count` 51, every `recommended_quantity` ≥ 0,
    item 1001 named "Organic Bananas", and `tags: []`;
  - the STORE_B Sunday query returns 200 with `count` 0;
  - store_z returns 404;
  - the timestamp `day` prints 422;
  - the POST returns 200 in under 2 s, with flags
    `{"inventory_suspect":1523,"missing_catalog_entry":606,"negative_quantity_clamped":509,"quantity_outlier":7}`;
  - the bad re-upload returns 422 naming `inventory` and `quantity`, and the
    store_a query still returns 51 rows;
  - `/docs` lists all five endpoints.

### Verified myself vs. taken on trust

**Coordinator:**
- `npm run verify`: green (kit 60, ruff clean, pytest "109 passed, 1
  warning in 20.57s").
- `npm run check:intent`: FAIL, and its only error is the owed live check.
- `pytest --durations`: the real-data fixture setup is 7.8 s.
- `od` on `ingest.py:238-242`: the literal U+FEFF is still present, and
  there is no `﻿` escape.
- `Get-Process`: PID 21260 started at 21:27 with about 49,000 s of CPU.

**Reviewer agent:**
- It re-ran `verify` (109 passed) and `check:intent`, with the same
  results.
- It ran 43 mutants, with a backup and restore per file and the full suite
  for each. It re-ran one kit mutant by hand.
- It ran the `load_dataset` A/B timing: 41b91d7 against HEAD, 3 rounds
  each, no difference.
- It re-measured the README numbers against `data/`; all reproduced.
- It ran `docker build` and `docker run` on port 18766:
  - the strict-day probes;
  - a re-upload, which returned 200;
  - the all-dropped items upload behind the MEDIUM finding;
  - `docker logs`.

  It then stopped the container and removed the image.
- `git status --short` was clean at the end.

**Taken on trust:** nothing beyond round 1.

# Round 1 (history)

- verdict: rework
- tier: reviewed
- reviewed-commit: 41b91d7510f3190bc94b543adb4d8e1a0aa20e84
- round: 1
- sampled: no
- live-check: owed

The resolution of each finding is in the round-2 table above.

**Tier and what set it:** the path table puts this change in the Reviewed
tier, because it touches `REVIEW-POLICY.md`, `scripts/intent-check-lib.mjs`,
and `src/freshflow/api.py` (named "by meaning"). `metadata.yml` also sets
`review_tier: reviewed`. The HIGH findings would have escalated it anyway.

**Verdict in short:** rework. Two things need fixing:
- **A real bug:** a malformed CSV makes `POST /data` return 500 instead of
  422, and the same file stops the service from starting.
- **Tests that don't prove the behaviour:** several spec behaviours have no
  test that fails when they break. These are the outlier median,
  `inventory_suspect`, the load-report counts, the autoload switch, the
  UTF-8 rejection, the price fields and the `CORE_CODE` narrowing.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. The divergences are recorded in Progress |
| 2 | Type check | pass |
| 3 | Behaviour against the spec | findings (4) |
| 4 | Tests prove the behaviour | findings (7). 87 mutants: 54 killed, 33 survived, of which 4 are equivalent |
| 5 | Conventions | pass. Pure/I-O split holds, no network calls in tests |
| 6 | Numbers in prose | findings (2) |
| 7 | Documentation | findings (1) |
| 8 | Guardrails and hygiene | pass (one nit) |
| 9 | Repository-specific footguns | pass. The list is empty; two entries are proposed below |

### Type check
```
> node scripts/check-intent.mjs
type-check: PASS (intent 1, feature)
  note:  26 file(s), 78952 line(s) changed outside intents/.
```

### Findings

### HIGH

1. **`src/freshflow/ingest.py:239`, `src/freshflow/api.py:61`: `csv.Error`
   escapes `load_dataset`.**
   - **What's wrong:** a field over 131072 characters, which an unclosed
     quote early in a file also produces, has two effects:
     - `POST /data` returns 500 instead of the 422 that B3 requires;
     - autoload fails at startup instead of leaving the service up and
       empty, as B2 requires.
   - **Related gap:** `_autoload` doesn't catch `OSError` either.
   - **Needs rework:**
     - in `_read`, wrap the `csv.Error` in `LoadError(name, "not valid CSV: …")`;
     - catch `OSError` in `_autoload`;
     - add one ingest test and one autoload test.

2. **`src/freshflow/flags.py:52-55`, `tests/test_flags.py:51-55`: the outlier
   median that ignores zeros and clamped negatives is unproven.**
   - **What's wrong:** mutants `q > 0 → q >= 0` and "use the source
     quantity" survive, because the fixture's median is 5 either way.
   - **Needs rework:** use a fixture where the median changes the verdict,
     e.g. `[0,0,0,0,0,10,10,10,60]` with 10 not flagged. Fix the test
     comment too.

3. **`src/freshflow/flags.py:60,64-66`, `tests/test_flags.py:73-96`:
   `inventory_suspect` is unproven.**
   - **What's wrong:** two mutants survive:
     - the per-item `median → max`, because every fixture series is
       constant;
     - the per-store median replaced by one global median.
   - **Needs rework:**
     - add a varying series where max and median fall on opposite sides of
       the limit;
     - add a per-store case where a global median would flag a value and
       the per-store median does not.

4. **`src/freshflow/ingest.py:385,410-411`, `tests/test_provided_data.py`:
   the B9 report counts are unproven.**
   - **What's wrong:** these mutants survive:
     - deleting `rows_accepted = len(kept)` after I6;
     - forcing `in_catalog=True` and `has_inventory=True` in the flag tally.
   - **Needs rework:**
     - assert `rows_accepted == 25000` for recommendations and
       `flags["missing_catalog_entry"] == 606` in AC5;
     - add a synthetic test for the `inventory_missing` tally.

5. **`src/freshflow/api.py:43,47-48,55`, `tests/test_api.py:58,139`: API tests
   pass for the wrong reasons.**
   - **What's wrong:** these mutants survive:
     - removing the `DATA_DIR=` disable;
     - `get("DATA_DIR") or DEFAULT`;
     - removing the `is_file()` skip;
     - decoding as latin-1 instead of rejecting non-UTF-8. The bytes still
       fail as "missing columns".
   - **Needs rework:**
     - assert the log message (caplog), or prove that `DATA_DIR=` loads
       nothing even when the default directory holds valid files;
     - assert the 422 detail says "not valid UTF-8";
     - add a test for a directory holding only some of the files.

### MEDIUM

6. **`src/freshflow/api.py:148`: `day: date` is lax.**
   - **What's wrong:** `?day=1709596800` and `?day=2024-03-05T00:00:00` both
     return 200. B4/B5 require `YYYY-MM-DD` and a 422 otherwise.
   - **Needs rework:** a strict pattern, then `date.fromisoformat`, plus tests
     for both inputs.

7. **`src/freshflow/query.py:47-49`: the prices in the view are unproven.**
   - **What's wrong:** three mutants survive: taking `purchase_price` from the
     catalog, taking `suggested_retail_price` from the catalog, and
     `profit_margin=None`. The fixture's orderable prices equal the
     catalog's.
   - **Needs rework:** make the orderable prices differ from the catalog's
     and assert all three fields.

8. **`src/freshflow/ingest.py:309,319`: two I8 mutants survive.**
   - **What's wrong:** dropping the empty-tag filter (`[""]`) and dropping the
     lowercasing of the orderable `category`.
   - **Needs rework:** use input `"VEGETABLES "` and assert `tags == ()` for an
     empty field.

9. **`scripts/intent-check-lib.mjs:106`: the `CORE_CODE` narrowing is
   untested.**
   - **What's wrong:** all three mutants survive: reverting to `/^src\//`,
     dropping `flags`, and removing the anchors.
   - **Needs rework:** add a case showing that `src/freshflow/api.py` is
     **not** core, and one showing that `flags.py` is.

### LOW (worth a look)

10. **`README.md:81`, spec B8: `inventory_suspect` also fires on store_b's
    item 1009** (305 of the 1,523 rows). The README names only 1004, 1033
    and 1050.
11. **`README.md:75,80`:**
    - "515 negatives served as 0": 509 after dedupe;
    - "median of about 15" for item 1009: the measured non-zero medians are
      18 for store_a and 9 for store_b.
12. **Stale text:**
    - `intents/README.md:52-53` still calls the rules "language-neutral until
      §1";
    - `docs/sdlc-grid.md:21` says there is no product suite (`/grid`
      refreshes it).
13. **`src/freshflow/ingest.py`: edges that no test catches.**
    - **Gaps:**
      - `_day` doesn't strip whitespace (:192);
      - the ISO regex is loose (:161);
      - `nan`/`inf` are accepted as quantities and would probably 500 in
        JSON (:215);
      - `bad_bool` falls through to False (:226);
      - the BOM strip is a literal U+FEFF and untested (:239);
      - blank rows (:239);
      - the header strip (:242);
      - a whitespace-only extra field (:266).
    - **Most worth fixing:** the `nan`/`inf` case.
14. **`src/freshflow/api.py:152`: "known store" means having at least one
    valid recommendation.** It's defensible, but the README should say so.
15. **`src/freshflow/api.py:130`: unbounded upload read.** Auth is out of
    scope, but a size cap is cheap.
16. **`src/freshflow/api.py:237`: quantities are served as JSON floats
    (`17.0`) for pieces.** Recorded in Progress.
17. **`src/freshflow/api.py`: the `freshflow` logger has no handler.** The
    "autoloaded" info line never reaches the container logs.
18. **`Dockerfile:1,3`: images are pinned by tag, not digest.**
19. **Nit:** `hatchling` is missing from plan.md's dependency table.

### Equivalent mutants (not findings)
- `flags.py:52`: dropping the clamp
- `ingest.py:400`: building the index before I6
- `ingest.py:341`: the int/float coercion
- `api.py:41`: `utf-8` versus `utf-8-sig`

### Not checked
- Concurrent `POST /data` and GET under load. I reasoned about this from the
  code (a single reference swap under a lock) but did not stress it.
- Memory and latency for large uploads: there is no cap, and nothing was
  measured beyond the provided data.
- The image on another machine or architecture: it was built only on this
  Windows host with Docker 29.8.2.
- Mutants not written:
  - the README codes table against every emitted code;
  - the cap on example rows in the report;
  - the `__init__`, Dockerfile and pyproject lines.
- Whether `npm run verify` fails loudly on a machine without uv. I took this
  on trust.
- Python 3.14: uv resolved 3.12.9 locally.
- AC6 on the owner's machine. That is the live check.

### Live check
- **owed:** rule 1. The diff touches `src/freshflow/api.py`, `Dockerfile`,
  `pyproject.toml` and `uv.lock`.
- **steps:** run these from the repository root on the branch, after the
  rework lands.
  1. `docker build -t freshflow .`
  2. `docker run --rm -p 8000:8000 freshflow`
  3. In a second shell, run:
     - `curl localhost:8000/health`
     - `curl localhost:8000/stores`
     - `curl "localhost:8000/stores/store_a/recommendations?day=2024-03-05"`
     - `curl "localhost:8000/stores/STORE_B/recommendations?day=2024-03-03"`
     - `curl -i "localhost:8000/stores/store_z/recommendations?day=2024-03-05"`
     - `curl -F items=@data/items.csv -F orderable_items=@data/orderable_items.csv -F inventory=@data/inventory.csv -F order_recommendations=@data/order_recommendations.csv localhost:8000/data`
     - a bad re-upload: the same command with `-F inventory=@data/items.csv`
       in place of the inventory file
  4. Re-run the store_a query.
  5. Open <http://localhost:8000/docs>.
- **you should see:**
  - `/health` returns `{"status":"ok","data_loaded":true}`;
  - `/stores` lists `store_a` and `store_b`, both 2024-01-01 to 2024-12-31;
  - the store_a query returns `count` 51, every `recommended_quantity` ≥ 0,
    item 1001 named "Organic Bananas", and `tags: []`;
  - the STORE_B Sunday query returns 200 with `"store_id":"store_b","count":0`;
  - store_z returns 404;
  - the POST returns 200 with flags
    `{"inventory_suspect":1523,"missing_catalog_entry":606,"negative_quantity_clamped":509,"quantity_outlier":7}`;
  - the bad re-upload returns 422 naming `inventory` and `quantity`, and
    store_a still returns 51 rows;
  - `/docs` lists all five endpoints.

### Verified myself vs. taken on trust

**Coordinator:**
- `npm run verify`: green. Kit tests passed, ruff passed, 83 pytest tests
  passed with 1 warning.
- `npm run check:intent`: `PASS (intent 1, feature)`.
- I reproduced finding 1 (TestClient: a 200,000-character field makes
  `POST /data` return 500) and finding 6 (`day=1709596800` returns 200).

**Reviewer agent:**
- It re-ran `verify` and `check:intent` with the same results.
- It loaded `data/` through `load_dataset`. The load took 1.33 s and a query
  0.27 ms. All counts in plan.md, the README and AC5 matched, except those
  in findings 10–11.
- It ran edge probes for CRLF, BOM, UTF-16, oversized fields, NUL, an
  unclosed quote, a store that has only orderable rows, and lax days.
- It ran 87 mutants, with a backup and restore per file and the full suite
  for each. The survivors are listed above.
- It ran `docker build` (an image of 284 MB, which runs as uid 999 `app`)
  and `docker run` on port 18765. The endpoints returned what the
  live-check section lists. The container has no `.git`, `node_modules`, zip
  or tests. The reviewer then removed the image. This is evidence, not the
  owner's live check.
- `git status --short` was clean at the end, apart from this file.

**Taken on trust:** that `verify` fails loudly without uv; the account of
the commit split.

### Proposed footguns for pass 9
1. Parser exceptions other than `LoadError` (`csv.Error`, `OSError`)
   escaping into the HTTP or startup paths.
2. Fixtures that make mutants equivalent:
   - catalog price equal to the orderable price;
   - constant inventory series;
   - environment-dependent defaults such as `/app/data` being absent on a
     dev machine.
