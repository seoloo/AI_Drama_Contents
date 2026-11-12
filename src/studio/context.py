"""실행 컨텍스트: 설정, DB, 비용 확인 방법, 단계별 구현체(provider)를 묶습니다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from studio.config import Settings, load_settings
from studio.cost import ConfirmFn, CostEstimate, interactive_confirm, require_approval
from studio.db import DB
from studio.models import SeriesBible, load_series
from studio.workspace import Workspace


@dataclass
class Context:
    settings: Settings
    db: DB
    confirm: ConfirmFn = interactive_confirm
    force_mock: bool = False
    force: bool = False  # 이미 만든 결과물도 다시 생성
    _cache: dict = field(default_factory=dict)

    @classmethod
    def create(cls, root: Path | None = None, overrides: dict | None = None, **kwargs) -> "Context":
        settings = load_settings(root, overrides)
        return cls(settings=settings, db=DB(settings.db_path), **kwargs)

    # --- 공용 도우미 ---
    def provider_name(self, kind: str) -> str:
        return "mock" if self.force_mock else self.settings.provider(kind)

    def workspace(self, episode_id: str) -> Workspace:
        return Workspace(self.settings.work_dir, episode_id)

    def series(self, series_id: str) -> SeriesBible:
        key = ("series", series_id)
        if key not in self._cache:
            self._cache[key] = load_series(self.settings.series_dir, series_id)
        return self._cache[key]

    def approve_cost(self, estimate: CostEstimate) -> None:
        require_approval(estimate, self.confirm, float(self.settings.get("max_cost_per_run_usd", 3.0)))

    # --- provider (설정에 따라 실제/가짜 구현을 고릅니다) ---
    def llm(self):
        from studio.providers import llm

        return llm.create(self.provider_name("llm"), self.settings)

    def visual(self):
        from studio.providers import visual

        return visual.create(self.provider_name("visual"), self.settings)

    def tts(self):
        from studio.providers import tts

        return tts.create(self.provider_name("tts"), self.settings)

    def renderer(self):
        from studio.providers import render

        # 렌더링은 무료라 --mock 이어도 ffmpeg 가 있으면 실제로 렌더링합니다
        return render.create(self.settings.provider("render"), self.settings)

    def publisher(self):
        from studio.providers import publish

        return publish.create(self.provider_name("publish"), self.settings)
