"""AC5: the rules against the real provided CSVs in data/. If the files change, this tells us."""

from __future__ import annotations

from pathlib import Path

import pytest

from freshflow.flags import INVENTORY_SUSPECT, QUANTITY_OUTLIER
from freshflow.ingest import FILE_COLUMNS, load_dataset
from freshflow.query import recommendations_for

DATA = Path(__file__).resolve().parent.parent / "data"

pytestmark = pytest.mark.provided_data


@pytest.fixture(scope="module")
def loaded():
    texts = {n: (DATA / f"{n}.csv").read_text(encoding="utf-8") for n in FILE_COLUMNS}
    return load_dataset(texts)


def test_two_stores(loaded):
    ds, _ = loaded
    assert {s for s, _ in ds.recommendations} == {"store_a", "store_b"}


def test_never_orderable_items_are_not_served(loaded):
    ds, rep = loaded
    served = {r.item_number for rs in ds.recommendations.values() for r in rs}
    assert not served & {9901, 9902, 9903}
    assert rep.files["order_recommendations"].counts["not_orderable"] == 327


def test_no_sunday_recommendations_survive(loaded):
    ds, _ = loaded
    assert all(day.weekday() != 6 for _, day in ds.recommendations)


def test_no_negative_quantity_is_served(loaded):
    ds, _ = loaded
    for store, day in ds.recommendations:
        assert all(v.recommended_quantity >= 0 for v in recommendations_for(ds, store, day))
    assert rep_flag(loaded, "negative_quantity_clamped") == 509


def rep_flag(loaded, code):
    return loaded[1].flags.get(code, 0)


def test_report_counts_the_profiled_anomalies(loaded):
    _, rep = loaded
    orderable, inventory = rep.files["orderable_items"], rep.files["inventory"]
    recs = rep.files["order_recommendations"]
    assert inventory.counts["duplicate_dropped"] == 120
    assert recs.counts["duplicate_dropped"] == 300
    assert orderable.counts["duplicate_dropped"] == 200
    assert inventory.counts["date_normalised"] == 803
    assert orderable.counts["extra_empty_field_ignored"] == 240
    assert recs.counts["item_number_normalised"] > 0
    assert not any(c for c in orderable.counts if c in ("extra_fields", "conflicting_duplicate"))
    assert "conflicting_duplicate" not in recs.counts


def test_unprofiled_drop_codes_stay_absent(loaded):
    _, rep = loaded
    allowed = {"duplicate_dropped", "not_orderable"}
    for name, fr in rep.files.items():
        dropped = {c for c in fr.counts if c in fr.examples or c == "duplicate_dropped"}
        assert dropped <= allowed, (name, dropped)


def test_catalog_gap_item_1099_is_served_and_flagged(loaded):
    ds, _ = loaded
    assert 1099 not in ds.items
    flagged = [
        v
        for (s, d) in ds.recommendations
        for v in recommendations_for(ds, s, d)
        if v.item_number == 1099
    ]
    assert flagged and all("missing_catalog_entry" in v.flags for v in flagged)
    assert all(v.name is None for v in flagged)


def test_item_1009_outliers_and_suspect_inventory_items(loaded):
    ds, rep = loaded
    assert rep.flags[QUANTITY_OUTLIER] > 0
    assert max(r.quantity for rs in ds.recommendations.values() for r in rs) >= 1939
    suspect_items = {item for _, item in ds.flag_index.suspect_inventory}
    assert {1004, 1033, 1050} <= suspect_items
    assert rep.flags[INVENTORY_SUSPECT] > 0
    assert any(
        QUANTITY_OUTLIER in v.flags
        for (s, d) in ds.recommendations
        for v in recommendations_for(ds, s, d)
        if v.item_number == 1009
    )
