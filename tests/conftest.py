from __future__ import annotations

import pytest

from studio.config import PROJECT_ROOT
from studio.context import Context


def make_ctx(tmp_path, render: str = "mock", confirm=None, **overrides):
    data = {
        "paths": {
            "output": str(tmp_path / "output"),
            "db": str(tmp_path / "output" / "studio.db"),
            "series": str(PROJECT_ROOT / "series"),
        },
        "providers": {"llm": "mock", "visual": "mock", "tts": "mock", "render": render, "publish": "mock"},
    }
    for key, value in overrides.items():
        data[key] = value
    kwargs = {"confirm": confirm} if confirm else {}
    return Context.create(root=tmp_path, overrides=data, **kwargs)


@pytest.fixture
def ctx(tmp_path):
    c = make_ctx(tmp_path)
    yield c
    c.db.close()
