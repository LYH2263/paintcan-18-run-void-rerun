import os, tempfile
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="paintcan-api-test-")
import pytest
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from app.main import app

def test_void_and_remeasure_flow():
    with TestClient(app) as c:
        rid = c.post("/api/estimate", json={"room_id": 1, "persist": True}).json()["run_id"]
        assert c.post(f"/api/history/{rid}/void").status_code == 200
        assert all(h["id"] != rid for h in c.get("/api/history").json()["items"])
        d = c.get(f"/api/history/{rid}").json()
        assert d["voided"] is True and d["result"]["liters"] == 11.6
        assert c.post(f"/api/history/{rid}/void").status_code == 409
        m = c.post(f"/api/history/{rid}/remeasure").json()
        assert m["supersedes_id"] == rid
        ids = [h["id"] for h in c.get("/api/history").json()["items"]]
        assert m["run_id"] in ids and rid not in ids
        assert c.get("/api/history/999999").status_code == 404
