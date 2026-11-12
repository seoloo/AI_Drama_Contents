"""7단계 기록: 회차별 상태를 SQLite 에 저장해 중복 작업/중복 업로드를 막습니다.

status 는 "마지막으로 성공한 단계"입니다.  실패하면 status 는 그대로 두고
failed_step / error 에 기록합니다.  그래서 실패한 단계만 다시 실행할 수 있습니다.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    CREATED = "created"            # 회차 등록됨
    SCRIPTED = "scripted"          # 1. 대본 완료
    VISUALS_DONE = "visuals_done"  # 2. 이미지(영상) 완료
    VOICED = "voiced"              # 3. 음성 완료
    PENDING = "pending"            # 4. 편집 완료 -> 검수 대기 (output/pending)
    APPROVED = "approved"          # 5. 승인됨 (output/approved)
    REJECTED = "rejected"          # 5. 반려됨
    PUBLISHING = "publishing"      # 6. 업로드 중 (중단되면 수동 확인 필요)
    PUBLISHED = "published"        # 6. 게시 완료 (output/published)


ORDER = [
    Status.CREATED,
    Status.SCRIPTED,
    Status.VISUALS_DONE,
    Status.VOICED,
    Status.PENDING,
    Status.APPROVED,
    Status.PUBLISHING,
    Status.PUBLISHED,
]


def at_least(current: str, required: Status) -> bool:
    status = Status(current)
    if status == Status.REJECTED:  # 반려 = 재료(대본/이미지/음성)는 있고 다시 편집해야 하는 상태
        status = Status.VOICED
    return ORDER.index(status) >= ORDER.index(required)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id              TEXT PRIMARY KEY,
    series_id       TEXT NOT NULL,
    number          INTEGER NOT NULL,
    topic           TEXT NOT NULL,
    title           TEXT,
    status          TEXT NOT NULL,
    video_path      TEXT,
    caption         TEXT,
    scheduled_at    TEXT,
    ig_media_id     TEXT,
    permalink       TEXT,
    failed_step     TEXT,
    error           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE(series_id, number)
);
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id  TEXT NOT NULL,
    at          TEXT NOT NULL,
    step        TEXT NOT NULL,
    result      TEXT NOT NULL,   -- ok | failed | skipped | declined
    message     TEXT,
    cost_usd    REAL DEFAULT 0
);
"""


@dataclass
class Episode:
    id: str
    series_id: str
    number: int
    topic: str
    title: str | None
    status: str
    video_path: str | None
    caption: str | None
    scheduled_at: str | None
    ig_media_id: str | None
    permalink: str | None
    failed_step: str | None
    error: str | None
    created_at: str
    updated_at: str


class DB:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- episodes ---
    def create_episode(self, series_id: str, topic: str) -> Episode:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(number), 0) + 1 FROM episodes WHERE series_id = ?", (series_id,)
        ).fetchone()
        number = int(row[0])
        ep_id = f"{series_id}-ep{number:03d}"
        ts = now_iso()
        with self.conn:
            self.conn.execute(
                "INSERT INTO episodes (id, series_id, number, topic, status, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ep_id, series_id, number, topic, Status.CREATED.value, ts, ts),
            )
        self.log(ep_id, "new", "ok", topic)
        return self.get(ep_id)

    def get(self, episode_id: str) -> Episode:
        row = self.conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)).fetchone()
        if row is None:
            raise KeyError(f"회차를 찾을 수 없습니다: {episode_id}")
        return Episode(**dict(row))

    def list(self, status: str | None = None) -> list[Episode]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM episodes WHERE status = ? ORDER BY created_at", (status,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM episodes ORDER BY created_at").fetchall()
        return [Episode(**dict(r)) for r in rows]

    def update(self, episode_id: str, **fields) -> Episode:
        if not fields:
            return self.get(episode_id)
        fields["updated_at"] = now_iso()
        cols = ", ".join(f"{k} = ?" for k in fields)
        values = [v.value if isinstance(v, Status) else v for v in fields.values()]
        with self.conn:
            self.conn.execute(f"UPDATE episodes SET {cols} WHERE id = ?", (*values, episode_id))
        return self.get(episode_id)

    def set_status(self, episode_id: str, status: Status, **fields) -> Episode:
        return self.update(episode_id, status=status, failed_step=None, error=None, **fields)

    def mark_failed(self, episode_id: str, step: str, error: str) -> None:
        self.update(episode_id, failed_step=step, error=error[:2000])
        self.log(episode_id, step, "failed", error[:2000])

    # --- events ---
    def log(self, episode_id: str, step: str, result: str, message: str = "", cost_usd: float = 0.0) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO events (episode_id, at, step, result, message, cost_usd) VALUES (?, ?, ?, ?, ?, ?)",
                (episode_id, now_iso(), step, result, message, cost_usd),
            )

    def events(self, episode_id: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM events WHERE episode_id = ? ORDER BY id", (episode_id,)
        ).fetchall()

    def total_cost(self, episode_id: str | None = None) -> float:
        if episode_id:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM events WHERE episode_id = ?", (episode_id,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM events").fetchone()
        return float(row[0])
