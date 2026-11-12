"""5. 검수: output/pending 의 영상을 사람이 보고 승인/반려합니다.  승인한 것만 업로드됩니다."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from studio.context import Context
from studio.db import Status
from studio.steps import StepError, guarded


def list_pending(ctx: Context) -> None:
    items = ctx.db.list(Status.PENDING.value)
    if not items:
        print("검수 대기 중인 영상이 없습니다.")
        return
    for ep in items:
        print(f"- {ep.id}  {ep.title or ''}\n    {ep.video_path}")


def show(ctx: Context, episode_id: str, open_file: bool = False) -> None:
    ep = ctx.db.get(episode_id)
    ws = ctx.workspace(episode_id)
    print(f"{ep.id} [{ep.status}] {ep.title or ''}")
    print(f"주제: {ep.topic}")
    if ws.has_script():
        script = ws.load_script()
        print(f"로그라인: {script.logline}\n훅: {script.hook}\n클리프행어: {script.cliffhanger}")
        for shot in script.shots():
            lines = [shot.narration] + [f"{d.speaker}: {d.text}" for d in shot.dialogue]
            print(f"  {shot.shot_id} ({shot.duration_sec:.0f}s) {' / '.join(x for x in lines if x)}")
    print(f"\n[캡션]\n{ep.caption or ''}\n")
    print(f"영상: {ep.video_path}")
    print(f"누적 비용: ${ctx.db.total_cost(episode_id):.4f}")
    if open_file and ep.video_path and Path(ep.video_path).exists() and hasattr(os, "startfile"):
        os.startfile(ep.video_path)  # Windows 기본 플레이어로 열기


def approve(ctx: Context, episode_id: str, ai_label_confirmed: bool = False) -> None:
    def body(ep):
        if ep.status != Status.PENDING.value:
            raise StepError(f"{episode_id} 는 검수 대기(pending) 상태가 아닙니다 (현재 {ep.status})")
        series = ctx.series(ep.series_id)
        if series.ai_generated_realistic_people and not ai_label_confirmed:
            raise StepError(
                "이 시리즈는 실사풍 AI 인물이 나옵니다. 인스타 계정의 'AI 생성' 라벨/고지를 확인한 뒤 "
                "--ai-label-confirmed 를 붙여 승인하세요"
            )
        src = Path(ep.video_path or "")
        if not src.exists():
            raise StepError(f"영상 파일이 없습니다: {src}")
        ctx.settings.approved_dir.mkdir(parents=True, exist_ok=True)
        dst = ctx.settings.approved_dir / src.name
        shutil.move(str(src), dst)
        ctx.db.set_status(episode_id, Status.APPROVED, video_path=str(dst))
        ctx.db.log(episode_id, "review", "ok", "approved")
        print(f"[검수] 승인 - {dst}\n       업로드: `studio upload {episode_id}` (예약은 --at \"2026-11-12 19:00\")")

    guarded(ctx, episode_id, "review", Status.PENDING, body)


def reject(ctx: Context, episode_id: str, reason: str = "") -> None:
    def body(ep):
        if ep.status not in (Status.PENDING.value, Status.APPROVED.value):
            raise StepError(f"{episode_id} 는 반려할 수 있는 상태가 아닙니다 (현재 {ep.status})")
        ctx.db.set_status(episode_id, Status.REJECTED)
        ctx.db.log(episode_id, "review", "ok", f"rejected: {reason}")
        print(f"[검수] 반려 - {reason or '(사유 없음)'}")
        print("       script.json 을 고치거나 필요한 단계를 --force 로 다시 실행한 뒤 `studio edit` 로 다시 편집하세요")

    guarded(ctx, episode_id, "review", Status.PENDING, body)
