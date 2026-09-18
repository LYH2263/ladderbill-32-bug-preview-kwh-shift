"""抄表批次：预览（行级校验/合计/不写库）+ 确认（令牌/原子写入/撞期覆盖）。"""

from app.services import preview_tokens

SEED_READINGS = 2  # seed 里两条抄表


def _preview(client, rows):
    r = client.post("/api/readings/preview", json={"rows": rows})
    assert r.status_code == 200, r.text
    return r.json()


def _confirm(client, token, overwrite=False):
    return client.post("/api/readings/confirm", json={"token": token, "overwrite": overwrite})


def _count(client):
    return len(client.get("/api/readings").json()["items"])


def test_preview_all_valid_returns_token_and_total(client):
    p = _preview(
        client,
        [
            {"account_id": 1, "period": "2026-09", "kwh": 100.5, "peak": False},
            {"account_id": 2, "period": "2026-09", "kwh": 200, "peak": True},
        ],
    )
    assert p["all_valid"] is True
    assert p["token"]
    assert p["expires_in"] > 0
    assert p["total_kwh"] == 300.5
    assert [(r["line"], r["status"], r["error_code"]) for r in p["rows"]] == [
        (1, "ok", None),
        (2, "ok", None),
    ]
    # 预览不写库
    assert _count(client) == SEED_READINGS


def test_preview_row_errors_with_codes_and_lines(client):
    p = _preview(
        client,
        [
            {"account_id": 1, "period": "2026-09", "kwh": 100},          # ok
            {"account_id": 999, "period": "2026-09", "kwh": 100},        # 户号不存在
            {"account_id": 1, "period": "2026-13", "kwh": 100},          # 账期非法
            {"account_id": 2, "period": "2026-09", "kwh": -5},           # 电量非法
            {"account_id": 1, "period": "2026-09", "kwh": 60},           # 批内重复
        ],
    )
    assert p["all_valid"] is False
    assert p["token"] is None
    assert p["total_kwh"] is None
    got = [(r["line"], r["status"], r["error_code"]) for r in p["rows"]]
    assert got == [
        (1, "ok", None),
        (2, "error", "ACCOUNT_NOT_FOUND"),
        (3, "error", "INVALID_PERIOD"),
        (4, "error", "INVALID_KWH"),
        (5, "error", "DUPLICATE_IN_BATCH"),
    ]
    assert _count(client) == SEED_READINGS


def test_preview_marks_period_conflict_but_issues_token(client):
    # 户 1 在 2026-08 已有 seed 抄表
    p = _preview(client, [{"account_id": 1, "period": "2026-08", "kwh": 130}])
    assert p["all_valid"] is True
    assert p["token"]
    assert p["conflict_count"] == 1
    assert p["rows"][0]["status"] == "conflict"
    assert p["rows"][0]["error_code"] == "PERIOD_CONFLICT"


def test_confirm_writes_batch_and_list_grows_by_passed_rows(client):
    p = _preview(
        client,
        [
            {"account_id": 1, "period": "2026-09", "kwh": 100},
            {"account_id": 2, "period": "2026-09", "kwh": 200, "peak": True},
        ],
    )
    r = _confirm(client, p["token"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"ok": True, "inserted": 2, "replaced": 0, "total": 2}
    # 列表条数与预览通过项一致
    assert _count(client) == SEED_READINGS + 2
    items = client.get("/api/readings").json()["items"]
    mine = [i for i in items if i["period"] == "2026-09"]
    assert {(i["account_id"], i["peak"]) for i in mine} == {(1, 0), (2, 1)}
    assert len(mine) == 2


def test_confirm_token_reuse_rejected(client):
    p = _preview(client, [{"account_id": 1, "period": "2026-09", "kwh": 100}])
    assert _confirm(client, p["token"]).status_code == 200
    r = _confirm(client, p["token"])
    assert r.status_code == 409
    assert r.json()["detail"]["error_code"] == "TOKEN_USED"
    assert _count(client) == SEED_READINGS + 1


def test_confirm_unknown_token_rejected(client):
    r = _confirm(client, "no-such-token")
    assert r.status_code == 409
    assert r.json()["detail"]["error_code"] == "TOKEN_INVALID"


def test_confirm_expired_token_rejected(client, monkeypatch):
    monkeypatch.setattr(preview_tokens, "TTL_SECONDS", -1)  # 签发即过期
    p = _preview(client, [{"account_id": 1, "period": "2026-09", "kwh": 100}])
    r = _confirm(client, p["token"])
    assert r.status_code == 409
    assert r.json()["detail"]["error_code"] == "TOKEN_EXPIRED"
    assert _count(client) == SEED_READINGS


def test_confirm_conflict_without_overwrite_rolls_back_then_overwrite_retries(client):
    p = _preview(
        client,
        [
            {"account_id": 1, "period": "2026-09", "kwh": 100},   # 新行
            {"account_id": 1, "period": "2026-08", "kwh": 999},   # 撞 seed
        ],
    )
    assert p["all_valid"] is True
    r = _confirm(client, p["token"], overwrite=False)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["error_code"] == "CONFIRM_FAILED"
    assert [(f["line"], f["error_code"]) for f in detail["failures"]] == [(2, "PERIOD_CONFLICT")]
    # 整批回滚：第 1 行也没写入；令牌未消耗
    assert _count(client) == SEED_READINGS
    r2 = _confirm(client, p["token"], overwrite=True)
    assert r2.status_code == 200
    assert r2.json() == {"ok": True, "inserted": 1, "replaced": 1, "total": 2}
    assert _count(client) == SEED_READINGS + 1


def test_overwrite_replaces_in_place(client):
    p = _preview(client, [{"account_id": 1, "period": "2026-08", "kwh": 999, "peak": True}])
    r = _confirm(client, p["token"], overwrite=True)
    assert r.status_code == 200
    assert r.json()["replaced"] == 1
    assert _count(client) == SEED_READINGS  # 替换不增条数
    items = client.get("/api/readings").json()["items"]
    row = next(i for i in items if i["account_id"] == 1 and i["period"] == "2026-08")
    assert row["peak"] == 1


def test_confirm_revalidates_against_writes_after_preview(client):
    # 两个批次预览同一户同一账期；先确认的写入后，后确认的必须撞期失败
    pa = _preview(client, [{"account_id": 1, "period": "2026-09", "kwh": 100}])
    pb = _preview(client, [{"account_id": 1, "period": "2026-09", "kwh": 200}])
    assert _confirm(client, pa["token"]).status_code == 200
    r = _confirm(client, pb["token"])
    assert r.status_code == 409
    assert r.json()["detail"]["failures"][0]["error_code"] == "PERIOD_CONFLICT"
    assert _count(client) == SEED_READINGS + 1  # 失败批次整批回滚
