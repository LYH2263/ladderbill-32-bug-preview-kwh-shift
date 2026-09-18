import json

from app.db import connect
from app.engines.peak_compare import compare_plain_vs_peak
from app.engines.tier_progressive import calc_bill
from app.repositories import accounts as accounts_repo
from app.repositories import readings as readings_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import tiers as tiers_repo
from app.services import preview_tokens
from app.services.reading_batch import (
    ACCOUNT_NOT_FOUND,
    DUPLICATE_IN_BATCH,
    PERIOD_CONFLICT,
    ConfirmFailed,
    row_error,
    validate_row,
)


class BillingService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def list_accounts(self):
        return accounts_repo.list_all(self._conn)

    def get_account(self, account_id: int):
        return accounts_repo.get(self._conn, account_id)

    def list_tiers(self):
        return tiers_repo.list_ordered(self._conn)

    def list_readings(self):
        return readings_repo.list_all(self._conn)

    def readings_for_account(self, account_id: int):
        return readings_repo.for_account(self._conn, account_id)

    def preview_readings(self, rows: list[dict]):
        """逐行校验，不写库。全部通过硬校验时签发批次令牌并返回电量合计。"""
        valid_accounts = {a["id"] for a in accounts_repo.list_all(self._conn)}
        seen: dict[tuple[int, str], int] = {}
        results = []
        clean_rows = []
        total = 0.0
        all_valid = True
        for line, raw in enumerate(rows, start=1):
            code, clean = validate_row(raw, valid_accounts)
            if code is None and (clean["account_id"], clean["period"]) in seen:
                code, clean = DUPLICATE_IN_BATCH, None
            if code is not None:
                results.append({"line": line, "status": "error", **row_error(line, code)})
                all_valid = False
                continue
            seen[(clean["account_id"], clean["period"])] = line
            existing = readings_repo.find_by_period(
                self._conn, clean["account_id"], clean["period"]
            )
            if existing:
                results.append(
                    {
                        "line": line,
                        "status": "conflict",
                        **row_error(line, PERIOD_CONFLICT),
                    }
                )
            else:
                results.append({"line": line, "status": "ok", "error_code": None, "message": ""})
            clean_rows.append(clean)
            total += clean["kwh"]
        out = {
            "all_valid": all_valid,
            "ok_count": sum(1 for r in results if r["status"] == "ok"),
            "conflict_count": sum(1 for r in results if r["status"] == "conflict"),
            "error_count": sum(1 for r in results if r["status"] == "error"),
            "total_kwh": round(total, 2) if all_valid else None,
            "token": None,
            "expires_in": None,
            "rows": results,
        }
        if all_valid:
            issued = preview_tokens.issue(clean_rows)
            out["token"] = issued["token"]
            out["expires_in"] = issued["expires_in"]
        return out

    def confirm_readings(self, token: str, overwrite: bool):
        """按令牌整批原子写入；任一行失败整批回滚。撞期行须 overwrite 才替换。"""
        rows = preview_tokens.take(token)
        failures = []
        for line, row in enumerate(rows, start=1):
            if accounts_repo.get(self._conn, row["account_id"]) is None:
                failures.append(row_error(line, ACCOUNT_NOT_FOUND))
                continue
            existing = readings_repo.find_by_period(self._conn, row["account_id"], row["period"])
            if existing and not overwrite:
                failures.append(row_error(line, PERIOD_CONFLICT))
        if failures:
            raise ConfirmFailed(failures)
        try:
            inserted, replaced, qty = readings_repo.persist_rows(
                self._conn, rows, preview_tokens.kwh_cursor()
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        preview_tokens.move_kwh_cursor(qty)
        preview_tokens.consume(token)
        return {"inserted": inserted, "replaced": replaced, "total": inserted + replaced}

    def settings_map(self):
        return settings_repo.get_map(self._conn)

    def run_bill(self, kwh: float, peak: bool, account_id: int | None, persist: bool):
        tiers = tiers_repo.as_calc_rows(self._conn)
        pf = settings_repo.peak_factor(self._conn)
        factor = pf if peak else 1.0
        result = calc_bill(kwh, tiers, factor)
        run_id = None
        if persist:
            run_id = runs_repo.insert(
                self._conn,
                "bill",
                {"kwh": kwh, "peak": peak, "account_id": account_id},
                result,
                account_id,
            )
        return {"run_id": run_id, **result}

    def run_compare(self, kwh: float, persist: bool):
        tiers = tiers_repo.as_calc_rows(self._conn)
        pf = settings_repo.peak_factor(self._conn)
        result = compare_plain_vs_peak(kwh, tiers, pf)
        run_id = None
        if persist:
            run_id = runs_repo.insert(self._conn, "compare", {"kwh": kwh}, result, None)
        return {"run_id": run_id, **result}

    def list_history(self, limit: int = 50):
        return runs_repo.list_recent(self._conn, limit)

    def get_run(self, run_id: int):
        return runs_repo.get(self._conn, run_id)

    def dashboard_stats(self):
        accounts = accounts_repo.list_all(self._conn)
        readings = readings_repo.list_all(self._conn)
        clean = [a for a in accounts if "种子" not in a.get("name", "")]
        dirty = [a for a in accounts if "种子" in a.get("name", "")]
        return {
            "account_count": len(accounts),
            "reading_count": len(readings),
            "clean_accounts": len(clean),
            "dirty_accounts": len(dirty),
            "recent_runs": len(runs_repo.list_recent(self._conn, 5)),
        }
