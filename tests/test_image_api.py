"""Nano Banana 2.1 (image_api) 구현을 가짜 Gemini 클라이언트로 확인합니다 (네트워크/비용 0)."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from conftest import make_ctx
from studio.config import load_settings
from studio.cost import CostDeclined
from studio.db import Status
from studio.providers.base import VisualJob
from studio.providers.visual import ImageAPIVisual
from studio.steps import script, visuals


def _png_b64(w=768, h=1376) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (30, 40, 60)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class FakeInteractions:
    """pending 번 만큼 in_progress 를 돌려준 뒤 완료되는 가짜 Interactions API."""

    def __init__(self, image=True, usage=True, pending=0, reject_background=False):
        self.calls: list[dict] = []
        self.gets = 0
        self.image, self.usage, self.pending = image, usage, pending
        self.reject_background = reject_background

    def _done(self):
        usage = SimpleNamespace(total_input_tokens=1000, total_output_tokens=1680, total_thought_tokens=0)
        return SimpleNamespace(
            id="int-1",
            status="completed" if self.image else "failed",
            output_image=SimpleNamespace(data=_png_b64(), mime_type="image/png") if self.image else None,
            output_text="" if self.image else "blocked by safety filter",
            errors=None,
            usage=usage if self.usage else None,
        )

    def create(self, **kwargs):
        self.calls.append(kwargs)
        assert kwargs.get("timeout"), "모든 요청에 timeout 이 있어야 합니다"
        if kwargs.get("background") and self.reject_background:
            raise RuntimeError("400 background is not supported for this model")
        if kwargs.get("background") and self.pending:
            return SimpleNamespace(id="int-1", status="in_progress")
        return self._done()

    def get(self, interaction_id, timeout=None):
        assert timeout
        self.gets += 1
        if self.gets < self.pending:
            return SimpleNamespace(id=interaction_id, status="in_progress")
        return self._done()


def _provider(fake: FakeInteractions) -> ImageAPIVisual:
    p = ImageAPIVisual(load_settings())
    p._client = SimpleNamespace(interactions=fake)
    p.poll_sec = 0
    return p


def _job(tmp_path, refs=()):
    return VisualJob(shot_id="s01_c01", prompt="a cashier at night", out_path=tmp_path / "img" / "s01_c01.png",
                     width=1080, height=1920, duration_sec=6, camera="", motion="",
                     reference_images=list(refs))


def _ref(tmp_path, name):
    p = tmp_path / name
    Image.new("RGB", (64, 64)).save(p)
    return p


def test_estimate_uses_official_price():
    p = ImageAPIVisual(load_settings())
    est = p.estimate([VisualJob(f"s01_c{i:02d}", "x", Path("x.png"), 1080, 1920, 6, "", "") for i in range(9)])
    image_line = est.lines[0]
    assert image_line.quantity == 9 and image_line.unit_price == pytest.approx(0.0504)
    assert image_line.verified
    # 이미지 9장 x $0.0504 + 사고/텍스트 출력 9 x 1,100 tok x $30/1M + 입력
    assert 0.75 < est.total < 0.8


def test_generate_sends_request_and_saves_png(tmp_path):
    fake = FakeInteractions()
    refs = [_ref(tmp_path, f"ref{i}.png") for i in range(6)]
    path, cost = _provider(fake).generate(_job(tmp_path, refs + [refs[0]]))

    call = fake.calls[0]
    assert call["model"] == "gemini-nano-banana-2.1"
    assert call["response_format"] == {"type": "image", "aspect_ratio": "9:16", "image_size": "2K"}
    parts = call["input"]
    assert parts[0] == {"type": "text", "text": "a cashier at night"}
    images = [x for x in parts if x["type"] == "image"]
    assert len(images) == 4  # 참고 이미지는 중복 제거 후 최대 4장
    assert base64.b64decode(images[0]["data"])[:4] == b"\x89PNG"

    with Image.open(path) as img:
        assert img.format == "PNG" and img.size == (768, 1376)
    # 입력 1000 tok x $1.50/1M + 출력 1680 tok x $30/1M
    assert cost == pytest.approx(1000 * 1.5 / 1e6 + 1680 * 30 / 1e6)


def test_generate_polls_background_job(tmp_path):
    fake = FakeInteractions(pending=3)
    path, _ = _provider(fake).generate(_job(tmp_path))
    assert fake.calls[0]["background"] is True
    assert fake.gets == 3 and path.exists()


def test_generate_gives_up_after_max_wait(tmp_path):
    fake = FakeInteractions(pending=10**6)
    p = _provider(fake)
    p.max_wait = 0
    with pytest.raises(RuntimeError, match="int-1"):
        p.generate(_job(tmp_path))


def test_generate_falls_back_when_background_unsupported(tmp_path):
    fake = FakeInteractions(reject_background=True)
    path, _ = _provider(fake).generate(_job(tmp_path))
    assert len(fake.calls) == 2 and "background" not in fake.calls[1]
    assert path.exists()


def test_generate_without_usage_falls_back_to_per_image(tmp_path):
    _, cost = _provider(FakeInteractions(usage=False)).generate(_job(tmp_path))
    assert cost == pytest.approx(0.0504)


def test_generate_raises_when_no_image(tmp_path):
    with pytest.raises(RuntimeError, match="blocked"):
        _provider(FakeInteractions(image=False)).generate(_job(tmp_path))
    assert not (tmp_path / "img" / "s01_c01.png").exists()


def _image_api_ctx(tmp_path, monkeypatch, fake, confirm):
    ctx = make_ctx(tmp_path, confirm=confirm,
                   providers={"llm": "mock", "visual": "image_api", "tts": "mock", "render": "mock",
                              "publish": "mock"})
    monkeypatch.setattr(ImageAPIVisual, "client", lambda self: SimpleNamespace(interactions=fake))
    return ctx


def test_visuals_step_asks_cost_then_generates(tmp_path, monkeypatch):
    fake, asked = FakeInteractions(), []
    ctx = _image_api_ctx(tmp_path, monkeypatch, fake, lambda est: asked.append(est.total) or True)
    ep_id = ctx.db.create_episode("sample", "테스트").id
    script.run(ctx, ep_id)
    visuals.run(ctx, ep_id)

    assert len(asked) == 1 and asked[0] > 0
    assert len(fake.calls) == 9
    assert ctx.db.get(ep_id).status == Status.VISUALS_DONE.value
    assert ctx.db.total_cost(ep_id) > 0

    visuals.run(ctx, ep_id)  # 다시 실행해도 API 를 부르지 않음
    assert len(fake.calls) == 9 and len(asked) == 1
    ctx.db.close()


def test_visuals_step_declined_makes_no_call(tmp_path, monkeypatch):
    fake = FakeInteractions()
    ctx = _image_api_ctx(tmp_path, monkeypatch, fake, lambda est: False)
    ep_id = ctx.db.create_episode("sample", "테스트").id
    script.run(ctx, ep_id)
    with pytest.raises(CostDeclined):
        visuals.run(ctx, ep_id)
    assert fake.calls == []
    assert ctx.db.get(ep_id).status == Status.SCRIPTED.value
    ctx.db.close()
