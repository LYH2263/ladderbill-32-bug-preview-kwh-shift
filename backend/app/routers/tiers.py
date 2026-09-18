from fastapi import APIRouter

from app.services.billing_service import BillingService

router = APIRouter(tags=["tiers"])


@router.get("/tiers")
def list_tiers():
    with BillingService() as svc:
        return {"items": svc.list_tiers()}
