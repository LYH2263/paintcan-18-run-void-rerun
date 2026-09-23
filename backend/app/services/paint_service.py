from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, rooms, runs, settings

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
    def run_detail(self, run_id):
        return runs.get(self._c, run_id)
    def void_run(self, run_id):
        return runs.void(self._c, run_id)
    def estimate(self, room_id, persist, coats=None, coverage=None, supersedes_id=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        linked = None
        if supersedes_id is not None:
            linked = runs.get(self._c, supersedes_id)
            if not linked: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        rid = runs.insert(self._c, "estimate", {"room_id": room_id, "coats": ct, "coverage": cov},
                          result, room_id, supersedes_id) if persist else None
        return {"run_id": rid, "room_id": room_id, "supersedes_id": supersedes_id, **result}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
