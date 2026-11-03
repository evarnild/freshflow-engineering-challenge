"""HTTP layer: the only I/O in the service. Holds the current dataset and swaps it atomically."""

from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from freshflow.ingest import FILE_COLUMNS, Dataset, LoadError, LoadReport, load_dataset
from freshflow.query import recommendations_for, stores

log = logging.getLogger("freshflow")

DEFAULT_DATA_DIR = "/app/data"


class _Holder:
    """The current dataset. Built fully elsewhere, then assigned once under the lock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: tuple[Dataset, LoadReport] | None = None

    def get(self) -> tuple[Dataset, LoadReport] | None:
        return self._state  # one reference read: atomic

    def swap(self, dataset: Dataset, report: LoadReport) -> None:
        with self._lock:
            self._state = (dataset, report)


def _decode(name: str, raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise LoadError(name, "not valid UTF-8 text") from None


def _autoload(holder: _Holder) -> None:
    data_dir = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)
    if not data_dir:
        log.info("autoload disabled (DATA_DIR is empty)")
        return
    try:
        texts: dict[str, str] = {}
        for name in FILE_COLUMNS:
            path = Path(data_dir) / f"{name}.csv"
            if not path.is_file():
                log.warning("autoload skipped: %s not found", path)
                return
            texts[name] = _decode(name, path.read_bytes())
        holder.swap(*load_dataset(texts))
        log.info("autoloaded dataset from %s", data_dir)
    except LoadError as e:
        log.warning("autoload failed: %s", e)


class RecommendationOut(BaseModel):
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
    tags: list[str]
    flags: list[str]


class RecommendationsOut(BaseModel):
    store_id: str
    day: date
    count: int
    recommendations: list[RecommendationOut]


class StoreOut(BaseModel):
    store_id: str
    first_day: date
    last_day: date


def create_app() -> FastAPI:
    holder = _Holder()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        _autoload(holder)
        yield

    app = FastAPI(title="FreshFlow order recommendations", lifespan=lifespan)

    def current() -> tuple[Dataset, LoadReport]:
        state = holder.get()
        if state is None:
            raise HTTPException(503, "no data loaded")
        return state

    @app.get("/health")
    def health() -> dict[str, Any]:
        """Liveness, and whether a dataset is loaded."""
        return {"status": "ok", "data_loaded": holder.get() is not None}

    @app.post("/data")
    def load_data(
        items: Annotated[UploadFile, File()],
        orderable_items: Annotated[UploadFile, File()],
        inventory: Annotated[UploadFile, File()],
        order_recommendations: Annotated[UploadFile, File()],
    ) -> dict[str, Any]:
        """Load all four CSVs as one snapshot. Replaces the dataset only if everything loads."""
        uploads = {
            "items": items,
            "orderable_items": orderable_items,
            "inventory": inventory,
            "order_recommendations": order_recommendations,
        }
        try:
            texts = {n: _decode(n, u.file.read()) for n, u in uploads.items()}
            dataset, report = load_dataset(texts)
        except LoadError as e:
            raise HTTPException(422, f"{e.file}: {e.message}") from e
        holder.swap(dataset, report)
        return report.to_dict()

    @app.get("/data/report")
    def data_report() -> dict[str, Any]:
        """The report of the last successful load."""
        return current()[1].to_dict()

    @app.get("/stores", response_model=list[StoreOut])
    def list_stores() -> list[dict[str, str]]:
        """Loaded stores with their first and last ordering day."""
        return stores(current()[0])

    @app.get("/stores/{store_id}/recommendations", response_model=RecommendationsOut)
    def get_recommendations(store_id: str, day: date) -> dict[str, Any]:
        """Recommendations whose ordering day is `day`, sorted by item number."""
        dataset, _ = current()
        store = store_id.strip().lower()
        if store not in {s["store_id"] for s in stores(dataset)}:
            raise HTTPException(404, f"unknown store: {store}")
        views = recommendations_for(dataset, store, day)
        return {"store_id": store, "day": day, "count": len(views), "recommendations": views}

    return app


app = create_app()
