import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """每个测试一个独立临时数据库；启动时跑 seed.init_db 建表+种子数据。"""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import config, db

    importlib.reload(config)
    importlib.reload(db)

    from app import main
    from app.services import preview_tokens

    preview_tokens.reset()
    with TestClient(main.app) as c:
        yield c
