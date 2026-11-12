"""6. 업로드 구현체."""

from __future__ import annotations

import hashlib
from pathlib import Path

from studio.config import Settings
from studio.providers.base import NotConfigured, PublishResult


def create(name: str, settings: Settings):
    if name == "mock":
        return MockPublisher()
    if name == "instagram":
        return InstagramPublisher(settings)
    raise NotConfigured(f"알 수 없는 publish provider: {name}")


class MockPublisher:
    """실제로 올리지 않고 게시된 것처럼 기록만 합니다."""

    name = "mock"

    def publishing_limit(self) -> dict | None:
        return {"quota_usage": 0, "quota_total": 50}

    def publish_reel(self, video_path: Path, caption: str) -> PublishResult:
        media_id = "mock-" + hashlib.sha1(str(video_path).encode()).hexdigest()[:12]
        return PublishResult(media_id=media_id, permalink=f"https://example.invalid/reel/{media_id}")


class InstagramPublisher:
    """Instagram Graph API 릴스 게시.

    이미 동작을 확인한 게시 코드를 이 클래스에 옮겨 올 예정입니다.
    필요한 것은 두 메서드뿐입니다:
      - publishing_limit(): content_publishing_limit 엔드포인트로 24시간 사용량/한도 조회
      - publish_reel(video_path, caption): 컨테이너 생성 -> 처리 완료 대기 -> media_publish -> 미디어 ID 반환
    (로컬 영상 파일을 어떻게 올리는지 - 공개 URL 또는 업로드 세션 - 는 기존 코드 방식을 따릅니다)
    """

    name = "instagram"

    def __init__(self, settings: Settings):
        self.settings = settings

    def publishing_limit(self) -> dict | None:
        raise NotConfigured("인스타그램 게시 코드가 아직 연결되지 않았습니다 (기존 코드를 옮겨 올 예정)")

    def publish_reel(self, video_path: Path, caption: str) -> PublishResult:
        raise NotConfigured("인스타그램 게시 코드가 아직 연결되지 않았습니다 (기존 코드를 옮겨 올 예정)")
