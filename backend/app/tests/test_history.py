import os, tempfile
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="paintcan-test-")
from app import seed
from app.db import connect
from app.services.paint_service import PaintService

seed.init_db()

def test_void_hides_from_default_list_but_pinned_values_survive():
    with PaintService() as s:
        run_id = s.estimate(1, persist=True)["run_id"]
        before = s.get_run(run_id)
        voided = s.void_run(run_id)
        assert voided and voided["voided"] is True
        assert all(h["id"] != run_id for h in s.history())
        row = [h for h in s.history(limit=1000, include_voided=True) if h["id"] == run_id][0]
        assert row["voided"] == 1
        after = s.get_run(run_id)
        assert after["voided"] is True and after["voided_at"]
        assert after["result"] == before["result"]
        assert after["result"]["liters"] == before["result"]["liters"]
        assert after["result"]["net_m2"] == before["result"]["net_m2"]
        assert after["result"]["coverage"] == before["result"]["coverage"]

def test_double_void_fails_and_changes_nothing():
    with PaintService() as s:
        run_id = s.estimate(1, persist=True)["run_id"]
        assert s.void_run(run_id)
        snap = s.get_run(run_id)
        n = len(s.history(limit=1000, include_voided=True))
        assert s.void_run(run_id) is False
        assert len(s.history(limit=1000, include_voided=True)) == n
        assert s.get_run(run_id) == snap

def test_void_unknown_run_returns_none():
    with PaintService() as s:
        assert s.void_run(999999) is None
        assert s.get_run(999999) is None
        assert s.remeasure(999999) is None

def test_remeasure_writes_new_valid_run_linked_to_old():
    with PaintService() as s:
        old_id = s.estimate(1, persist=True)["run_id"]
        r = s.remeasure(old_id)
        assert r["run_id"] and r["run_id"] != old_id
        assert r["supersedes_id"] == old_id
        ids = [h["id"] for h in s.history(limit=1000)]
        assert r["run_id"] in ids and old_id not in ids
        assert s.get_run(old_id)["voided"] is True
        new_run = s.get_run(r["run_id"])
        assert new_run["voided"] is False
        assert new_run["supersedes_id"] == old_id

def test_remeasure_uses_current_room_params():
    with PaintService() as s:
        old_id = s.estimate(1, persist=True)["run_id"]
        old_net = s.get_run(old_id)["result"]["net_m2"]
    c = connect()
    c.execute("UPDATE rooms SET length=6.0 WHERE id=1")
    c.commit(); c.close()
    try:
        with PaintService() as s:
            r = s.remeasure(old_id)
            fresh = s.estimate(1, persist=False)
            assert r["net_m2"] == fresh["net_m2"]
            assert r["net_m2"] != old_net
    finally:
        c = connect()
        c.execute("UPDATE rooms SET length=5.0 WHERE id=1")
        c.commit(); c.close()
