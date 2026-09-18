from fastapi import APIRouter

from app.services.billing_service import BillingService

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings():
    with BillingService() as svc:
        return svc.settings_map()
