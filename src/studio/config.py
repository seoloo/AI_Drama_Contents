"""설정 로딩: config/settings.yaml + .env."""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(RuntimeError):
    pass


def _deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


@dataclass
class Settings:
    root: Path
    data: dict[str, Any]

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def path(self, dotted: str) -> Path:
        value = self.get(dotted)
        if value is None:
            raise ConfigError(f"설정에 {dotted} 가 없습니다")
        p = Path(value)
        return p if p.is_absolute() else self.root / p

    # --- 자주 쓰는 경로 ---
    @property
    def output_dir(self) -> Path:
        return self.path("paths.output")

    @property
    def work_dir(self) -> Path:
        return self.output_dir / "work"

    @property
    def pending_dir(self) -> Path:
        return self.output_dir / "pending"

    @property
    def approved_dir(self) -> Path:
        return self.output_dir / "approved"

    @property
    def published_dir(self) -> Path:
        return self.output_dir / "published"

    @property
    def series_dir(self) -> Path:
        return self.path("paths.series")

    @property
    def db_path(self) -> Path:
        return self.path("paths.db")

    def provider(self, kind: str) -> str:
        name = self.get(f"providers.{kind}")
        if not name:
            raise ConfigError(f"settings.yaml 의 providers.{kind} 가 비어 있습니다")
        return str(name)


def load_settings(
    root: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> Settings:
    root = Path(root or os.environ.get("STUDIO_ROOT") or PROJECT_ROOT)
    load_dotenv(root / ".env")
    config_file = root / "config" / "settings.yaml"
    if not config_file.exists():
        # 테스트처럼 다른 root 를 쓸 때는 프로젝트 기본 설정을 사용
        config_file = PROJECT_ROOT / "config" / "settings.yaml"
    data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    if overrides:
        data = _deep_merge(data, overrides)
    return Settings(root=root, data=data)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} 가 .env 에 없습니다 (.env.example 참고)")
    return value
