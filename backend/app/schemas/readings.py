from pydantic import BaseModel, Field


class PreviewRowIn(BaseModel):
    """抄表批次单行。字段可空，由业务层给出行级错误码而非 422。"""

    account_id: int | None = None
    period: str | None = None
    kwh: float | None = None
    peak: bool = False


class PreviewRequest(BaseModel):
    rows: list[PreviewRowIn] = Field(min_length=1, max_length=500)


class ConfirmRequest(BaseModel):
    token: str
    overwrite: bool = False
