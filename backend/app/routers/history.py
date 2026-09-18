from fastapi import APIRouter, HTTPException

from app.services.billing_service import BillingService

router = APIRouter(tags=["history"])


@router.get("/history")
def list_history(limit: int = 50):
    with BillingService() as svc:
        return {"items": svc.list_history(limit)}


@router.get("/history/{run_id}")
def get_history(run_id: int):
    with BillingService() as svc:
        row = svc.get_run(run_id)
        if not row:
            raise HTTPException(404, "run not found")
        return row
