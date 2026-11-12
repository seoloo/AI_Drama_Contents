"""1. 대본 생성: 주제 -> 장면/컷/내레이션/대사/이미지 프롬프트/캡션/해시태그 (script.json)."""

from __future__ import annotations

from studio.context import Context
from studio.db import Status
from studio.providers.base import ScriptRequest
from studio.steps import guarded


def _previous_summary(ctx: Context, series_id: str, number: int) -> str:
    if number <= 1:
        return ""
    prev_id = f"{series_id}-ep{number - 1:03d}"
    ws = ctx.workspace(prev_id)
    if not ws.has_script():
        return ""
    prev = ws.load_script()
    return f"{prev.title}: {prev.logline} / 마지막 장면: {prev.cliffhanger}"


def run(ctx: Context, episode_id: str) -> None:
    def body(ep):
        ws = ctx.workspace(episode_id)
        if ws.has_script() and not ctx.force:
            print(f"[대본] 이미 있습니다: {ws.script_path}  (다시 만들려면 --force)")
            ctx.db.log(episode_id, "script", "skipped", "script.json exists")
            if ep.status == Status.CREATED.value:
                ctx.db.set_status(episode_id, Status.SCRIPTED)
            return

        series = ctx.series(ep.series_id)
        req = ScriptRequest(
            series=series,
            episode_number=ep.number,
            topic=ep.topic,
            previous_summary=_previous_summary(ctx, ep.series_id, ep.number),
        )
        llm = ctx.llm()
        ctx.approve_cost(llm.estimate(req))
        script, cost = llm.write_script(req)

        known = {c.id for c in series.characters}
        unknown = sorted({cid for s in script.shots() for cid in s.characters if cid not in known})
        if unknown:
            print(f"[대본] 경고: 캐릭터 바이블에 없는 id 가 있습니다: {', '.join(unknown)}")

        ws.save_script(script)
        footer = str(ctx.settings.get("publish.caption_footer", "") or "")
        ctx.db.set_status(episode_id, Status.SCRIPTED, title=script.title,
                          caption=script.full_caption(footer))
        total = sum(s.duration_sec for s in script.shots())
        ctx.db.log(episode_id, "script", "ok", f"{llm.name}: {len(script.shots())}컷 {total:.0f}초", cost)
        print(f"[대본] {script.title} - {len(script.scenes)}장면 {len(script.shots())}컷, 약 {total:.0f}초 "
              f"(비용 ${cost:.4f})")
        print(f"       {ws.script_path}  <- 직접 고친 뒤 다음 단계를 진행해도 됩니다")

    guarded(ctx, episode_id, "script", Status.CREATED, body)
