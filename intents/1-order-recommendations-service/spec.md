<!-- generated-by: freshflow-engineering-challenge/intent@0.1.0 -->
# §1 spec — Stack, skeleton and the order-recommendations service

Accepted intent: [intent.md](intent.md)

## Sources that apply

| Source | What it settles |
| --- | --- |
| `engineering-challenge.zip` → `README.md` | "Load data — accept the CSV files and ingest them"; "Retrieve recommendations — return order recommendations for a given store and day"; "Python, any web framework"; "must run with `docker build` + `docker run`"; "All quantities are in pieces" |
| `CLAUDE.md` → "Conventions that already apply" | external calls faked in tests; no secrets or real user data committed; every new dependency gets a reason in the plan |
| `intent.md` → Problem | the profiled anomalies that the rules below answer |

## Behaviour

**Service**

- **B1** The service is a FastAPI app served by uvicorn on port 8000 inside
  the container. `docker build -t freshflow .` and
  `docker run -p 8000:8000 freshflow` are enough to run it.
- **B2** At startup, if `DATA_DIR` (default `/app/data` in the image) holds
  the four CSVs, the service loads them through the same path as B3. A
  failed or absent autoload leaves the service up and empty, and logs why.
  `DATA_DIR=` (empty) disables autoload.
- **B3** `POST /data`: a multipart upload with exactly four file fields,
  `items`, `orderable_items`, `inventory` and `order_recommendations`. On
  success, the new dataset replaces the old one atomically, and the
  response (200) is the **load report** (B9). If a file is missing, has a
  missing required column, or is not decodable UTF-8 CSV, the response is
  422 naming the file and the problem, and the previous dataset stays in
  place. *(Amended 2026-11-03 at the owner's request, review round 2,
  MEDIUM 1.)* The same 422 applies when any of the four files ends up with
  zero accepted rows after cleaning. The detail names the file and includes
  that file's report counts, so one bad file cannot silently wipe the
  catalog or the recommendations. An autoload in that state leaves the
  service up and empty, as for any other load error (B2).
- **B4** `GET /stores/{store_id}/recommendations?day=YYYY-MM-DD` returns the
  recommendations whose **ordering day** is `day`, sorted by item number.
  Each row carries `item_number`, `name`, `category`, `is_bio`,
  `delivery_day`, `recommended_quantity`, `inventory_quantity` (the stock
  on the ordering day, or `null`), `purchase_price`,
  `suggested_retail_price`, `profit_margin`, `tags` and `flags` (a list of
  B8 codes). The envelope carries `store_id`, `day` and `count`.
- **B5** `store_id` in the path is normalised the same way as in the data
  (I1). An unknown store gives 404. A known store with no recommendations
  that day (e.g. a Sunday) gives 200 with an empty list. A malformed `day`
  gives 422. Any query before a dataset has been loaded gives 503 with
  "no data loaded".
- **B6** `GET /stores` lists the loaded store ids and, for each, the first
  and last ordering day. `GET /health` returns 200 and whether a dataset is
  loaded. `GET /data/report` returns the last load report.
- **B7** The OpenAPI docs at `/docs` (FastAPI's default) describe every
  endpoint.

**Data rules** (each one counted in the load report)

- **B8** Row flags, attached to returned recommendations:
  - `negative_quantity_clamped`: the source quantity was < 0. It is served
    as 0, and the source value is kept in `source_recommended_quantity`.
  - `quantity_outlier`: the quantity is more than 10× the median of that
    store-item's non-zero recommendations (item 1009's 525–1,939 against
    ≈15).
  - `inventory_suspect`: that store-item's median inventory is more than
    10× the store's median of per-item medians (items 1004, 1033, 1050).
  - `missing_catalog_entry`: the item is orderable but absent from
    `items.csv` (1099). Name, category and `is_bio` are `null`.
  - `inventory_missing`: no inventory row for that store, item and day.
- **B9** The load report lists, per file: rows read, rows accepted, and
  counts by rule code for everything normalised, dropped or flagged, with
  up to 5 example rows per drop code. Codes are stable strings, listed in
  the README.

## Interpretations

- **I1 Store ids:** strip and lowercase (`" STORE_A"` → `store_a`). The
  profiled variants are all case or whitespace variants of two stores.
- **I2 Item numbers:** an integral float (`1029.0`) becomes `1029`. A
  non-integral value or text drops the row (`bad_item_number`).
- **I3 Dates:** ISO `YYYY-MM-DD`. In addition, `dd/mm/yyyy` is accepted.
  The evidence for day-first: in 464 of the 803 slash dates the first
  field is > 12, and the second field never is. Anything else drops the
  row (`bad_date`).
- **I4 Duplicates:** after normalisation, exact duplicate rows collapse to
  one (`duplicate_dropped`). Rows with the same key but different values
  are all dropped (`conflicting_duplicate`), because neither can be
  trusted. The provided data has none after normalisation. Keys:
  inventory (store, item, day); orderable items and recommendations
  (store, item, ordering_day).
- **I5 Negative recommendations:** an order cannot be negative. Served as 0
  with a flag (B8), not dropped, because "order nothing" is the actionable
  reading and dropping it would hide that a recommendation existed.
- **I6 Recommendation validity:** a recommendation is kept only if a
  matching orderable-items row exists (same store, item and ordering day)
  with the same delivery day. Otherwise it is dropped (`not_orderable`).
  This removes 9901–9903, including all Sunday rows, and nothing else in
  the provided data.
- **I7 Missing catalog entry:** kept and flagged (B8). The item is genuinely
  orderable and stocked; only its master data is missing.
- **I8 Orderable items:** a trailing extra field that is empty is ignored.
  A non-empty extra field drops the row (`extra_fields`). Empty price or
  margin is served as `null`. Tags and categories are stripped and
  lowercased (category displayed title-case: `Fruits`, `Vegetables`), and
  the same applies to `items.csv`'s category.
- **I9 Inventory values:** fractional quantities are kept as given. The
  brief says "pieces", but the values cannot be safely rounded without
  knowing why they are fractional (e.g. an average or weighed goods).
  Negative inventory would drop the row (`negative_inventory`); there is
  none in the provided data.
- **I10 Outliers are flagged, never changed:** the service does not know
  whether 1,939 oranges is a data error or a promotion. A buyer does.

## Acceptance criteria

- **AC1** Each of I1–I10 has a unit test on a synthetic fixture that fails
  if the rule is removed (tests: `tests/test_ingest.py`).
- **AC2** Each B8 flag has a unit test (tests: `tests/test_flags.py`).
- **AC3** `POST /data` with valid files returns the report and swaps the
  dataset; a file with a missing column gives 422 and leaves the old
  dataset served (tests: `tests/test_api.py`).
- **AC4** `GET …/recommendations`: the B5 cases 200 / 200-empty / 404 / 422
  / 503 (tests: `tests/test_api.py`).
- **AC5** Loading the real provided data (one test, marked, reading
  `data/`) yields two stores, no `9901`–`9903` served, no negative
  `recommended_quantity` served, and the report counts the anomalies the
  intent lists (tests: `tests/test_provided_data.py`).
- **AC6** `docker build` and `docker run`, then `curl` on `/health`,
  `/stores/store_a/recommendations?day=2024-03-05` and a `POST /data`
  re-upload, behave as specified (live check, the owner's).
- **AC7** `npm run verify` runs the kit tests, `ruff check`,
  `ruff format --check` and `pytest`, and fails if any of them fails.

## Non-functional

- **Boundaries:** pure, tested logic in `src/freshflow/ingest.py` (parse
  and clean), `src/freshflow/flags.py` (anomaly detection) and
  `src/freshflow/query.py` (assemble a store-day view). I/O only in
  `src/freshflow/api.py` (HTTP, startup autoload, holding the current
  dataset).
- **Data:** challenge sample data, no personal data. Held in memory and
  lost on restart, rebuilt by autoload or `POST /data`. Size ~25k rows per
  file, so memory is trivial.
- **Model use:** none.
- **Autonomy:** read-only advice. The service places no orders.
- **Performance:** a full load in under 2 s and a query in under 50 ms on a
  laptop. Indexed by (store, ordering_day).

## Out of scope

- Computing or correcting recommendations, forecasting, and using
  inventory to adjust quantities.
- Persistence across restarts, authentication, multi-tenant isolation,
  pagination.
- Incremental or per-file loads. A load is always a full snapshot.
- CI and a container registry.

## Assumptions I made

- The 10× thresholds in B8 are judgement calls chosen to catch the obvious
  cases in this data without flagging normal variation. They are constants
  in `flags.py`, named and documented.
- A query by delivery day is not needed. It is easy to add as `?by=delivery`
  later.
- In-memory storage over SQLite: there is one writer, the data is small,
  and an atomic swap of an immutable object is simpler than transactions.
