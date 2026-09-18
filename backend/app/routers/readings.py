from fastapi import APIRouter, HTTPException

from app.schemas.readings import ConfirmRequest, PreviewRequest
from app.services.billing_service import BillingService
from app.services.preview_tokens import TokenError
from app.services.reading_batch import ConfirmFailed

router = APIRouter(tags=["readings"])


@router.get("/readings")
def list_readings():
    with BillingService() as svc:
        return {"items": svc.list_readings()}


@router.post("/readings/preview")
def preview_readings(body: PreviewRequest):
    """逐行校验并返回行号/状态/错误码与合计；全部通过时签发批次令牌。不写库。"""
    with BillingService() as svc:
        return svc.preview_readings([r.model_dump() for r in body.rows])


@router.post("/readings/confirm")
def confirm_readings(body: ConfirmRequest):
    """按预览令牌整批原子写入；任一行失败整批回滚；撞期须 overwrite。"""
    with BillingService() as svc:
        try:
            result = svc.confirm_readings(body.token, body.overwrite)
        except TokenError as e:
            raise HTTPException(status_code=409, detail={"error_code": e.code, "message": e.message})
        except ConfirmFailed as e:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "CONFIRM_FAILED",
                    "message": "批次未写入，已整批回滚",
                    "failures": e.failures,
                },
            )
        return {"ok": True, **result}
