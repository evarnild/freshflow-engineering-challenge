from __future__ import annotations

from datetime import date

from fixtures import ITEM_1001, inv_row, make_files, ord_row, rec_row
from freshflow.ingest import load_dataset
from freshflow.query import recommendations_for, stores

D = date(2024, 3, 5)


def build(**kw):
    return load_dataset(make_files(**kw))[0]


def test_sorted_by_item_number_with_catalog_join():
    ds = build(
        items=[ITEM_1001, "1002,Apples,Fruits,True,1,2"],
        orderable=[ord_row(item="1002", tags="new"), ord_row(item="1001")],
        inventory=[],
        recs=[rec_row(item="1002"), rec_row(item="1001")],
    )
    views = recommendations_for(ds, "store_a", D)
    assert [v.item_number for v in views] == [1001, 1002]
    assert views[0].name == "Bananas"
    assert views[0].category == "Fruits"
    assert views[1].is_bio is True
    assert views[1].tags == ["new"]
    assert views[0].purchase_price == 0.89


def test_inventory_is_joined_on_the_ordering_day():
    ds = build(
        inventory=[inv_row(day="2024-03-05", qty="3"), inv_row(day="2024-03-06", qty="99")],
    )
    (v,) = recommendations_for(ds, "store_a", D)
    assert v.inventory_quantity == 3
    assert "inventory_missing" not in v.flags


def test_missing_inventory_is_null_and_flagged():
    (v,) = recommendations_for(build(inventory=[]), "store_a", D)
    assert v.inventory_quantity is None
    assert "inventory_missing" in v.flags


def test_negative_is_served_as_zero_and_keeps_source():
    (v,) = recommendations_for(build(recs=[rec_row(qty="-9")]), "store_a", D)
    assert v.recommended_quantity == 0
    assert v.source_recommended_quantity == -9
    assert "negative_quantity_clamped" in v.flags


def test_missing_catalog_entry_has_null_master_data():
    ds = build(
        orderable=[ord_row(item="1099")],
        inventory=[inv_row(item="1099")],
        recs=[rec_row(item="1099")],
    )
    (v,) = recommendations_for(ds, "store_a", D)
    assert v.name is None and v.category is None and v.is_bio is None
    assert "missing_catalog_entry" in v.flags


def test_day_without_recommendations_is_empty():
    assert recommendations_for(build(), "store_a", date(2024, 3, 10)) == []


def test_stores_lists_first_and_last_ordering_day():
    ds = build(
        orderable=[ord_row(day="2024-03-05"), ord_row(day="2024-03-07", delivery="2024-03-08")],
        recs=[rec_row(day="2024-03-05"), rec_row(day="2024-03-07", delivery="2024-03-08")],
    )
    assert stores(ds) == [
        {"store_id": "store_a", "first_day": "2024-03-05", "last_day": "2024-03-07"}
    ]
