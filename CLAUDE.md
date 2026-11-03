# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project overview

freshflow-engineering-challenge: a containerised Python service that loads
FreshFlow's four CSV files (items, orderable items, inventory, order
recommendations) through explicit, tested cleaning rules and serves order
recommendations per store and ordering day, with anomaly flags. It is
read-only advice: it computes and places nothing. The repository also holds
the AI-native SDLC kit (from ai-sdlc-kit, first built for heraklios).

Stack: Python 3.12 (image) / >=3.12 (local), FastAPI + uvicorn, stdlib `csv`
(no pandas: the rules need row-level control), pytest, ruff, uv for the
lockfile. `README.md` has the endpoints, the data-rule codes and the design
trade-offs.

## Commands

```
npm run verify        # THE check before a change is done: kit tests, ruff check, ruff format --check, pytest
npm run verify:py     # the Python half of verify
npm run check:intent  # does this branch's change match its intent? (intents/README.md)
npm run sdlc:scan     # the evidence behind docs/sdlc-grid.md
npm run test:kit      # node --test over scripts/*.test.mjs
uv run pytest -q      # product tests only
uv run ruff format .  # format
docker build -t freshflow . && docker run --rm -p 8000:8000 freshflow
```

Needs Node >= 22 for the kit and uv (https://docs.astral.sh/uv/) for the
service; `uv run` creates `.venv/` from `uv.lock` on first use. `verify` fails
loudly if uv is missing. Keep `verify` **one** command.

## How work flows

`sdlc.md` is the step-by-step version for the owner: intent → spec → plan →
build → review → merge, and what each type requires. If it disagrees with the
rules below or with `intents/README.md` and `REVIEW-POLICY.md`, those win.

- `plan.md` is the coordinator view (snapshot, queue, backlog, shipped).
  Each work item's detail lives in `intents/<id>-<slug>/`. Read
  `intents/README.md` for the types, the gates and branch naming
  (`feat/2-…`, `fix/2-…`).
- No code before the plan's gate is recorded in `metadata.yml`. Who may
  record a gate is set out in `intents/README.md` → "Recording a gate".
- `/intent` drafts an intent, `/review` runs `REVIEW-POLICY.md` and writes
  `review.md`, and `/grid` refreshes `docs/sdlc-grid.md`.
- The `freshflow-engineering-challenge-implementer` agent builds an approved plan, and the
  `freshflow-engineering-challenge-reviewer` agent does the adversarial passes for `/review`.
- Merges into `main` are local. An agent merges, pushes, deletes a branch
  or removes a worktree only when the owner explicitly asks for that action
  in the current conversation, never on its own initiative, and only after
  the preconditions in `REVIEW-POLICY.md` → "Merging".
- **Never `git checkout` a branch in the main checkout.** It belongs to the
  coordinator session. Implementers and reviewers work in their own
  worktrees.
- A change owes a **live check** when `REVIEW-POLICY.md` → "Live checks"
  says so. The owner runs it and records `live_checked: <date>` before the
  merge. An agent's own run is evidence, never that gate.

## Architecture

`src/freshflow/`, with a hard line between pure logic and I/O:

| Module | Role | Pure? |
| --- | --- | --- |
| `ingest.py` | parse the four CSVs, normalise → validate → dedupe → cross-file checks (spec I1–I9); returns an immutable `Dataset` and a `LoadReport` of rule counts; raises `LoadError(file, message)` | pure |
| `flags.py` | I5 clamping and the anomaly flags, thresholds as named constants | pure |
| `query.py` | assembles the store-day view (`recommendations_for`, `stores`) | pure |
| `api.py` | FastAPI app (`create_app()`), the lifespan autoload from `DATA_DIR`, upload handling, error mapping, and the holder of the current dataset | I/O |

Conventions worth knowing before editing:

- A load builds the whole new `Dataset`, then swaps it in with one assignment.
  A failed load never leaves a half-loaded state.
- Dedupe runs **after** normalisation, or `STORE_A` and `store_a` copies
  survive. Medians for flags run on cleaned, deduplicated rows, with clamped
  negatives counted as 0.
- Every rule that changes, drops or flags a row is counted in the report under
  a stable code (README lists them). A new rule needs a code and a test that
  fails if the rule is removed.
- Outliers are flagged, never changed (I10). The service does not own the
  numbers.
- Tests build CSVs from strings in `tests/fixtures.py`; no network, no model.
  `tests/test_provided_data.py` (marker `provided_data`) runs the rules on the
  real `data/` files and asserts the profiled counts.
- `data/` holds the challenge's sample CSVs (untrusted input, no personal
  data); the Docker image bakes them in for the startup autoload.

Wiring from §1:

- `CORE_CODE` in `scripts/intent-check-lib.mjs` is
  `src/freshflow/(ingest|flags|query).py`: the modules whose mistakes cost most.
- Runtime paths that owe a live check (`REVIEW-POLICY.md` → "Live checks",
  rule 1): `src/freshflow/api.py`, `Dockerfile`, `pyproject.toml`, `uv.lock`.
- Reviewed tier "by meaning": `src/freshflow/api.py` (sends output to an
  external system). No prompts, credentials or personal data exist yet.

## Conventions that already apply

- Model calls and external APIs are faked or recorded in tests, never called
  live from the suite.
- No secret, token or real user data is committed, including in fixtures
  and logs.
- No new dependency arrives without a line in the intent's `plan.md` saying
  why.
- No lint warning cap is raised and no `noqa` is added without a reason.
