"""미디어 도우미: WAV 처리(파이썬 표준 라이브러리), ffmpeg 찾기, 자막 이미지 그리기."""

from __future__ import annotations

import os
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# WAV  (음성은 모두 16bit mono WAV 로 통일 -> ffmpeg 없이 길이 계산/이어 붙이기 가능)
# ---------------------------------------------------------------------------
SAMPLE_WIDTH = 2  # 16bit
CHANNELS = 1


def write_wav(path: Path, pcm: bytes, sample_rate: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return path


def silence(seconds: float, sample_rate: int) -> bytes:
    return b"\x00" * (int(round(seconds * sample_rate)) * SAMPLE_WIDTH * CHANNELS)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def read_wav(path: Path, expected_rate: int) -> bytes:
    with wave.open(str(path), "rb") as w:
        if w.getframerate() != expected_rate or w.getsampwidth() != SAMPLE_WIDTH or w.getnchannels() != CHANNELS:
            raise ValueError(
                f"{path.name}: {expected_rate}Hz 16bit mono WAV 가 아닙니다 "
                f"({w.getframerate()}Hz, {w.getsampwidth() * 8}bit, {w.getnchannels()}ch)"
            )
        return w.readframes(w.getnframes())


def build_track(clips: list[Path], gap_sec: float, total_sec: float, sample_rate: int, out: Path) -> Path:
    """음성 클립들을 gap 을 두고 이어 붙이고 total_sec 길이로 맞춥니다."""
    pcm = bytearray()
    for i, clip in enumerate(clips):
        if i:
            pcm += silence(gap_sec, sample_rate)
        pcm += read_wav(clip, sample_rate)
    target = int(round(total_sec * sample_rate)) * SAMPLE_WIDTH
    if len(pcm) < target:
        pcm += b"\x00" * (target - len(pcm))
    else:
        pcm = pcm[:target]
    return write_wav(out, bytes(pcm), sample_rate)


def concat_wavs(parts: list[Path], sample_rate: int, out: Path) -> Path:
    pcm = bytearray()
    for p in parts:
        pcm += read_wav(p, sample_rate)
    return write_wav(out, bytes(pcm), sample_rate)


# ---------------------------------------------------------------------------
# ffmpeg
# ---------------------------------------------------------------------------
def find_ffmpeg() -> str | None:
    """FFMPEG_PATH -> PATH -> imageio-ffmpeg(pip 설치본) 순서로 찾습니다."""
    env = os.environ.get("FFMPEG_PATH", "").strip()
    if env and Path(env).exists():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def run_ffmpeg(ffmpeg: str, args: list[str], cwd: Path | None = None) -> None:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패 (code {proc.returncode}):\n{proc.stderr.strip()[-2000:]}")


# ---------------------------------------------------------------------------
# 이미지/자막
# ---------------------------------------------------------------------------
def load_font(font_path: str | None, size: int) -> ImageFont.ImageFont:
    candidates = [font_path, "C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf",
                  "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]
    for c in candidates:
        if c and Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default(size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """한국어는 띄어쓰기 단위로, 너무 긴 단어는 글자 단위로 줄바꿈."""
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for word in paragraph.split(" "):
            trial = f"{current} {word}".strip()
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
                continue
            if current:
                lines.append(current)
            current = ""
            for ch in word:
                if draw.textlength(current + ch, font=font) > max_width and current:
                    lines.append(current)
                    current = ch
                else:
                    current += ch
        lines.append(current)
    return [ln for ln in lines if ln]


def subtitle_overlay(text: str, width: int, height: int, font_path: str | None, size: int,
                     y_ratio: float, out: Path) -> Path:
    """투명 배경 위에 자막을 그린 PNG (영상 위에 겹칩니다)."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if text.strip():
        draw = ImageDraw.Draw(img)
        font = load_font(font_path, size)
        lines = wrap_text(draw, text, font, int(width * 0.84))
        line_h = int(size * 1.35)
        y = int(height * y_ratio) - (line_h * len(lines)) // 2
        for ln in lines:
            w = draw.textlength(ln, font=font)
            draw.text(((width - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
                      stroke_width=max(3, size // 14), stroke_fill=(0, 0, 0, 255))
            y += line_h
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
