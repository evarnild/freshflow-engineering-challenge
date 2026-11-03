"""Assemble a store-day view from a Dataset (pure)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from freshflow.flags import clamp_quantity, row_flags
from freshflow.ingest import Dataset


@dataclass(frozen=True)
class RecommendationView:
    item_number: int
    name: str | None
    category: str | None
    is_bio: bool | None
    delivery_day: date
    recommended_quantity: float
    source_recommended_quantity: float
    inventory_quantity: float | None
    purchase_price: float | None
    suggested_retail_price: float | None
    profit_margin: float | None
    tags: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def recommendations_for(dataset: Dataset, store_id: str, day: date) -> list[RecommendationView]:
    """Recommendations whose ordering day is `day`, sorted by item number."""
    out: list[RecommendationView] = []
    for r in dataset.recommendations.get((store_id, day), ()):
        item = dataset.items.get(r.item_number)
        orderable = dataset.orderable[(store_id, r.item_number, day)]
        inventory = dataset.inventory.get((store_id, r.item_number, day))
        served, _ = clamp_quantity(r.quantity)
        out.append(
            RecommendationView(
                item_number=r.item_number,
                name=item.name if item else None,
                category=item.category.title() if item else None,
                is_bio=item.is_bio if item else None,
                delivery_day=r.delivery_day,
                recommended_quantity=served,
                source_recommended_quantity=r.quantity,
                inventory_quantity=inventory,
                purchase_price=orderable.purchase_price,
                suggested_retail_price=orderable.suggested_retail_price,
                profit_margin=orderable.profit_margin,
                tags=list(orderable.tags),
                flags=row_flags(
                    dataset.flag_index,
                    store_id,
                    r.item_number,
                    r.quantity,
                    in_catalog=item is not None,
                    has_inventory=inventory is not None,
                ),
            )
        )
    return out


def stores(dataset: Dataset) -> list[dict[str, str]]:
    """Loaded store ids with first and last ordering day (ISO strings)."""
    days: dict[str, list[date]] = {}
    for store, day in dataset.recommendations:
        days.setdefault(store, []).append(day)
    return [
        {"store_id": s, "first_day": min(d).isoformat(), "last_day": max(d).isoformat()}
        for s, d in sorted(days.items())
    ]
