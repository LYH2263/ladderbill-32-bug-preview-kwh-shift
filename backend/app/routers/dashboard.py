from fastapi import APIRouter

from app.services.billing_service import BillingService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard():
    with BillingService() as svc:
        return svc.dashboard_stats()
