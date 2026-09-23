import json
from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, rooms, runs, settings

def _parse_run(row):
    if not row: return None
    return {**row, "voided": bool(row["voided"]),
            "input": json.loads(row["input_json"]), "result": json.loads(row["result_json"])}

class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_rooms(self): return rooms.list_all(self._c)
    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50, include_voided=False):
        return runs.list_recent(self._c, limit, include_voided)
    def get_run(self, run_id):
        return _parse_run(runs.get(self._c, run_id))
    def void_run(self, run_id):
        if not runs.get(self._c, run_id): return None
        if not runs.mark_void(self._c, run_id): return False
        return self.get_run(run_id)
    def remeasure(self, run_id):
        old = runs.get(self._c, run_id)
        if not old: return None
        r = self.estimate(old["room_id"], persist=True, supersedes_id=run_id)
        if not r: return None
        runs.mark_void(self._c, run_id)
        return r
    def estimate(self, room_id, persist, coats=None, coverage=None, supersedes_id=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        rid = runs.insert(self._c, "estimate", {"room_id": room_id, "coats": ct, "coverage": cov}, result, room_id, supersedes_id) if persist else None
        return {"run_id": rid, "room_id": room_id, "supersedes_id": supersedes_id, **result}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
