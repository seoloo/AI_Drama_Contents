"""데이터 구조.

대본은 처음부터 드라마 구조(회차 -> 장면 -> 컷)로 만듭니다.
1단계(image_narration)는 컷마다 정지 이미지 + 내레이션만 쓰고,
2단계 이후에는 같은 대본의 dialogue / camera / motion 을 영상 생성에 씁니다.
그래서 형식을 넓혀도 대본 단계는 다시 만들 필요가 없습니다.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 시리즈 / 캐릭터 바이블 (사람이 쓰는 YAML)
# ---------------------------------------------------------------------------
class Voice(BaseModel):
    elevenlabs_voice_id: str = ""


class Character(BaseModel):
    id: str
    name: str
    role: str = ""
    age: str | int | None = None
    personality: str = ""
    appearance: str = Field("", description="모든 컷 프롬프트에 붙는 고정 외모 묘사")
    voice: Voice = Field(default_factory=Voice)
    reference_images: list[str] = Field(default_factory=list)


class Narrator(BaseModel):
    name: str = "내레이터"
    elevenlabs_voice_id: str = ""


class SeriesBible(BaseModel):
    id: str
    title: str
    genre: str = ""
    logline: str = ""
    world: str = ""
    tone: str = ""
    visual_style: str = ""
    narration_style: str = ""
    format: str = "image_narration"
    target_duration_sec: int = 60
    narrator: Narrator = Field(default_factory=Narrator)
    ai_generated_realistic_people: bool = False
    characters: list[Character] = Field(default_factory=list)

    def character(self, char_id: str) -> Character | None:
        return next((c for c in self.characters if c.id == char_id), None)


def load_series(series_dir: Path, series_id: str) -> SeriesBible:
    folder = series_dir / series_id
    meta = folder / "series.yaml"
    if not meta.exists():
        raise FileNotFoundError(f"시리즈 설정이 없습니다: {meta}")
    data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
    chars = []
    for f in sorted((folder / "characters").glob("*.yaml")):
        chars.append(Character(**(yaml.safe_load(f.read_text(encoding="utf-8")) or {})))
    data["characters"] = chars
    return SeriesBible(**data)


# ---------------------------------------------------------------------------
# 대본 (LLM 이 만드는 JSON).  구조화 출력 스키마로 그대로 쓰기 때문에
# 모든 필드를 필수로 두었습니다 (빈 값은 "" 또는 [] 로).
# ---------------------------------------------------------------------------
class DialogueLine(BaseModel):
    speaker: str = Field(description="캐릭터 id")
    text: str = Field(description="한국어 대사")
    emotion: str = Field(description="감정/톤 (예: 담담하게, 놀라서)")


class Shot(BaseModel):
    shot_id: str = Field(description="예: s01_c01")
    duration_sec: float = Field(description="컷 길이(초), 보통 4~8")
    characters: list[str] = Field(description="화면에 나오는 캐릭터 id 목록")
    visual_prompt: str = Field(
        description="영어 이미지 프롬프트. 행동/표정/구도/배경만 쓰고 캐릭터 고정 외모는 쓰지 않는다"
    )
    camera: str = Field(description="카메라 연출 (예: close-up, slow push-in). 2단계 영상용")
    motion: str = Field(description="움직임 묘사. 2단계 영상용")
    narration: str = Field(description="이 컷의 한국어 내레이션 (없으면 빈 문자열)")
    dialogue: list[DialogueLine] = Field(description="이 컷의 대사 (없으면 빈 배열)")
    subtitle: str = Field(description="화면에 띄울 짧은 한국어 자막")


class Scene(BaseModel):
    scene_id: str = Field(description="예: s01")
    location: str
    time_of_day: str
    summary: str
    shots: list[Shot]


class EpisodeScript(BaseModel):
    title: str
    logline: str
    hook: str = Field(description="첫 3초 안에 시선을 잡는 장치")
    scenes: list[Scene]
    cliffhanger: str = Field(description="다음 화로 이어지는 궁금증")
    caption: str = Field(description="인스타그램 캡션 (해시태그 제외)")
    hashtags: list[str] = Field(description="'#' 없이 5~10개")

    def shots(self) -> list[Shot]:
        return [shot for scene in self.scenes for shot in scene.shots]

    def full_caption(self, footer: str = "") -> str:
        tags = " ".join("#" + t.lstrip("#").replace(" ", "") for t in self.hashtags)
        parts = [self.caption.strip(), tags]
        if footer:
            parts.append(footer.strip())
        return "\n\n".join(p for p in parts if p)
