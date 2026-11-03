# freshflow-engineering-challenge

A containerised service that loads FreshFlow's four CSV files and serves order
recommendations per store and day. It cleans the data on the way in, flags what
looks wrong, and never changes a number it cannot explain.

Built with the AI-native SDLC (`sdlc.md`, `intents/`): the intent, spec and plan
for this service are in `intents/1-order-recommendations-service/`.

## Run it

```
docker build -t freshflow .
docker run --rm -p 8000:8000 freshflow
```

The image bakes in `data/` and loads it at startup, so it answers straight
away. API docs (OpenAPI/Swagger) are at <http://localhost:8000/docs>.

```
curl localhost:8000/health
curl "localhost:8000/stores"
curl "localhost:8000/stores/store_a/recommendations?day=2024-03-05"

# reload (a full snapshot of all four files; the old data stays if any file is bad)
curl -F items=@data/items.csv -F orderable_items=@data/orderable_items.csv \
     -F inventory=@data/inventory.csv -F order_recommendations=@data/order_recommendations.csv \
     localhost:8000/data

curl localhost:8000/data/report
```

## Endpoints

| Endpoint | What |
| --- | --- |
| `POST /data` | multipart upload with the fields `items`, `orderable_items`, `inventory`, `order_recommendations`. 200 returns the load report. 422 names the file and the problem (including malformed CSV and non-UTF-8 bytes); 413 if a file exceeds the cap; the previous dataset stays |
| `GET /stores/{store_id}/recommendations?day=YYYY-MM-DD` | recommendations whose **ordering day** is `day` (strict ISO date), sorted by item number. Store id is case and whitespace insensitive. A store is "known" if it has at least one valid recommendation on any day. 404 unknown store, 200 with an empty list when the store has nothing that day, 422 bad `day`, 503 before any data is loaded |
| `GET /stores` | loaded stores with first and last ordering day |
| `GET /data/report` | the last load report |
| `GET /health` | liveness and whether data is loaded |

Each recommendation carries `item_number`, `name`, `category`, `is_bio`,
`delivery_day`, `recommended_quantity` (served, never negative),
`source_recommended_quantity` (as in the file), `inventory_quantity` (stock on
the ordering day or null), prices, `profit_margin`, `tags` and `flags`.

`DATA_DIR` (default `/app/data`) is where startup autoload looks. Set it empty
to start with no data. `MAX_UPLOAD_BYTES` (default 52428800, 50 MB) caps each
uploaded file; larger uploads get 413 and change nothing.

## Develop

Needs Node >= 22 (the SDLC kit) and [uv](https://docs.astral.sh/uv/).

```
npm run verify        # kit tests + ruff check + ruff format --check + pytest
npm run check:intent  # does this branch match its intent?
```

## What the data looked like, and what the service does about it

The provided CSVs are dirty. Each rule below is counted in the load report
under its code, with up to five example rows per drop code.

| Finding | Rule | Code(s) |
| --- | --- | --- |
| store ids in 4 case/whitespace variants each (`STORE_A`, ` store_a`) | strip + lowercase | `store_normalised` |
| item numbers like `1029.0` in recommendations | integral float becomes int; other values drop the row | `item_number_normalised`, `bad_item_number` |
| 803 inventory dates as `dd/mm/yyyy` | accepted as day-first (in 464 of them the first field is > 12, and the second never is); other formats drop | `date_normalised`, `bad_date` |
| exact duplicate rows (120 inventory, 300 recommendations, 200 orderable) | collapse to one, after normalisation | `duplicate_dropped` |
| same key, different values | drop all of them; neither can be trusted (none in the sample) | `conflicting_duplicate` |
| 240 orderable rows with a trailing empty field | ignored; a non-empty extra field drops the row | `extra_empty_field_ignored`, `extra_fields` |
| short rows, unparseable numbers or booleans, empty store | dropped | `short_row`, `bad_number`, `bad_bool`, `bad_store` |
| negative inventory | dropped (none in the sample) | `negative_inventory` |
| 515 negative recommended quantities (509 after dedupe) | served as 0, source value kept | flag `negative_quantity_clamped` |
| items 9901-9903 recommended (incl. all Sunday rows) but never orderable | recommendation dropped unless an orderable row exists for the same store, item, ordering day and delivery day | `not_orderable` |
| item 1099 orderable and stocked, absent from `items.csv` | kept; name, category, `is_bio` are null | flag `missing_catalog_entry` |
| 1,299 orderable rows with no price or margin | served as null | |
| no inventory row for the store, item and day | inventory is null | flag `inventory_missing` |
| item 1009 recommended at up to 1,939 against non-zero medians of 18 (store_a) and 9 (store_b) | flagged, not changed | flag `quantity_outlier` |
| items 1004, 1033, 1050 stocked in the thousands (store_b's item 1009 also trips the rule, 305 of the 1,523 flagged rows) | flagged, not changed | flag `inventory_suspect` |

Flags are attached to each returned row in `flags`, and their totals appear in
the report under `flags`.

## Design decisions and trade-offs

- **Flag, do not fix.** The service cannot know whether 1,939 oranges is a
  typo or a promotion, so outliers are flagged and a buyer decides. Only a
  negative order quantity, which has no reading as an order, is clamped, and
  the source value is kept beside it.
- **Thresholds are judgement calls.** An outlier is more than 10x the median of
  the store-item's non-zero recommendations; suspect inventory is a store-item
  median above 10x the store's median of item medians. Named constants in
  `src/freshflow/flags.py`; a value exactly at the limit is not flagged.
- **Recommendations without an orderable row are dropped**, since the store
  cannot order them. The alternative, serving and flagging them, would put
  unorderable items on a buyer's list.
- **Fractional inventory is kept.** The unit is pieces, but without knowing why
  values are fractional (averages? weighed goods?), rounding would invent data.
- **stdlib `csv`, not pandas.** The rules are row-level and need exact control
  over malformed rows, which pandas would coerce silently. It also keeps the
  image small.
- **In memory, atomic swap.** One writer, about 25k rows per file, so an
  immutable `Dataset` replaced in one assignment beats a database. The cost:
  data is lost on restart and rebuilt by autoload or `POST /data`.
- **Pure core, thin I/O.** `ingest.py`, `flags.py` and `query.py` do no I/O and
  carry the tests; `api.py` is the only place that touches HTTP or files.
- **Not done:** forecasting or adjusting recommendations, persistence,
  authentication, pagination, per-file partial loads, CI. A query by delivery
  day is easy to add.
