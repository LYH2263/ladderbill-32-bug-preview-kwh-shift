# 12-ladderbill（阶梯电费）

Ladderbill — 居民阶梯电价分段累进（含尖峰系数）

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4100 |
| API | http://localhost:9100 |

## 主链

抄表录入 → 阶梯分段计费 → 账单明细

## 抄表批次（预览确认）

- `POST /api/readings/preview`：接收多行 `{account_id, period(YYYY-MM), kwh, peak}`，逐行返回行号/状态/错误码，全部通过时返回电量合计与批次令牌（10 分钟有效），全程不写库。
- `POST /api/readings/confirm`：凭预览令牌整批原子写入，任一行失败整批回滚并返回失败行号与原因；令牌过期或复用拒绝（409）。同户同账期已有抄表时须带 `overwrite: true` 才替换，否则撞期失败。
- 前端「抄表」页：多行编辑 → 预览看行级错误与合计 → 确认写入后列表刷新，预览阶段列表行数不变。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
