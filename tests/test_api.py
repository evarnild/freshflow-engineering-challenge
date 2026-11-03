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


# ---- review round 1


def write_dataset(path, **kw):
    for name, text in make_files(**kw).items():
        (path / f"{name}.csv").write_text(text, encoding="utf-8")


def test_oversized_csv_field_is_422_on_post_and_leaves_service_up(client):
    files = make_files()
    files["items"] = "item_number,name\n1001," + "x" * 200_000 + "\n"
    r = upload(client, files)
    assert r.status_code == 422
    assert "items" in r.text and "not valid CSV" in r.text


def test_autoload_with_oversized_field_leaves_service_empty(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    (tmp_path / "items.csv").write_text("a,b\n1," + "x" * 200_000 + "\n", encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
    assert "autoload failed" in caplog.text


def test_autoload_survives_os_error(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    def boom(self):
        raise PermissionError("denied")

    monkeypatch.setattr("pathlib.Path.read_bytes", boom)
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
    assert "autoload failed" in caplog.text


def test_empty_data_dir_disables_even_when_default_dir_has_data(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    monkeypatch.setattr("freshflow.api.DEFAULT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATA_DIR", "")
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
    assert "autoload disabled" in caplog.text


def test_unset_data_dir_uses_the_default(tmp_path, monkeypatch):
    write_dataset(tmp_path)
    monkeypatch.setattr("freshflow.api.DEFAULT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("DATA_DIR", raising=False)
    with TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is True


def test_autoload_with_only_some_files_is_skipped_and_logged(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    (tmp_path / "inventory.csv").unlink()
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
    assert "autoload skipped" in caplog.text
    assert "inventory.csv not found" in caplog.text


def test_successful_autoload_is_logged_at_info(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is True
    assert "autoloaded dataset" in caplog.text


def test_freshflow_logger_has_a_handler_at_info():
    import logging

    create_app()
    lg = logging.getLogger("freshflow")
    assert lg.handlers and lg.level == logging.INFO


def test_non_utf8_upload_detail_says_not_valid_utf8(loaded):
    files = {k: (f"{k}.csv", v.encode(), "text/csv") for k, v in make_files().items()}
    files["inventory"] = ("inventory.csv", "caf\u00e9".encode("latin-1"), "text/csv")
    r = loaded.post("/data", files=files)
    assert r.status_code == 422
    assert "inventory" in r.text and "not valid UTF-8" in r.text


@pytest.mark.parametrize("day", ["1709596800", "2024-03-05T00:00:00", "2024-3-5", "20240305"])
def test_day_must_be_strict_iso(loaded, day):
    assert loaded.get(URL, params={"day": day}).status_code == 422


def test_upload_over_the_size_cap_is_413_and_keeps_old_data(loaded, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "50")
    r = upload(loaded, make_files())
    assert r.status_code == 413
    monkeypatch.delenv("MAX_UPLOAD_BYTES")
    assert loaded.get(URL, params={"day": "2024-03-05"}).json()["count"] == 1


# ---- round 3: zero accepted rows, upload-size setting


def test_upload_whose_items_file_cleans_to_nothing_is_422_and_keeps_old_data(loaded):
    bad = make_files()
    bad["items"] = "item_number,name,category,is_bio,purchase_price,suggested_retail_price\nx,y\n"
    r = upload(loaded, bad)
    assert r.status_code == 422
    assert "items" in r.text and "no rows accepted" in r.text and "short_row" in r.text
    body = loaded.get(URL, params={"day": "2024-03-05"}).json()
    assert body["recommendations"][0]["name"] == "Bananas"


def test_autoload_that_cleans_to_nothing_leaves_service_empty(tmp_path, monkeypatch, caplog):
    write_dataset(tmp_path)
    (tmp_path / "items.csv").write_text(
        "item_number,name,category,is_bio,purchase_price,suggested_retail_price\nx,y\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with caplog.at_level("INFO", logger="freshflow"), TestClient(create_app()) as c:
        assert c.get("/health").json()["data_loaded"] is False
    assert "no rows accepted" in caplog.text


@pytest.mark.parametrize("value", ["abc", "0", "-5", ""])
def test_invalid_max_upload_bytes_falls_back_to_default_with_a_warning(
    loaded, monkeypatch, caplog, value
):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", value)
    with caplog.at_level("WARNING", logger="freshflow"):
        assert upload(loaded, make_files()).status_code == 200
    assert "invalid MAX_UPLOAD_BYTES" in caplog.text


def test_upload_exactly_at_the_limit_is_accepted_and_one_over_is_refused(loaded, monkeypatch):
    files = make_files()
    biggest = max(len(v.encode()) for v in files.values())
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(biggest))
    assert upload(loaded, files).status_code == 200
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(biggest - 1))
    assert upload(loaded, files).status_code == 413
