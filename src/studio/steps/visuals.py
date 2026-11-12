"""2. 이미지 생성 (1단계: 컷당 1장).  2단계부터는 같은 단계에서 영상 클립을 만듭니다."""

from __future__ import annotations

from pathlib import Path

from studio.context import Context
from studio.db import Status
from studio.prompts import build_visual_prompt
from studio.providers.base import VisualJob
from studio.steps import guarded


def run(ctx: Context, episode_id: str) -> None:
    def body(ep):
        ws = ctx.workspace(episode_id)
        script = ws.load_script()
        series = ctx.series(ep.series_id)
        provider = ctx.visual()
        width = int(ctx.settings.get("visual.width", 1080))
        height = int(ctx.settings.get("visual.height", 1920))
        series_folder = ctx.settings.series_dir / ep.series_id

        outputs: dict[str, str] = {}
        jobs: list[VisualJob] = []
        for shot in script.shots():
            if provider.kind == "image":
                out = ws.image_path(shot.shot_id)
            else:
                out = ws.dir / "clips" / f"{shot.shot_id}.mp4"
            outputs[shot.shot_id] = str(out.relative_to(ws.dir))
            if out.exists() and not ctx.force:
                continue
            refs: list[Path] = []
            for cid in shot.characters:
                c = series.character(cid)
                if c:
                    refs += [series_folder / r for r in c.reference_images]
            jobs.append(VisualJob(
                shot_id=shot.shot_id,
                prompt=build_visual_prompt(series, shot.characters, shot.visual_prompt),
                out_path=out, width=width, height=height,
                duration_sec=shot.duration_sec, camera=shot.camera, motion=shot.motion,
                reference_images=[r for r in refs if r.exists()],
            ))

        spent = 0.0
        try:
            if jobs:
                ctx.approve_cost(provider.estimate(jobs))
                for i, job in enumerate(jobs, start=1):
                    _, cost = provider.generate(job)
                    spent += cost
                    print(f"[이미지] {i}/{len(jobs)} {job.shot_id}")
            else:
                print("[이미지] 모든 컷이 이미 있습니다 (다시 만들려면 --force)")
        finally:
            if spent:  # 중간에 실패해도 이미 쓴 비용은 기록
                ctx.db.log(episode_id, "visuals", "cost", "생성 비용", spent)

        ws.update_manifest("visuals", outputs)
        ws.update_manifest("visual_kind", provider.kind)
        ctx.db.set_status(episode_id, Status.VISUALS_DONE)
        ctx.db.log(episode_id, "visuals", "ok", f"{provider.name}: {len(jobs)}개 생성")
        print(f"[이미지] 완료 - 새로 만든 컷 {len(jobs)}개, 비용 ${spent:.4f}  ({ws.images_dir})")

    guarded(ctx, episode_id, "visuals", Status.SCRIPTED, body)
