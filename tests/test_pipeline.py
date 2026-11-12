"""mock 구현으로 1~7단계를 끝까지 돌려 봅니다 (비용 0, API 키 불필요)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_ctx
from studio.cost import CostDeclined, CostEstimate, CostLine
from studio.db import Status
from studio.media import find_ffmpeg
from studio.steps import StepError, edit, review, script, upload, visuals, voice


def make_episode(ctx, topic="영수증에 찍힌 내일 날짜"):
    return ctx.db.create_episode("sample", topic).id


def test_end_to_end_mock(ctx):
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)

    ep = ctx.db.get(ep_id)
    assert ep.status == Status.PENDING.value
    assert Path(ep.video_path).exists()
    assert Path(ep.video_path).parent == ctx.settings.pending_dir
    assert "#숏폼드라마" in ep.caption

    ws = ctx.workspace(ep_id)
    shots = ws.load_script().shots()
    assert len(shots) == 9
    assert all(ws.image_path(s.shot_id).exists() for s in shots)
    assert (ws.render_dir / "voice_track.wav").exists()
    assert (ws.render_dir / "subtitles.srt").read_text(encoding="utf-8").strip()

    review.approve(ctx, ep_id)
    assert ctx.db.get(ep_id).status == Status.APPROVED.value

    upload.run(ctx, ep_id)
    ep = ctx.db.get(ep_id)
    assert ep.status == Status.PUBLISHED.value
    assert ep.ig_media_id.startswith("mock-")
    assert Path(ep.video_path).parent == ctx.settings.published_dir


def test_duplicate_upload_is_blocked(ctx):
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)
    review.approve(ctx, ep_id)
    upload.run(ctx, ep_id)
    with pytest.raises(StepError, match="이미 게시"):
        upload.run(ctx, ep_id)


def test_unapproved_video_cannot_be_uploaded(ctx):
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)
    with pytest.raises(StepError):
        upload.run(ctx, ep_id)
    assert ctx.db.get(ep_id).status == Status.PENDING.value


def test_steps_must_run_in_order(ctx):
    ep_id = make_episode(ctx)
    with pytest.raises(StepError, match="studio script"):
        visuals.run(ctx, ep_id)


def test_rerun_skips_existing_outputs(ctx):
    ep_id = make_episode(ctx)
    script.run(ctx, ep_id)
    visuals.run(ctx, ep_id)
    img = ctx.workspace(ep_id).image_path("s01_c01")
    before = img.stat().st_mtime_ns
    visuals.run(ctx, ep_id)  # 다시 실행해도 이미 있는 이미지는 다시 만들지 않음 (= 돈이 두 번 나가지 않음)
    assert img.stat().st_mtime_ns == before


def test_reject_then_rerender(ctx):
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)
    review.reject(ctx, ep_id, reason="자막이 너무 길다")
    assert ctx.db.get(ep_id).status == Status.REJECTED.value
    with pytest.raises(StepError):
        review.approve(ctx, ep_id)
    edit.run(ctx, ep_id)
    assert ctx.db.get(ep_id).status == Status.PENDING.value


def test_scheduled_upload(ctx):
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)
    review.approve(ctx, ep_id)
    upload.run(ctx, ep_id, at="2999-01-01 09:00")
    assert ctx.db.get(ep_id).status == Status.APPROVED.value
    assert upload.run_due(ctx) == 0
    ctx.db.update(ep_id, scheduled_at="2000-01-01T00:00+00:00")
    assert upload.run_due(ctx) == 1
    assert ctx.db.get(ep_id).status == Status.PUBLISHED.value


# --- 비용 확인 -----------------------------------------------------------------
class PaidLLM:
    """비용이 드는 것처럼 보이는 가짜 LLM."""

    name = "paid"

    def __init__(self, cost):
        from studio.providers.llm import MockLLM

        self.inner, self.cost, self.called = MockLLM(), cost, False

    def estimate(self, req):
        return CostEstimate("test", [CostLine("claude", "tokens", 1, "x", self.cost)])

    def write_script(self, req):
        self.called = True
        return self.inner.write_script(req)


def _with_paid_llm(ctx, monkeypatch, cost):
    llm = PaidLLM(cost)
    monkeypatch.setattr(type(ctx), "llm", lambda self: llm)
    return llm


def test_paid_call_requires_confirmation(tmp_path, monkeypatch):
    asked = []
    ctx = make_ctx(tmp_path, confirm=lambda est: asked.append(est.total) or False)
    llm = _with_paid_llm(ctx, monkeypatch, 0.20)
    ep_id = make_episode(ctx)
    with pytest.raises(CostDeclined):
        script.run(ctx, ep_id)
    assert asked == [pytest.approx(0.20)]
    assert not llm.called
    assert ctx.db.get(ep_id).status == Status.CREATED.value
    ctx.db.close()


def test_paid_call_proceeds_after_yes(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path, confirm=lambda est: True)
    llm = _with_paid_llm(ctx, monkeypatch, 0.20)
    ep_id = make_episode(ctx)
    script.run(ctx, ep_id)
    assert llm.called
    assert ctx.db.get(ep_id).status == Status.SCRIPTED.value
    ctx.db.close()


def test_cost_cap_blocks_without_asking(tmp_path, monkeypatch):
    asked = []
    ctx = make_ctx(tmp_path, confirm=lambda est: asked.append(1) or True)
    llm = _with_paid_llm(ctx, monkeypatch, 999.0)
    ep_id = make_episode(ctx)
    with pytest.raises(CostDeclined, match="상한"):
        script.run(ctx, ep_id)
    assert asked == [] and not llm.called
    ctx.db.close()


# --- 실제 ffmpeg 렌더링 (ffmpeg 가 있을 때만) --------------------------------------
@pytest.mark.skipif(find_ffmpeg() is None, reason="ffmpeg 없음")
def test_ffmpeg_render(tmp_path):
    ctx = make_ctx(tmp_path, render="ffmpeg")
    ep_id = make_episode(ctx)
    for step in (script, visuals, voice, edit):
        step.run(ctx, ep_id)
    video = Path(ctx.db.get(ep_id).video_path)
    assert video.stat().st_size > 100_000
    ctx.db.close()
