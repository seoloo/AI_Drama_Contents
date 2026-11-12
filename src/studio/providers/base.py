"""단계별 인터페이스.  새 모델(예: Kling)을 붙일 때는 이 모양만 맞추면 됩니다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from studio.cost import CostEstimate
from studio.models import EpisodeScript, SeriesBible


class NotConfigured(RuntimeError):
    """아직 연결하지 않은 provider 를 골랐을 때."""


# --- 1. 대본 -----------------------------------------------------------------
@dataclass
class ScriptRequest:
    series: SeriesBible
    episode_number: int
    topic: str
    previous_summary: str = ""  # 앞 회차 요약 (시리즈 연속성)


class LLMProvider(Protocol):
    name: str

    def estimate(self, req: ScriptRequest) -> CostEstimate: ...

    def write_script(self, req: ScriptRequest) -> tuple[EpisodeScript, float]:
        """(대본, 실제 비용 USD)"""
        ...


# --- 2. 이미지/영상 ----------------------------------------------------------
@dataclass
class VisualJob:
    shot_id: str
    prompt: str
    out_path: Path
    width: int
    height: int
    duration_sec: float = 0.0          # 영상 모델용 (이미지 모델은 무시)
    camera: str = ""                   # 영상 모델용
    motion: str = ""                   # 영상 모델용
    reference_images: list[Path] = field(default_factory=list)  # 캐릭터 일관성용


class VisualProvider(Protocol):
    name: str
    kind: str  # "image" | "video"

    def estimate(self, jobs: list[VisualJob]) -> CostEstimate: ...

    def generate(self, job: VisualJob) -> tuple[Path, float]:
        """(결과 파일, 실제 비용 USD)"""
        ...


# --- 3. 음성 -----------------------------------------------------------------
@dataclass
class SpeechJob:
    line_id: str
    speaker: str       # 캐릭터 id 또는 "narrator"
    text: str
    voice_id: str
    emotion: str
    out_path: Path     # 16bit mono WAV


class TTSProvider(Protocol):
    name: str

    def estimate(self, jobs: list[SpeechJob]) -> CostEstimate: ...

    def synthesize(self, job: SpeechJob) -> tuple[Path, float]: ...


# --- 4. 편집 -----------------------------------------------------------------
@dataclass
class RenderShot:
    shot_id: str
    visual: Path            # 이미지(1단계) 또는 영상 클립(2단계)
    subtitle_overlay: Path  # 투명 PNG
    duration_sec: float


@dataclass
class RenderPlan:
    episode_id: str
    shots: list[RenderShot]
    voice_track: Path       # 전체 음성 WAV (컷 길이에 맞춰 이미 정렬됨)
    out_path: Path
    work_dir: Path
    width: int
    height: int
    fps: int
    zoom: bool
    bgm: Path | None = None
    bgm_volume: float = 0.12


class Renderer(Protocol):
    name: str

    def render(self, plan: RenderPlan) -> Path: ...


# --- 6. 업로드 ---------------------------------------------------------------
@dataclass
class PublishResult:
    media_id: str
    permalink: str = ""


class Publisher(Protocol):
    name: str

    def publishing_limit(self) -> dict | None:
        """{'quota_usage': int, 'quota_total': int} 또는 확인 불가 시 None"""
        ...

    def publish_reel(self, video_path: Path, caption: str) -> PublishResult: ...
