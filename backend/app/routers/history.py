from fastapi import APIRouter, HTTPException
from app.repositories.runs import AlreadyVoided
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/history")
def history(limit: int = 50, include_voided: bool = False):
    with PaintService() as s: return {"items": s.history(limit, include_voided)}
@router.get("/history/{run_id}")
def history_one(run_id: int):
    with PaintService() as s:
        r = s.run_detail(run_id)
        if not r: raise HTTPException(404)
        return r
@router.post("/runs/{run_id}/void")
def void_run(run_id: int):
    with PaintService() as s:
        try:
            r = s.void_run(run_id)
        except AlreadyVoided:
            raise HTTPException(409, detail=f"run {run_id} already voided")
        if not r: raise HTTPException(404)
        return r
