from __future__ import annotations

from datetime import date, timedelta

from freshflow.flags import (
    INVENTORY_MISSING,
    INVENTORY_SUSPECT,
    MISSING_CATALOG_ENTRY,
    NEGATIVE_CLAMPED,
    QUANTITY_OUTLIER,
    build_flag_index,
    clamp_quantity,
    row_flags,
)
from freshflow.ingest import Recommendation

D0 = date(2024, 1, 1)


def recs(item, qtys, store="store_a"):
    return [
        Recommendation(store, item, D0 + timedelta(i), D0 + timedelta(i + 1), q)
        for i, q in enumerate(qtys)
    ]


def flags_of(index, store, item, qty, in_catalog=True, has_inventory=True):
    return row_flags(index, store, item, qty, in_catalog=in_catalog, has_inventory=has_inventory)


def test_clamp_negative_to_zero():
    assert clamp_quantity(-5) == (0, True)
    assert clamp_quantity(0) == (0, False)
    assert clamp_quantity(7) == (7, False)


def test_negative_flag():
    idx = build_flag_index(recs(1, [10, -3]), {})
    assert NEGATIVE_CLAMPED in flags_of(idx, "store_a", 1, -3)
    assert NEGATIVE_CLAMPED not in flags_of(idx, "store_a", 1, 10)


def test_outlier_boundary_is_exclusive_at_ten_times_median():
    # non-zero values 10,10,10,100 -> median 10; limit 100. 100 is not flagged, 101 is.
    idx = build_flag_index(recs(1, [10, 10, 10, 100]), {})
    assert QUANTITY_OUTLIER not in flags_of(idx, "store_a", 1, 100)
    idx2 = build_flag_index(recs(1, [10, 10, 10, 101]), {})
    assert QUANTITY_OUTLIER in flags_of(idx2, "store_a", 1, 101)


def test_outlier_median_ignores_zero_and_clamped_negatives():
    # non-zero: 10, 10, 10 -> median 10. Zeros and clamped negatives would drag it to 0.
    idx = build_flag_index(recs(1, [0, 0, -50, -50, 10, 10, 10, 200]), {})
    assert QUANTITY_OUTLIER in flags_of(idx, "store_a", 1, 200)
    assert QUANTITY_OUTLIER not in flags_of(idx, "store_a", 1, 10)


def test_all_zero_item_has_no_division_error_and_no_flag():
    idx = build_flag_index(recs(1, [0, 0, -4]), {})
    assert QUANTITY_OUTLIER not in flags_of(idx, "store_a", 1, 0)


def test_outlier_is_per_store_item():
    r = recs(1, [10, 10, 10]) + recs(1, [1000, 1000, 1000], store="store_b")
    idx = build_flag_index(r, {})
    assert QUANTITY_OUTLIER not in flags_of(idx, "store_b", 1, 1000)


def _inv(item, value, store="store_a", n=3):
    return {(store, item, D0 + timedelta(i)): value for i in range(n)}


def test_inventory_suspect_when_median_over_ten_times_store_median():
    inv = {}
    for item in (1, 2, 3, 4):
        inv.update(_inv(item, 10.0))
    inv.update(_inv(5, 5000.0))
    idx = build_flag_index([], inv)
    assert INVENTORY_SUSPECT in flags_of(idx, "store_a", 5, 1)
    assert INVENTORY_SUSPECT not in flags_of(idx, "store_a", 1, 1)


def test_inventory_suspect_boundary_exactly_ten_times_is_not_flagged():
    inv = {}
    for item in (1, 2, 3):
        inv.update(_inv(item, 10.0))
    inv.update(_inv(4, 100.0))  # store median of medians = 10 -> limit 100
    idx = build_flag_index([], inv)
    assert INVENTORY_SUSPECT not in flags_of(idx, "store_a", 4, 1)


def test_inventory_suspect_is_computed_per_store():
    inv = _inv(1, 10.0) | _inv(2, 10.0) | _inv(3, 10.0)
    inv |= _inv(1, 1000.0, store="store_b") | _inv(2, 1000.0, store="store_b")
    idx = build_flag_index([], inv)
    assert INVENTORY_SUSPECT not in flags_of(idx, "store_b", 1, 1)


def test_missing_catalog_entry_flag():
    idx = build_flag_index([], {})
    assert MISSING_CATALOG_ENTRY in flags_of(idx, "store_a", 1, 1, in_catalog=False)
    assert MISSING_CATALOG_ENTRY not in flags_of(idx, "store_a", 1, 1)


def test_inventory_missing_flag():
    idx = build_flag_index([], {})
    assert INVENTORY_MISSING in flags_of(idx, "store_a", 1, 1, has_inventory=False)
    assert INVENTORY_MISSING not in flags_of(idx, "store_a", 1, 1)
