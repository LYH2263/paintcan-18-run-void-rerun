from fastapi import APIRouter, HTTPException
from app.services.paint_service import PaintService
router = APIRouter()

@router.get("/history")
def history(limit: int = 50, include_voided: bool = False):
    with PaintService() as s: return {"items": s.history(limit, include_voided)}

@router.get("/history/{run_id}")
def history_detail(run_id: int):
    with PaintService() as s:
        r = s.get_run(run_id)
        if not r: raise HTTPException(404)
        return r

@router.post("/history/{run_id}/void")
def void_run(run_id: int):
    with PaintService() as s:
        r = s.void_run(run_id)
        if r is None: raise HTTPException(404)
        if r is False: raise HTTPException(409, "run already voided")
        return r

@router.post("/history/{run_id}/remeasure")
def remeasure(run_id: int):
    with PaintService() as s:
        r = s.remeasure(run_id)
        if not r: raise HTTPException(404)
        return r
