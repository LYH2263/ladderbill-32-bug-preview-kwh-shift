"""抄表批次的行级校验：错误码、账期格式、确认失败异常。"""

import math
import re

ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
INVALID_PERIOD = "INVALID_PERIOD"
INVALID_KWH = "INVALID_KWH"
DUPLICATE_IN_BATCH = "DUPLICATE_IN_BATCH"
PERIOD_CONFLICT = "PERIOD_CONFLICT"

MESSAGES = {
    ACCOUNT_NOT_FOUND: "户号不存在",
    INVALID_PERIOD: "账期格式应为 YYYY-MM",
    INVALID_KWH: "电量须为不小于 0 的数字",
    DUPLICATE_IN_BATCH: "同户同账期在批次内重复",
    PERIOD_CONFLICT: "该户该账期已有有效抄表，须显式覆盖",
}

PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ConfirmFailed(Exception):
    """确认时有行校验失败，整批回滚。failures 为 [{line, error_code, message}]。"""

    def __init__(self, failures: list[dict]):
        super().__init__("batch confirm failed")
        self.failures = failures


def row_error(line: int, code: str) -> dict:
    return {"line": line, "error_code": code, "message": MESSAGES[code]}


def validate_row(raw: dict, valid_account_ids: set[int]) -> tuple[str | None, dict | None]:
    """校验单行，返回 (错误码, 规范化行)。通过时错误码为 None。"""
    account_id = raw.get("account_id")
    if not isinstance(account_id, int) or isinstance(account_id, bool) or account_id not in valid_account_ids:
        return ACCOUNT_NOT_FOUND, None
    period = raw.get("period")
    if not isinstance(period, str) or not PERIOD_RE.match(period.strip()):
        return INVALID_PERIOD, None
    kwh = raw.get("kwh")
    if not isinstance(kwh, (int, float)) or isinstance(kwh, bool) or not math.isfinite(kwh) or kwh < 0:
        return INVALID_KWH, None
    return None, {
        "account_id": account_id,
        "period": period.strip(),
        "kwh": float(kwh),
        "peak": bool(raw.get("peak", False)),
    }
