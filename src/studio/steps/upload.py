"""6. 업로드: 승인된 영상만 인스타그램 릴스로 게시합니다.

예약 게시는 우리 쪽에서 처리합니다: `--at` 으로 시각을 기록해 두고,
`studio upload --due` 를 주기적으로(예: Windows 작업 스케줄러) 실행하면 시각이 지난 것만 게시합니다.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from studio.context import Context
from studio.db import Status
from studio.steps import StepError, guarded


def parse_when(text: str) -> datetime:
    """'2026-11-12 19:00' 같은 로컬 시각 또는 ISO 형식 -> 시간대 포함 datetime."""
    dt = datetime.fromisoformat(text.strip().replace(" ", "T", 1))
    if dt.tzinfo is None:
        dt = dt.astimezone()  # 로컬 시간대로 해석
    return dt


def run(ctx: Context, episode_id: str, at: str | None = None) -> None:
    def body(ep):
        if ep.status == Status.PUBLISHED.value:
            raise StepError(f"{episode_id} 는 이미 게시되었습니다 ({ep.ig_media_id}). 중복 업로드를 막았습니다")
        if ep.status == Status.PUBLISHING.value:
            raise StepError(
                f"{episode_id} 는 이전 업로드가 중간에 멈췄습니다. 인스타그램에 올라갔는지 직접 확인한 뒤 "
                "DB 상태를 정리하세요 (중복 게시 방지)"
            )
        if ep.status != Status.APPROVED.value:
            raise StepError(f"승인된 영상만 올릴 수 있습니다. `studio review approve {episode_id}` 먼저 (현재 {ep.status})")

        if at:
            when = parse_when(at)
            if when > datetime.now(timezone.utc):
                ctx.db.update(episode_id, scheduled_at=when.isoformat(timespec="minutes"))
                ctx.db.log(episode_id, "upload", "ok", f"scheduled {when.isoformat()}")
                print(f"[업로드] 예약됨 - {when:%Y-%m-%d %H:%M}. 그 이후 `studio upload --due` 가 실행되면 게시됩니다")
                return

        video = Path(ep.video_path or "")
        if not video.exists():
            raise StepError(f"영상 파일이 없습니다: {video}")

        publisher = ctx.publisher()
        limit = publisher.publishing_limit()
        if limit and limit.get("quota_total") and limit.get("quota_usage", 0) >= limit["quota_total"]:
            raise StepError(f"24시간 게시 한도에 도달했습니다 ({limit['quota_usage']}/{limit['quota_total']})")

        # 업로드 시작을 먼저 기록 -> 중간에 멈춰도 같은 영상이 두 번 올라가지 않게
        ctx.db.set_status(episode_id, Status.PUBLISHING)
        result = publisher.publish_reel(video, ep.caption or "")

        ctx.settings.published_dir.mkdir(parents=True, exist_ok=True)
        dst = ctx.settings.published_dir / video.name
        shutil.move(str(video), dst)
        ctx.db.set_status(episode_id, Status.PUBLISHED, video_path=str(dst),
                          ig_media_id=result.media_id, permalink=result.permalink)
        ctx.db.log(episode_id, "upload", "ok", f"{publisher.name}: {result.media_id}")
        print(f"[업로드] 게시 완료 - {result.media_id} {result.permalink}")

    guarded(ctx, episode_id, "upload", Status.APPROVED, body)


def run_due(ctx: Context) -> int:
    now = datetime.now(timezone.utc)
    count = 0
    for ep in ctx.db.list(Status.APPROVED.value):
        if ep.scheduled_at and datetime.fromisoformat(ep.scheduled_at) <= now:
            try:
                run(ctx, ep.id)
                count += 1
            except Exception as e:  # 하나가 실패해도 나머지는 계속
                print(f"[업로드] {ep.id} 실패: {e}")
    print(f"[업로드] 예약 시각이 지난 영상 {count}개 처리")
    return count
