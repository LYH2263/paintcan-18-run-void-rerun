import json, sqlite3
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).isoformat()

def insert(conn, kind, payload, result, room_id=None, supersedes_id=None):
    cur = conn.execute("INSERT INTO calc_runs(kind,room_id,input_json,result_json,created_at,supersedes_id) VALUES (?,?,?,?,?,?)",
        (kind, room_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), _now(), supersedes_id))
    conn.commit(); return int(cur.lastrowid)

def get(conn, run_id):
    r = conn.execute("SELECT * FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    return dict(r) if r else None

def list_recent(conn, limit=50, include_voided=False):
    sql = "SELECT * FROM calc_runs"
    if not include_voided: sql += " WHERE voided = 0"
    return [dict(r) for r in conn.execute(sql + " ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

def mark_void(conn, run_id):
    cur = conn.execute("UPDATE calc_runs SET voided=1, voided_at=? WHERE id=? AND voided=0", (_now(), run_id))
    conn.commit(); return cur.rowcount > 0
