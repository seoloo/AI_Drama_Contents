"""4. 편집 구현체: 컷(이미지/영상) + 자막 + 음성 + 배경음악 -> 9:16 MP4."""

from __future__ import annotations

import json
from pathlib import Path

from studio.config import Settings
from studio.media import find_ffmpeg, run_ffmpeg
from studio.providers.base import NotConfigured, RenderPlan, RenderShot

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}


def create(name: str, settings: Settings):
    if name == "ffmpeg":
        return FFmpegRenderer()
    if name == "mock":
        return MockRenderer()
    raise NotConfigured(f"알 수 없는 render provider: {name}")


class MockRenderer:
    """ffmpeg 없이 흐름만 확인할 때. 실제 영상이 아닌 자리표시 파일을 만듭니다."""

    name = "mock"

    def render(self, plan: RenderPlan) -> Path:
        plan.out_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "mock": True,
            "episode": plan.episode_id,
            "shots": [{"id": s.shot_id, "sec": round(s.duration_sec, 2)} for s in plan.shots],
        }
        plan.out_path.write_bytes(b"MOCK-VIDEO\n" + json.dumps(summary, ensure_ascii=False).encode("utf-8"))
        return plan.out_path


class FFmpegRenderer:
    name = "ffmpeg"

    def render(self, plan: RenderPlan) -> Path:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            raise NotConfigured(
                "ffmpeg 를 찾을 수 없습니다. 설치하거나(winget install Gyan.FFmpeg) "
                "`pip install imageio-ffmpeg` 후 다시 실행하세요"
            )
        seg_dir = plan.work_dir / "segments"
        seg_dir.mkdir(parents=True, exist_ok=True)

        names = []
        for i, shot in enumerate(plan.shots):
            out = seg_dir / f"{i:03d}_{shot.shot_id}.mp4"
            self._segment(ffmpeg, plan, shot, out)
            names.append(out.name)

        list_file = seg_dir / "segments.txt"
        list_file.write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")

        plan.out_path.parent.mkdir(parents=True, exist_ok=True)
        args = ["-f", "concat", "-safe", "0", "-i", list_file.name, "-i", str(plan.voice_track.resolve())]
        if plan.bgm and plan.bgm.exists():
            args += ["-stream_loop", "-1", "-i", str(plan.bgm.resolve()),
                     "-filter_complex",
                     f"[2:a]volume={plan.bgm_volume}[b];"
                     "[1:a][b]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
                     "-map", "0:v", "-map", "[a]"]
        else:
            args += ["-map", "0:v", "-map", "1:a"]
        args += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                 "-shortest", "-movflags", "+faststart", str(plan.out_path.resolve())]
        run_ffmpeg(ffmpeg, args, cwd=seg_dir)
        return plan.out_path

    def _segment(self, ffmpeg: str, plan: RenderPlan, shot: RenderShot, out: Path) -> None:
        w, h, fps = plan.width, plan.height, plan.fps
        frames = max(1, round(shot.duration_sec * fps))
        cover = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        is_video = shot.visual.suffix.lower() in VIDEO_EXT

        if is_video:  # 2단계: 영상 클립. 짧으면 마지막 프레임을 늘려 컷 길이를 맞춥니다.
            inputs = ["-i", str(shot.visual.resolve())]
            bg = f"[0:v]{cover},fps={fps},tpad=stop_mode=clone:stop_duration={shot.duration_sec:.3f}[bg]"
        elif plan.zoom:  # 1단계: 정지 이미지에 천천히 확대
            big_w, big_h = w * 3 // 2 // 2 * 2, h * 3 // 2 // 2 * 2
            inputs = ["-i", str(shot.visual.resolve())]
            bg = (f"[0:v]scale={big_w}:{big_h}:force_original_aspect_ratio=increase,crop={big_w}:{big_h},"
                  f"zoompan=z='min(1+0.0007*on,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                  f":d={frames}:s={w}x{h}:fps={fps}[bg]")
        else:
            inputs = ["-loop", "1", "-framerate", str(fps), "-i", str(shot.visual.resolve())]
            bg = f"[0:v]{cover}[bg]"

        args = [*inputs, "-i", str(shot.subtitle_overlay.resolve()),
                "-filter_complex", f"{bg};[bg][1:v]overlay=0:0,format=yuv420p[v]",
                "-map", "[v]", "-frames:v", str(frames), "-r", str(fps),
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-an", str(out.resolve())]
        run_ffmpeg(ffmpeg, args)
