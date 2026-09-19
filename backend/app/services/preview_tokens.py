"""预览批次令牌：预览全部通过后签发，确认时校验，过期或复用拒绝。

令牌只活在进程内存里——预览全程不写库，重启后令牌自然失效。
"""

import secrets
import threading
import time

TTL_SECONDS = 600

TOKEN_INVALID = "TOKEN_INVALID"
TOKEN_EXPIRED = "TOKEN_EXPIRED"
TOKEN_USED = "TOKEN_USED"


class TokenError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


_lock = threading.Lock()
_tokens: dict[str, dict] = {}


def _purge_expired(now: float) -> None:
    for t in [t for t, b in _tokens.items() if b["expires_at"] <= now]:
        del _tokens[t]


def issue(rows: list[dict]) -> dict:
    """预览全部通过后签发令牌，rows 为规范化后的待写入行。"""
    with _lock:
        now = time.time()
        _purge_expired(now)
        token = secrets.token_urlsafe(24)
        _tokens[token] = {"rows": rows, "expires_at": now + TTL_SECONDS, "used": False}
        return {"token": token, "expires_in": TTL_SECONDS}


def take(token: str) -> list[dict]:
    """取出令牌对应批次；无效/过期/已用均抛 TokenError。不消耗令牌。"""
    with _lock:
        batch = _tokens.get(token)
        if batch is None:
            raise TokenError(TOKEN_INVALID, "批次令牌无效，请先预览")
        if batch["used"]:
            raise TokenError(TOKEN_USED, "批次令牌已使用，请重新预览")
        if batch["expires_at"] <= time.time():
            raise TokenError(TOKEN_EXPIRED, "批次令牌已过期，请重新预览")
        return batch["rows"]


def consume(token: str) -> None:
    """确认写入成功后消耗令牌，防止复用。"""
    with _lock:
        batch = _tokens.get(token)
        if batch is not None:
            batch["used"] = True


def reset() -> None:
    """清空全部令牌（测试用）。"""
    with _lock:
        _tokens.clear()
