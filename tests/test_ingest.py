from __future__ import annotations

from datetime import date

import pytest

from fixtures import (
    ITEM_1001,
    inv_row,
    make_files,
    ord_row,
    rec_row,
)
from freshflow.ingest import LoadError, load_dataset

D = date(2024, 3, 5)


def counts(report, file):
    return report.files[file].counts


def test_baseline_loads_one_row_each():
    ds, rep = load_dataset(make_files())
    assert len(ds.items) == 1
    assert len(ds.inventory) == 1
    assert len(ds.recommendations[("store_a", D)]) == 1
    assert rep.files["order_recommendations"].rows_read == 1
    assert rep.files["order_recommendations"].rows_accepted == 1


# I1
def test_i1_store_ids_are_stripped_and_lowercased():
    f = make_files(
        orderable=[ord_row(store=" STORE_A")],
        inventory=[inv_row(store="Store_A ")],
        recs=[rec_row(store="STORE_A")],
    )
    ds, rep = load_dataset(f)
    assert list(ds.recommendations) == [("store_a", D)]
    assert ("store_a", 1001, D) in ds.inventory
    assert counts(rep, "order_recommendations")["store_normalised"] == 1


def test_i1_empty_store_id_drops_row():
    ds, rep = load_dataset(make_files(inventory=[inv_row(store="  ")]))
    assert ds.inventory == {}
    assert counts(rep, "inventory")["bad_store"] == 1


# I2
def test_i2_integral_float_item_number_becomes_int():
    ds, rep = load_dataset(make_files(recs=[rec_row(item="1001.0")]))
    assert ds.recommendations[("store_a", D)][0].item_number == 1001
    assert counts(rep, "order_recommendations")["item_number_normalised"] == 1


@pytest.mark.parametrize("bad", ["abc", "1001.5", ""])
def test_i2_bad_item_number_drops_row(bad):
    ds, rep = load_dataset(make_files(recs=[rec_row(item=bad)]))
    assert ds.recommendations == {}
    assert counts(rep, "order_recommendations")["bad_item_number"] == 1
    assert rep.files["order_recommendations"].examples["bad_item_number"]


# I3
def test_i3_day_first_slash_date_is_accepted():
    ds, rep = load_dataset(make_files(inventory=[inv_row(day="05/03/2024")]))
    assert ("store_a", 1001, D) in ds.inventory
    assert counts(rep, "inventory")["date_normalised"] == 1


@pytest.mark.parametrize("bad", ["2024-13-01", "31/02/2024", "garbage", "03-05-2024"])
def test_i3_bad_date_drops_row(bad):
    ds, rep = load_dataset(make_files(inventory=[inv_row(day=bad)]))
    assert ds.inventory == {}
    assert counts(rep, "inventory")["bad_date"] == 1


# I4
def test_i4_exact_duplicates_collapse_after_normalisation():
    # differ only in case/whitespace of the store id: must still collapse
    f = make_files(inventory=[inv_row(store="store_a"), inv_row(store="STORE_A "), inv_row()])
    ds, rep = load_dataset(f)
    assert len(ds.inventory) == 1
    assert counts(rep, "inventory")["duplicate_dropped"] == 2
    assert rep.files["inventory"].rows_accepted == 1


def test_i4_conflicting_duplicates_are_all_dropped():
    f = make_files(inventory=[inv_row(qty="5"), inv_row(qty="6")])
    ds, rep = load_dataset(f)
    assert ds.inventory == {}
    assert counts(rep, "inventory")["conflicting_duplicate"] == 2


def test_i4_conflicting_recommendations_drop_all_and_nothing_is_served():
    f = make_files(recs=[rec_row(qty="5"), rec_row(qty="6")])
    ds, rep = load_dataset(f)
    assert ds.recommendations == {}
    assert counts(rep, "order_recommendations")["conflicting_duplicate"] == 2


def test_i4_duplicate_orderable_rows_collapse():
    f = make_files(orderable=[ord_row(), ord_row(store="STORE_A")])
    ds, rep = load_dataset(f)
    assert len(ds.orderable) == 1
    assert counts(rep, "orderable_items")["duplicate_dropped"] == 1


# I5 lives in flags; here the source value must survive loading
def test_i5_source_negative_quantity_is_kept_in_dataset():
    ds, _ = load_dataset(make_files(recs=[rec_row(qty="-7")]))
    assert ds.recommendations[("store_a", D)][0].quantity == -7


# I6
def test_i6_recommendation_without_orderable_row_is_dropped():
    f = make_files(recs=[rec_row(), rec_row(item="9901")])
    ds, rep = load_dataset(f)
    assert [r.item_number for r in ds.recommendations[("store_a", D)]] == [1001]
    assert counts(rep, "order_recommendations")["not_orderable"] == 1


def test_i6_recommendation_with_different_delivery_day_is_dropped():
    f = make_files(recs=[rec_row(delivery="2024-03-09")])
    ds, rep = load_dataset(f)
    assert ds.recommendations == {}
    assert counts(rep, "order_recommendations")["not_orderable"] == 1


# I7
def test_i7_item_missing_from_catalog_is_kept():
    f = make_files(
        orderable=[ord_row(item="1099")],
        inventory=[inv_row(item="1099")],
        recs=[rec_row(item="1099")],
    )
    ds, _ = load_dataset(f)
    assert 1099 not in ds.items
    assert ds.recommendations[("store_a", D)][0].item_number == 1099


# I8
def test_i8_trailing_empty_extra_field_is_ignored():
    f = make_files(orderable=[ord_row() + ","])
    ds, rep = load_dataset(f)
    assert len(ds.orderable) == 1
    assert counts(rep, "orderable_items")["extra_empty_field_ignored"] == 1


def test_i8_non_empty_extra_field_drops_row():
    f = make_files(orderable=[ord_row() + ",surprise"])
    ds, rep = load_dataset(f)
    assert ds.orderable == {}
    assert counts(rep, "orderable_items")["extra_fields"] == 1


def test_i8_missing_price_and_margin_become_none():
    f = make_files(orderable=[ord_row(price="", margin="")])
    ds, _ = load_dataset(f)
    o = ds.orderable[("store_a", 1001, D)]
    assert o.purchase_price is None
    assert o.profit_margin is None
    assert o.suggested_retail_price == 1.49


def test_i8_tags_and_categories_are_normalised():
    f = make_files(
        items=["1001,Bananas, FRUITS ,False,0.89,1.49"],
        orderable=[ord_row(tags="NEW  ", category="vegetables")],
    )
    ds, _ = load_dataset(f)
    assert ds.orderable[("store_a", 1001, D)].tags == ("new",)
    assert ds.orderable[("store_a", 1001, D)].category == "vegetables"
    assert ds.items[1001].category == "fruits"


def test_short_row_is_dropped():
    f = make_files(inventory=["store_a,1001"])
    ds, rep = load_dataset(f)
    assert ds.inventory == {}
    assert counts(rep, "inventory")["short_row"] == 1


# I9
def test_i9_fractional_inventory_is_kept():
    ds, _ = load_dataset(make_files(inventory=[inv_row(qty="16.4")]))
    assert ds.inventory[("store_a", 1001, D)] == 16.4


def test_i9_negative_inventory_drops_row():
    ds, rep = load_dataset(make_files(inventory=[inv_row(qty="-1")]))
    assert ds.inventory == {}
    assert counts(rep, "inventory")["negative_inventory"] == 1


def test_non_numeric_quantity_drops_row():
    ds, rep = load_dataset(make_files(inventory=[inv_row(qty="lots")]))
    assert ds.inventory == {}
    assert counts(rep, "inventory")["bad_number"] == 1


# I10: ingest never alters outliers
def test_i10_outlier_quantities_are_not_changed():
    ds, _ = load_dataset(make_files(recs=[rec_row(qty="1939")]))
    assert ds.recommendations[("store_a", D)][0].quantity == 1939


# errors
@pytest.mark.parametrize("name", ["items", "orderable_items", "inventory", "order_recommendations"])
def test_missing_file_raises_load_error_naming_it(name):
    f = make_files()
    del f[name]
    with pytest.raises(LoadError) as e:
        load_dataset(f)
    assert e.value.file == name


def test_missing_required_column_raises_load_error_naming_file():
    f = make_files()
    f["inventory"] = "store_id,item_number,day\nstore_a,1001,2024-03-05\n"
    with pytest.raises(LoadError) as e:
        load_dataset(f)
    assert e.value.file == "inventory"
    assert "quantity" in e.value.message


def test_empty_file_raises_load_error():
    f = make_files()
    f["items"] = ""
    with pytest.raises(LoadError) as e:
        load_dataset(f)
    assert e.value.file == "items"


def test_examples_are_capped_at_five():
    rows = [inv_row(item=f"x{i}") for i in range(9)]
    _, rep = load_dataset(make_files(inventory=rows))
    assert counts(rep, "inventory")["bad_item_number"] == 9
    assert len(rep.files["inventory"].examples["bad_item_number"]) == 5


def test_conflicting_items_are_all_dropped():
    f = make_files(items=[ITEM_1001, ITEM_1001.replace("False", "True")])
    ds, rep = load_dataset(f)
    assert ds.items == {}
    assert counts(rep, "items")["conflicting_duplicate"] == 2


def test_report_serialises_to_plain_dict():
    _, rep = load_dataset(make_files())
    d = rep.to_dict()
    assert d["files"]["items"]["rows_read"] == 1
    assert "flags" in d
