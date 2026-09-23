import json
import pytest
from fastapi.testclient import TestClient

import app.db as db_mod
from app import seed
from app.main import app
from app.repositories.runs import AlreadyVoided
from app.services.paint_service import PaintService


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    return TestClient(app)


def _result_of(run):
    return json.loads(run["result_json"])


def test_void_hides_from_default_history_but_readable_by_id(client):
    with PaintService() as s:
        rid = s.estimate(1, True)["run_id"]
        pinned = _result_of(s.run_detail(rid))
        voided = s.void_run(rid)

    assert voided["voided"] is True
    assert voided["voided_at"]
    # 作废前钉选的升数、净面积、涂布率仍可读
    assert _result_of(voided) == pinned
    assert {"liters", "net_m2", "coverage"} <= pinned.keys()

    with PaintService() as s:
        ids_default = [r["id"] for r in s.history()]
        ids_all = [r["id"] for r in s.history(include_voided=True)]
        again = s.run_detail(rid)
    assert rid not in ids_default
    assert rid in ids_all  # include_voided 与按号读取同一口径
    assert again["voided"] is True
    assert _result_of(again) == pinned


def test_repeat_void_fails_and_changes_nothing(client):
    with PaintService() as s:
        rid = s.estimate(1, True)["run_id"]
        pinned = _result_of(s.run_detail(rid))
        count_before = len(s.history(include_voided=True))
        s.void_run(rid)
        first_voided_at = s.run_detail(rid)["voided_at"]
        with pytest.raises(AlreadyVoided):
            s.void_run(rid)
        count_after = len(s.history(include_voided=True))
        row = s.run_detail(rid)

    assert count_after == count_before  # 条数不变
    assert row["voided_at"] == first_voided_at  # 戳记不被改写
    assert _result_of(row) == pinned  # result 数值字段不变

    resp = client.post(f"/api/runs/{rid}/void")
    assert resp.status_code == 409


def test_remeasure_writes_new_valid_run_linked_to_predecessor(client):
    with PaintService() as s:
        old = s.estimate(1, True)["run_id"]
        s.void_run(old)
        new = s.estimate(1, True, supersedes_id=old)

    assert new["run_id"] != old
    assert new["supersedes_id"] == old
    with PaintService() as s:
        new_row = s.run_detail(new["run_id"])
        ids = [r["id"] for r in s.history()]
        new_pinned = _result_of(new_row)
    assert new_row["supersedes_id"] == old
    assert new_row["voided"] is False
    assert new["run_id"] in ids and old not in ids
    assert {"liters", "net_m2", "coverage"} <= new_pinned.keys()


def test_api_history_filter_and_read_share_void_flag(client):
    with PaintService() as s:
        rid = s.estimate(1, True)["run_id"]
    assert client.post(f"/api/runs/{rid}/void").status_code == 200

    assert rid not in [i["id"] for i in client.get("/api/history").json()["items"]]
    all_items = client.get("/api/history?include_voided=true").json()["items"]
    by_id = client.get(f"/api/history/{rid}")
    assert by_id.status_code == 200
    assert rid in [i["id"] for i in all_items]
    assert by_id.json()["voided"] is True
    assert client.get("/api/history/99999").status_code == 404


def test_remeasure_unknown_predecessor_is_404(client):
    resp = client.post("/api/estimate", json={"room_id": 1, "persist": True, "supersedes_id": 99999})
    assert resp.status_code == 404
