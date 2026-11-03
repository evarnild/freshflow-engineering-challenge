"""Synthetic CSV builders. Each test passes only the rows it is about."""

from __future__ import annotations

from collections.abc import Sequence

ITEMS_HEADER = "item_number,name,category,is_bio,purchase_price,suggested_retail_price"
ORDERABLE_HEADER = (
    "store_id,item_number,ordering_day,delivery_day,purchase_price,"
    "suggested_retail_price,profit_margin,tags,category"
)
INVENTORY_HEADER = "store_id,item_number,day,quantity"
RECS_HEADER = "store_id,item_number,ordering_day,delivery_day,recommended_quantity"

ITEM_1001 = "1001,Bananas,Fruits,False,0.89,1.49"
ORD_1001 = "store_a,1001,2024-03-05,2024-03-06,0.89,1.49,0.4,,Fruits"
INV_1001 = "store_a,1001,2024-03-05,12.5"
REC_1001 = "store_a,1001,2024-03-05,2024-03-06,10"


def _csv(header: str, rows: Sequence[str]) -> str:
    return "\n".join([header, *rows]) + "\n"


def make_files(
    items: Sequence[str] = (ITEM_1001,),
    orderable: Sequence[str] = (ORD_1001,),
    inventory: Sequence[str] = (INV_1001,),
    recs: Sequence[str] = (REC_1001,),
) -> dict[str, str]:
    return {
        "items": _csv(ITEMS_HEADER, items),
        "orderable_items": _csv(ORDERABLE_HEADER, orderable),
        "inventory": _csv(INVENTORY_HEADER, inventory),
        "order_recommendations": _csv(RECS_HEADER, recs),
    }


def ord_row(
    store: str = "store_a",
    item: str = "1001",
    day: str = "2024-03-05",
    delivery: str = "2024-03-06",
    price: str = "0.89",
    retail: str = "1.49",
    margin: str = "0.4",
    tags: str = "",
    category: str = "Fruits",
) -> str:
    return f"{store},{item},{day},{delivery},{price},{retail},{margin},{tags},{category}"


def rec_row(
    store: str = "store_a",
    item: str = "1001",
    day: str = "2024-03-05",
    delivery: str = "2024-03-06",
    qty: str = "10",
) -> str:
    return f"{store},{item},{day},{delivery},{qty}"


def inv_row(
    store: str = "store_a", item: str = "1001", day: str = "2024-03-05", qty: str = "12.5"
) -> str:
    return f"{store},{item},{day},{qty}"


def world(days: Sequence[str], item: str = "1001", store: str = "store_a", qtys=()):
    """Orderable + recommendation rows (one per day) for one store-item."""
    ords = [ord_row(store, item, d, d) for d in days]
    recs = [rec_row(store, item, d, d, str(q)) for d, q in zip(days, qtys, strict=True)]
    return ords, recs
