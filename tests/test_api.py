from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fixtures import ITEM_1001, inv_row, make_files, ord_row, rec_row
from freshflow.api import create_app

URL = "/stores/store_a/recommendations"


def upload(client, files):
    return client.post(
        "/data", files={k: (f"{k}.csv", v.encode(), "text/csv") for k, v in files.items()}
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "")  # autoload disabled
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def loaded(client):
    assert upload(client, make_files()).status_code == 200
    return client


def test_health_before_and_after_load(client):
    assert client.get("/health").json() == {"status": "ok", "data_loaded": False}
    upload(client, make_files())
    assert client.get("/health").json() == {"status": "ok", "data_loaded": True}


def test_post_data_returns_report_and_serves_new_data(client):
    r = upload(client, make_files())
    assert r.status_code == 200
    assert r.json()["files"]["order_recommendations"]["rows_accepted"] == 1
    assert client.get("/data/report").json() == r.json()
    body = client.get(URL, params={"day": "2024-03-05"}).json()
    assert body["count"] == 1 and body["store_id"] == "store_a" and body["day"] == "2024-03-05"
    row = body["recommendations"][0]
    assert row["item_number"] == 1001 and row["name"] == "Bananas"
    assert row["inventory_quantity"] == 12.5 and row["flags"] == []


def test_failed_post_keeps_previous_dataset(loaded):
    bad = make_files()
    bad["inventory"] = "store_id,item_number,day\nstore_a,1001,2024-03-05\n"
    r = upload(loaded, bad)
    assert r.status_code == 422
    assert "inventory" in r.text and "quantity" in r.text
    assert loaded.get(URL, params={"day": "2024-03-05"}).json()["count"] == 1


def test_undecodable_file_is_422_and_names_file(loaded):
    files = {k: (f"{k}.csv", v.encode(), "text/csv") for k, v in make_files().items()}
    files["items"] = ("items.csv", b"\xff\xfe\x00bad", "text/csv")
    r = loaded.post("/data", files=files)
    assert r.status_code == 422
    assert "items" in r.text


def test_missing_file_field_is_422(client):
    files = {"items": ("items.csv", b"x", "text/csv")}
    assert client.post("/data", files=files).status_code == 422


def test_query_before_load_is_503(client):
    r = client.get(URL, params={"day": "2024-03-05"})
    assert r.status_code == 503
    assert "no data loaded" in r.text
    assert client.get("/stores").status_code == 503


def test_unknown_store_is_404(loaded):
    r = loaded.get("/stores/store_z/recommendations", params={"day": "2024-03-05"})
    assert r.status_code == 404


def test_known_store_empty_day_is_200_empty(loaded):
    r = loaded.get(URL, params={"day": "2024-03-10"})
    assert r.status_code == 200
    assert r.json()["recommendations"] == [] and r.json()["count"] == 0


@pytest.mark.parametrize("day", ["nope", "2024-13-01", ""])
def test_malformed_day_is_422(loaded, day):
    assert loaded.get(URL, params={"day": day}).status_code == 422


def test_missing_day_is_422(loaded):
    assert loaded.get(URL).status_code == 422


def test_path_store_id_is_normalised(loaded):
    r = loaded.get("/stores/%20STORE_A/recommendations", params={"day": "2024-03-05"})
    assert r.status_code == 200 and r.json()["store_id"] == "store_a"


def test_stores_endpoint(loaded):
    assert loaded.get("/stores").json() == [
        {"store_id": "store_a", "first_day": "2024-03-05", "last_day": "2024-03-05"}
    ]


def test_report_before_load_is_503(client):
    assert client.get("/data/report").status_code == 503


def test_openapi_docs_describe_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/data", "/data/report", "/stores", "/health"} <= set(paths)
    assert "/stores/{store_id}/recommendations" in paths


def test_autoload_from_data_dir(tmp_path, monkeypatch):
    files = make_files(
        items=[ITEM_1001], orderable=[ord_row()], inventory=[inv_row()], recs=[rec_row()]
    )
    for name, text in files.items():
        (tmp_path / f"{name}.csv").write_text(text, encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is True


def test_failed_autoload_leaves_service_up_and_empty(tmp_path, monkeypatch):
    for name, text in make_files().items():
        (tmp_path / f"{name}.csv").write_text(text, encoding="utf-8")
    (tmp_path / "items.csv").write_text("garbage", encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False


def test_empty_data_dir_variable_disables_autoload(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "")
    with TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
