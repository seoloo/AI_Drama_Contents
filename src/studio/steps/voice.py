"""3. 음성: 컷마다 내레이션 + 대사를 줄 단위 WAV 로 만듭니다."""

from __future__ import annotations

from studio.context import Context
from studio.db import Status
from studio.media import wav_duration
from studio.providers.base import SpeechJob
from studio.steps import guarded


def run(ctx: Context, episode_id: str) -> None:
    def body(ep):
        ws = ctx.workspace(episode_id)
        script = ws.load_script()
        series = ctx.series(ep.series_id)
        provider = ctx.tts()
        narrator_voice = series.narrator.elevenlabs_voice_id

        plan: dict[str, list[dict]] = {}
        jobs: list[SpeechJob] = []
        for shot in script.shots():
            lines = []
            if shot.narration.strip():
                lines.append(("narrator", shot.narration, narrator_voice, ""))
            for d in shot.dialogue:
                c = series.character(d.speaker)
                lines.append((d.speaker, d.text, c.voice.elevenlabs_voice_id if c else "", d.emotion))
            entries = []
            for n, (speaker, text, voice_id, emotion) in enumerate(lines, start=1):
                line_id = f"{shot.shot_id}_l{n:02d}"
                out = ws.line_audio_path(line_id)
                entries.append({"line_id": line_id, "speaker": speaker, "text": text,
                                "path": str(out.relative_to(ws.dir))})
                if out.exists() and not ctx.force:
                    continue
                jobs.append(SpeechJob(line_id=line_id, speaker=speaker, text=text,
                                      voice_id=voice_id, emotion=emotion, out_path=out))
            plan[shot.shot_id] = entries

        spent = 0.0
        try:
            if jobs:
                ctx.approve_cost(provider.estimate(jobs))
                for i, job in enumerate(jobs, start=1):
                    _, cost = provider.synthesize(job)
                    spent += cost
                    print(f"[음성] {i}/{len(jobs)} {job.line_id} ({job.speaker})")
            else:
                print("[음성] 모든 줄이 이미 있습니다 (다시 만들려면 --force)")
        finally:
            if spent:  # 중간에 실패해도 이미 쓴 비용은 기록
                ctx.db.log(episode_id, "voice", "cost", "생성 비용", spent)

        for entries in plan.values():
            for e in entries:
                e["duration"] = round(wav_duration(ws.dir / e["path"]), 3)
        ws.update_manifest("audio", plan)
        ctx.db.set_status(episode_id, Status.VOICED)
        total = sum(e["duration"] for es in plan.values() for e in es)
        ctx.db.log(episode_id, "voice", "ok", f"{provider.name}: {len(jobs)}줄 생성, 음성 {total:.1f}초")
        print(f"[음성] 완료 - 새로 만든 줄 {len(jobs)}개, 음성 합계 {total:.1f}초, 비용 ${spent:.4f}")

    guarded(ctx, episode_id, "voice", Status.VISUALS_DONE, body)
