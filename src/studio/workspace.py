"""회차별 작업 폴더 (output/work/<회차 id>/).

    script.json      1. 대본 (직접 고쳐도 됩니다 - 고친 뒤 다음 단계를 다시 실행)
    images/          2. 컷별 이미지 (2단계 이후엔 clips/)
    audio/           3. 대사/내레이션별 음성 (WAV)
    manifest.json    단계별 결과 기록 (음성 길이 등)
    render/          4. 편집 중간물 (자막 이미지, 컷 영상, 합친 음성)
"""

from __future__ import annotations

import json
from pathlib import Path

from studio.models import EpisodeScript


class Workspace:
    def __init__(self, work_dir: Path, episode_id: str):
        self.episode_id = episode_id
        self.dir = work_dir / episode_id
        self.dir.mkdir(parents=True, exist_ok=True)

    # --- 경로 ---
    @property
    def script_path(self) -> Path:
        return self.dir / "script.json"

    @property
    def manifest_path(self) -> Path:
        return self.dir / "manifest.json"

    def _sub(self, name: str) -> Path:
        p = self.dir / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def images_dir(self) -> Path:
        return self._sub("images")

    @property
    def audio_dir(self) -> Path:
        return self._sub("audio")

    @property
    def render_dir(self) -> Path:
        return self._sub("render")

    def image_path(self, shot_id: str) -> Path:
        return self.images_dir / f"{shot_id}.png"

    def line_audio_path(self, line_id: str) -> Path:
        return self.audio_dir / f"{line_id}.wav"

    # --- 대본 ---
    def has_script(self) -> bool:
        return self.script_path.exists()

    def load_script(self) -> EpisodeScript:
        if not self.script_path.exists():
            raise FileNotFoundError(f"대본이 없습니다. 먼저 `studio script {self.episode_id}` 를 실행하세요")
        return EpisodeScript.model_validate_json(self.script_path.read_text(encoding="utf-8"))

    def save_script(self, script: EpisodeScript) -> None:
        self.script_path.write_text(
            script.model_dump_json(indent=2), encoding="utf-8"
        )

    # --- manifest ---
    def load_manifest(self) -> dict:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {}

    def update_manifest(self, key: str, value) -> dict:
        data = self.load_manifest()
        data[key] = value
        self.manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
