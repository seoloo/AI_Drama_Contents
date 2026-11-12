"""4. 편집: 컷 + 자막 + 음성 + 배경음악 -> 1080x1920 MP4 -> output/pending/."""

from __future__ import annotations

from pathlib import Path

from studio.context import Context
from studio.db import Status
from studio.media import build_track, concat_wavs, subtitle_overlay
from studio.providers.base import RenderPlan, RenderShot
from studio.steps import guarded


def _srt_time(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def run(ctx: Context, episode_id: str) -> None:
    def body(ep):
        ws = ctx.workspace(episode_id)
        script = ws.load_script()
        manifest = ws.load_manifest()
        visuals, audio = manifest.get("visuals", {}), manifest.get("audio", {})
        s = ctx.settings
        rate = int(s.get("tts.sample_rate", 24000))
        gap = float(s.get("render.line_gap_sec", 0.25))
        tail = float(s.get("render.shot_tail_sec", 0.4))
        width, height = int(s.get("visual.width", 1080)), int(s.get("visual.height", 1920))
        font = s.get("render.font_path")
        rdir = ws.render_dir

        shots: list[RenderShot] = []
        tracks: list[Path] = []
        srt: list[str] = []
        t = 0.0
        for idx, shot in enumerate(script.shots(), start=1):
            if shot.shot_id not in visuals:
                raise FileNotFoundError(f"{shot.shot_id} 이미지가 없습니다. `studio visuals {episode_id}` 를 먼저 실행하세요")
            entries = audio.get(shot.shot_id, [])
            speech = sum(e["duration"] for e in entries) + gap * max(0, len(entries) - 1)
            duration = max(shot.duration_sec, speech + tail) if entries else shot.duration_sec

            track = build_track([ws.dir / e["path"] for e in entries], gap, duration, rate,
                                rdir / "audio" / f"{shot.shot_id}.wav")
            tracks.append(track)
            overlay = subtitle_overlay(shot.subtitle, width, height, font,
                                       int(s.get("render.subtitle_font_size", 60)),
                                       float(s.get("render.subtitle_y_ratio", 0.66)),
                                       rdir / "subtitles" / f"{shot.shot_id}.png")
            shots.append(RenderShot(shot.shot_id, ws.dir / visuals[shot.shot_id], overlay, duration))
            if shot.subtitle.strip():
                srt.append(f"{idx}\n{_srt_time(t)} --> {_srt_time(t + duration)}\n{shot.subtitle}\n")
            t += duration

        voice_track = concat_wavs(tracks, rate, rdir / "voice_track.wav")
        (rdir / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")

        bgm_setting = str(s.get("render.bgm_file", "") or "")
        bgm = (s.root / bgm_setting) if bgm_setting else None
        out = s.pending_dir / f"{episode_id}.mp4"
        renderer = ctx.renderer()
        renderer.render(RenderPlan(
            episode_id=episode_id, shots=shots, voice_track=voice_track, out_path=out,
            work_dir=rdir, width=width, height=height, fps=int(s.get("render.fps", 30)),
            zoom=bool(s.get("render.zoom", True)), bgm=bgm,
            bgm_volume=float(s.get("render.bgm_volume", 0.12)),
        ))

        ctx.db.set_status(episode_id, Status.PENDING, video_path=str(out))
        ctx.db.log(episode_id, "edit", "ok", f"{renderer.name}: {t:.1f}초")
        print(f"[편집] 완료 - {t:.1f}초, {out}")
        if t > 90:
            print("[편집] 경고: 90초를 넘습니다. 대본을 줄이는 것을 고려하세요")
        print(f"       확인 후 `studio review approve {episode_id}` 또는 `studio review reject {episode_id}`")

    guarded(ctx, episode_id, "edit", Status.VOICED, body)
