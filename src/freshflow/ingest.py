"""Parse and clean the four CSV files into an immutable Dataset (pure, no I/O).

Order of work per file: normalise -> validate -> dedupe. Cross-file checks run
last. Every rule that changes, drops or flags a row is counted in the
LoadReport under a stable code (listed in the README).
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType
from typing import Any

from freshflow import flags as flagmod

MAX_EXAMPLES = 5

FILE_COLUMNS: dict[str, tuple[str, ...]] = {
    "items": (
        "item_number",
        "name",
        "category",
        "is_bio",
        "purchase_price",
        "suggested_retail_price",
    ),
    "orderable_items": (
        "store_id",
        "item_number",
        "ordering_day",
        "delivery_day",
        "purchase_price",
        "suggested_retail_price",
        "profit_margin",
        "tags",
        "category",
    ),
    "inventory": ("store_id", "item_number", "day", "quantity"),
    "order_recommendations": (
        "store_id",
        "item_number",
        "ordering_day",
        "delivery_day",
        "recommended_quantity",
    ),
}


class LoadError(Exception):
    """A file is missing, undecodable or lacks a required column."""

    def __init__(self, file: str, message: str):
        super().__init__(f"{file}: {message}")
        self.file = file
        self.message = message


@dataclass(frozen=True)
class Item:
    item_number: int
    name: str
    category: str
    is_bio: bool
    purchase_price: float | None
    suggested_retail_price: float | None


@dataclass(frozen=True)
class Orderable:
    store_id: str
    item_number: int
    ordering_day: date
    delivery_day: date
    purchase_price: float | None
    suggested_retail_price: float | None
    profit_margin: float | None
    tags: tuple[str, ...]
    category: str


@dataclass(frozen=True)
class InventoryRow:
    store_id: str
    item_number: int
    day: date
    quantity: float


@dataclass(frozen=True)
class Recommendation:
    store_id: str
    item_number: int
    ordering_day: date
    delivery_day: date
    quantity: float  # as given in the source; may be negative (I5 clamps at serving)


@dataclass(frozen=True)
class Dataset:
    items: Mapping[int, Item]
    orderable: Mapping[tuple[str, int, date], Orderable]
    inventory: Mapping[tuple[str, int, date], float]
    recommendations: Mapping[tuple[str, date], tuple[Recommendation, ...]]
    flag_index: flagmod.FlagIndex


@dataclass
class FileReport:
    rows_read: int = 0
    rows_accepted: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    examples: dict[str, list[list[str]]] = field(default_factory=dict)

    def note(self, code: str, n: int = 1) -> None:
        self.counts[code] = self.counts.get(code, 0) + n

    def drop(self, code: str, row: Sequence[str], n: int = 1) -> None:
        self.note(code, n)
        ex = self.examples.setdefault(code, [])
        if len(ex) < MAX_EXAMPLES:
            ex.append(list(row))


@dataclass
class LoadReport:
    files: dict[str, FileReport] = field(default_factory=dict)
    flags: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": {
                name: {
                    "rows_read": r.rows_read,
                    "rows_accepted": r.rows_accepted,
                    "counts": dict(sorted(r.counts.items())),
                    "examples": r.examples,
                }
                for name, r in self.files.items()
            },
            "flags": dict(sorted(self.flags.items())),
        }


# ---------------------------------------------------------------- field parsers


class _Drop(Exception):
    def __init__(self, code: str):
        self.code = code


Notes = list[str]

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")


def _store(raw: str, notes: Notes) -> str:
    s = raw.strip().lower()
    if not s:
        raise _Drop("bad_store")
    if s != raw:
        notes.append("store_normalised")  # I1
    return s


def _item_number(raw: str, notes: Notes) -> int:
    s = raw.strip()
    try:
        n = int(s)
    except ValueError:
        try:
            f = float(s)
        except ValueError:
            raise _Drop("bad_item_number") from None
        if not math.isfinite(f) or not f.is_integer():
            raise _Drop("bad_item_number") from None
        n = int(f)
    if str(n) != raw:
        notes.append("item_number_normalised")  # I2
    return n


def _day(raw: str, notes: Notes) -> date:
    s = raw.strip()
    try:
        if _ISO.match(s):
            return datetime.strptime(s, "%Y-%m-%d").date()
        if _DMY.match(s):
            d = datetime.strptime(s, "%d/%m/%Y").date()  # I3: day-first
            notes.append("date_normalised")
            return d
    except ValueError:
        pass
    raise _Drop("bad_date")


def _number(raw: str, *, optional: bool = False) -> float | None:
    s = raw.strip()
    if not s:
        if optional:
            return None
        raise _Drop("bad_number")
    try:
        v = float(s)
    except ValueError:
        raise _Drop("bad_number") from None
    if not math.isfinite(v):
        raise _Drop("bad_number")
    return v


def _bool(raw: str) -> bool:
    s = raw.strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    raise _Drop("bad_bool")


def _text(raw: str) -> str:
    return raw.strip().lower()


# ------------------------------------------------------------------- file read


def _read(name: str, text: str | None) -> tuple[list[str], list[list[str]]]:
    if text is None:
        raise LoadError(name, "file is missing")
    rows = [r for r in csv.reader(io.StringIO(text.lstrip("﻿"), newline="")) if r]
    if not rows:
        raise LoadError(name, "file is empty")
    header = [h.strip() for h in rows[0]]
    missing = [c for c in FILE_COLUMNS[name] if c not in header]
    if missing:
        raise LoadError(name, f"missing required column(s): {', '.join(missing)}")
    return header, rows[1:]


def _process(
    name: str,
    text: str | None,
    build: Callable[[dict[str, str], Notes], Any],
    key: Callable[[Any], Any],
    report: LoadReport,
) -> list[Any]:
    """Normalise + validate every row, then dedupe on key (I4). Returns records."""
    header, body = _read(name, text)
    fr = report.files.setdefault(name, FileReport())
    fr.rows_read = len(body)
    groups: dict[Any, list[tuple[Any, list[str]]]] = defaultdict(list)
    for row in body:
        if len(row) < len(header):
            fr.drop("short_row", row)
            continue
        extras = row[len(header) :]
        if any(x.strip() for x in extras):
            fr.drop("extra_fields", row)  # I8
            continue
        notes: Notes = []
        if extras:
            notes.append("extra_empty_field_ignored")  # I8
        try:
            rec = build(dict(zip(header, row, strict=False)), notes)
        except _Drop as d:
            fr.drop(d.code, row)
            continue
        for n in notes:
            fr.note(n)
        groups[key(rec)].append((rec, row))
    out = []
    for members in groups.values():
        first = members[0][0]
        if all(m[0] == first for m in members):
            if len(members) > 1:
                fr.note("duplicate_dropped", len(members) - 1)
            out.append(first)
        else:
            for _, raw in members:
                fr.drop("conflicting_duplicate", raw)
    fr.rows_accepted = len(out)
    return out


# --------------------------------------------------------------------- builders


def _build_item(r: dict[str, str], notes: Notes) -> Item:
    return Item(
        item_number=_item_number(r["item_number"], notes),
        name=r["name"].strip(),
        category=_text(r["category"]),
        is_bio=_bool(r["is_bio"]),
        purchase_price=_number(r["purchase_price"], optional=True),
        suggested_retail_price=_number(r["suggested_retail_price"], optional=True),
    )


def _build_orderable(r: dict[str, str], notes: Notes) -> Orderable:
    tags = tuple(t for t in (_text(x) for x in r["tags"].split(",")) if t)
    return Orderable(
        store_id=_store(r["store_id"], notes),
        item_number=_item_number(r["item_number"], notes),
        ordering_day=_day(r["ordering_day"], notes),
        delivery_day=_day(r["delivery_day"], notes),
        purchase_price=_number(r["purchase_price"], optional=True),
        suggested_retail_price=_number(r["suggested_retail_price"], optional=True),
        profit_margin=_number(r["profit_margin"], optional=True),
        tags=tags,
        category=_text(r["category"]),
    )


def _build_inventory(r: dict[str, str], notes: Notes) -> InventoryRow:
    store = _store(r["store_id"], notes)
    item = _item_number(r["item_number"], notes)
    day = _day(r["day"], notes)
    qty = _number(r["quantity"])
    assert qty is not None
    if qty < 0:
        raise _Drop("negative_inventory")  # I9
    return InventoryRow(store, item, day, qty)


def _build_rec(r: dict[str, str], notes: Notes) -> Recommendation:
    store = _store(r["store_id"], notes)
    item = _item_number(r["item_number"], notes)
    ordering = _day(r["ordering_day"], notes)
    delivery = _day(r["delivery_day"], notes)
    qty = _number(r["recommended_quantity"])
    assert qty is not None
    return Recommendation(store, item, ordering, delivery, int(qty) if qty.is_integer() else qty)


# ------------------------------------------------------------------------ main


def load_dataset(files: Mapping[str, str]) -> tuple[Dataset, LoadReport]:
    """Build a Dataset from the four CSV texts. Raises LoadError on structural faults."""
    report = LoadReport()
    items = _process("items", files.get("items"), _build_item, lambda i: i.item_number, report)
    orderable = _process(
        "orderable_items",
        files.get("orderable_items"),
        _build_orderable,
        lambda o: (o.store_id, o.item_number, o.ordering_day),
        report,
    )
    inventory = _process(
        "inventory",
        files.get("inventory"),
        _build_inventory,
        lambda i: (i.store_id, i.item_number, i.day),
        report,
    )
    recs = _process(
        "order_recommendations",
        files.get("order_recommendations"),
        _build_rec,
        lambda r: (r.store_id, r.item_number, r.ordering_day),
        report,
    )

    orderable_by_key = {(o.store_id, o.item_number, o.ordering_day): o for o in orderable}
    fr = report.files["order_recommendations"]
    kept: list[Recommendation] = []
    for r in recs:  # I6: needs a matching orderable row with the same delivery day
        o = orderable_by_key.get((r.store_id, r.item_number, r.ordering_day))
        if o is None or o.delivery_day != r.delivery_day:
            fr.drop(
                "not_orderable",
                [r.store_id, str(r.item_number), str(r.ordering_day), str(r.delivery_day)],
            )
        else:
            kept.append(r)
    fr.rows_accepted = len(kept)

    inventory_by_key = {(i.store_id, i.item_number, i.day): i.quantity for i in inventory}
    items_by_no = {i.item_number: i for i in items}
    by_store_day: dict[tuple[str, date], list[Recommendation]] = defaultdict(list)
    for r in kept:
        by_store_day[(r.store_id, r.ordering_day)].append(r)

    dataset = Dataset(
        items=MappingProxyType(items_by_no),
        orderable=MappingProxyType(orderable_by_key),
        inventory=MappingProxyType(inventory_by_key),
        recommendations=MappingProxyType(
            {k: tuple(sorted(v, key=lambda r: r.item_number)) for k, v in by_store_day.items()}
        ),
        flag_index=flagmod.build_flag_index(kept, inventory_by_key),
    )

    tally: dict[str, int] = defaultdict(int)
    for r in kept:
        for f in flagmod.row_flags(
            dataset.flag_index,
            r.store_id,
            r.item_number,
            r.quantity,
            in_catalog=r.item_number in items_by_no,
            has_inventory=(r.store_id, r.item_number, r.ordering_day) in inventory_by_key,
        ):
            tally[f] += 1
    report.flags = dict(tally)
    return dataset, report
