import json
import sqlite3
from datetime import datetime, timezone

class AlreadyVoided(Exception):
    """对已作废编号重复作废。"""

def _now():
    return datetime.now(timezone.utc).isoformat()

def insert(conn, kind, payload, result, room_id=None, supersedes_id=None):
    now = _now()
    cur = conn.execute(
        "INSERT INTO calc_runs(kind,room_id,input_json,result_json,created_at,supersedes_id) VALUES (?,?,?,?,?,?)",
        (kind, room_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now, supersedes_id))
    conn.commit()
    return int(cur.lastrowid)

def _row_to_dict(r):
    d = dict(r)
    d["voided"] = d.get("voided_at") is not None
    return d

def list_recent(conn, limit=50, include_voided=False):
    sql = "SELECT * FROM calc_runs"
    if not include_voided:
        sql += " WHERE voided_at IS NULL"
    sql += " ORDER BY id DESC LIMIT ?"
    return [_row_to_dict(r) for r in conn.execute(sql, (limit,)).fetchall()]

def get(conn, run_id):
    r = conn.execute("SELECT * FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    return _row_to_dict(r) if r else None

def void(conn, run_id):
    # 先按号读取：不存在或已作废都失败，且不改动任何行（含 result_json）
    row = get(conn, run_id)
    if row is None:
        return None
    if row["voided"]:
        raise AlreadyVoided(run_id)
    conn.execute("UPDATE calc_runs SET voided_at=? WHERE id=? AND voided_at IS NULL",
                 (_now(), run_id))
    conn.commit()
    return get(conn, run_id)
