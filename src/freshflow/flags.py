"""Anomaly flags and quantity clamping (pure). Flags annotate; they never alter data (I10)."""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol

NEGATIVE_CLAMPED = "negative_quantity_clamped"
QUANTITY_OUTLIER = "quantity_outlier"
INVENTORY_SUSPECT = "inventory_suspect"
MISSING_CATALOG_ENTRY = "missing_catalog_entry"
INVENTORY_MISSING = "inventory_missing"

# Judgement calls, chosen to catch the obvious cases in the sample data (item 1009's
# 525-1,939 against a median of about 15; items 1004/1033/1050 stocked in the thousands)
# without flagging normal variation. A value exactly at the limit is not flagged.
OUTLIER_FACTOR = 10.0
INVENTORY_SUSPECT_FACTOR = 10.0

StoreItem = tuple[str, int]


class _Rec(Protocol):
    store_id: str
    item_number: int
    quantity: float


@dataclass(frozen=True)
class FlagIndex:
    outlier_limit: Mapping[StoreItem, float]  # quantity above this is an outlier
    suspect_inventory: frozenset[StoreItem]


def clamp_quantity(quantity: float) -> tuple[float, bool]:
    """I5: an order cannot be negative. Returns (served quantity, was clamped)."""
    if quantity < 0:
        return 0, True
    return quantity, False


def build_flag_index(
    recs: Iterable[_Rec], inventory: Mapping[tuple[str, int, date], float]
) -> FlagIndex:
    """Medians are taken on cleaned rows; clamped negatives count as 0 and are ignored."""
    nonzero: dict[StoreItem, list[float]] = defaultdict(list)
    for r in recs:
        q, _ = clamp_quantity(r.quantity)
        if q > 0:
            nonzero[(r.store_id, r.item_number)].append(q)
    limits = {k: OUTLIER_FACTOR * statistics.median(v) for k, v in nonzero.items()}

    per_item: dict[StoreItem, list[float]] = defaultdict(list)
    for (store, item, _day), qty in inventory.items():
        per_item[(store, item)].append(qty)
    medians = {k: statistics.median(v) for k, v in per_item.items()}
    by_store: dict[str, list[float]] = defaultdict(list)
    for (store, _item), m in medians.items():
        by_store[store].append(m)
    store_median = {s: statistics.median(v) for s, v in by_store.items()}
    suspect = frozenset(
        k for k, m in medians.items() if m > INVENTORY_SUSPECT_FACTOR * store_median[k[0]]
    )
    return FlagIndex(limits, suspect)


def row_flags(
    index: FlagIndex,
    store_id: str,
    item_number: int,
    source_quantity: float,
    *,
    in_catalog: bool,
    has_inventory: bool,
) -> list[str]:
    out: list[str] = []
    served, clamped = clamp_quantity(source_quantity)
    key = (store_id, item_number)
    if clamped:
        out.append(NEGATIVE_CLAMPED)
    limit = index.outlier_limit.get(key)
    if limit is not None and served > limit:
        out.append(QUANTITY_OUTLIER)
    if key in index.suspect_inventory:
        out.append(INVENTORY_SUSPECT)
    if not in_catalog:
        out.append(MISSING_CATALOG_ENTRY)
    if not has_inventory:
        out.append(INVENTORY_MISSING)
    return out
