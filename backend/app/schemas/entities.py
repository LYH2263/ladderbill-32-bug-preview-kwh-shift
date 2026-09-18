from pydantic import BaseModel


class AccountOut(BaseModel):
    id: int
    name: str
    meter_no: str
    note: str | None = None


class TierOut(BaseModel):
    id: int
    up_to: float | None
    price: float
    sort_order: int


class ReadingOut(BaseModel):
    id: int
    account_id: int
    kwh: float
    peak: int
    period: str | None = None
