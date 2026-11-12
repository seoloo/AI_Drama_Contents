"""2. 이미지/영상 생성 구현체.

1단계: 컷마다 이미지 1장 (image_api = Gemini Nano Banana 2.1).
2단계 이후: 같은 VisualJob(프롬프트 + camera/motion + 참조 이미지 + 길이)으로 영상 클립 생성 (kling/seedance).
"""

from __future__ import annotations

import base64
import hashlib
import io
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw

from studio.config import Settings, require_env
from studio.cost import CostEstimate, CostLine
from studio.media import load_font
from studio.providers.base import NotConfigured, VisualJob


def create(name: str, settings: Settings):
    if name == "mock":
        return MockVisual(settings)
    if name == "image_api":
        return ImageAPIVisual(settings)
    if name in ("kling", "seedance", "runway"):
        return VideoAPIVisual(settings, name)
    raise NotConfigured(f"알 수 없는 visual provider: {name}")


class MockVisual:
    """색 배경 + 컷 정보를 그린 가짜 이미지."""

    name = "mock"
    kind = "image"

    def __init__(self, settings: Settings):
        self.font_path = settings.get("render.font_path")

    def estimate(self, jobs: list[VisualJob]) -> CostEstimate:
        return CostEstimate(step="이미지 (mock)")

    def generate(self, job: VisualJob) -> tuple[Path, float]:
        digest = hashlib.md5(job.shot_id.encode()).digest()
        top = (40 + digest[0] % 60, 50 + digest[1] % 60, 80 + digest[2] % 80)
        bottom = (10, 12, 20)
        img = Image.new("RGB", (job.width, job.height), bottom)
        draw = ImageDraw.Draw(img)
        for y in range(job.height):
            t = y / job.height
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            draw.line([(0, y), (job.width, y)], fill=color)
        title = load_font(self.font_path, 72)
        body = load_font(self.font_path, 34)
        draw.text((80, 180), f"MOCK  {job.shot_id}", font=title, fill=(255, 255, 255))
        y = 320
        for line in textwrap.wrap(job.prompt.splitlines()[0], width=38)[:12]:
            draw.text((80, y), line, font=body, fill=(220, 220, 230))
            y += 48
        job.out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(job.out_path)
        return job.out_path, 0.0


class ImageAPIVisual:
    """1단계 실제 이미지 생성: Gemini API 의 Nano Banana 2.1 (gemini-nano-banana-2.1).

    - google-genai SDK 의 Interactions API (client.interactions.create) 를 씁니다.
    - 캐릭터 참고 이미지(job.reference_images)를 함께 보내 얼굴/옷차림 일관성을 높입니다.
    - 결과 이미지에는 구글 SynthID 워터마크가 들어갑니다.
    """

    name = "image_api"
    kind = "image"
    # 문서 기준: nano-banana-2.1 / 3.1-flash-image 는 캐릭터 참고 이미지를 최대 4장까지 받습니다.
    MAX_CHARACTER_REFS = 4
    PROMPT_TOKENS = 400       # 비용 예상용: 컷 프롬프트(캐릭터 외모 포함) 대략치
    REF_IMAGE_TOKENS = 1120   # 비용 예상용: 참고 이미지 1장 입력 토큰 대략치

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = str(settings.get("visual.image_api.model", "gemini-nano-banana-2.1"))
        self.aspect_ratio = str(settings.get("visual.image_api.aspect_ratio", "9:16"))
        self.image_size = str(settings.get("visual.image_api.image_size", "2K"))
        self.max_refs = min(int(settings.get("visual.image_api.max_reference_images", 4)),
                            self.MAX_CHARACTER_REFS)
        self.max_wait = float(settings.get("visual.image_api.max_wait_sec", 300))
        self.poll_sec = float(settings.get("visual.image_api.poll_sec", 3))
        self.request_timeout = float(settings.get("visual.image_api.request_timeout_sec", 60))
        self.extra_output_tokens = int(settings.get("visual.image_api.extra_output_tokens", 1100))
        self._client = None

        table = settings.get("pricing.image", {}) or {}
        entry = table.get(self.model)
        if not entry:
            raise NotConfigured(f"pricing.image 에 {self.model} 단가가 없습니다 (config/settings.yaml)")
        per_image = entry.get("per_image", {}) or {}
        if self.image_size not in per_image:
            raise NotConfigured(f"pricing.image.{self.model}.per_image 에 {self.image_size} 단가가 없습니다")
        self.per_image = float(per_image[self.image_size])
        self.input_price = float(entry["input_per_mtok"])
        self.output_price = float(entry["image_output_per_mtok"])
        self.verified = bool(table.get("verified", False))

    def client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=require_env("GEMINI_API_KEY"))
        return self._client

    def _refs(self, job: VisualJob) -> list[Path]:
        seen, refs = set(), []
        for p in job.reference_images:
            if p not in seen and p.exists():
                seen.add(p)
                refs.append(p)
        return refs[: self.max_refs]

    def estimate(self, jobs: list[VisualJob]) -> CostEstimate:
        n_refs = sum(len(self._refs(j)) for j in jobs)
        input_tokens = len(jobs) * self.PROMPT_TOKENS + n_refs * self.REF_IMAGE_TOKENS
        # 실제 응답에는 이미지 외에 사고/텍스트 출력이 장당 ~700~1,100 토큰 붙습니다 (2026-11-12 실측).
        # 실제 비용 기록(_actual_cost)과 같은 기준(이미지 출력 단가)으로 넉넉히 잡습니다.
        extra_tokens = len(jobs) * self.extra_output_tokens
        return CostEstimate(
            step=f"2. 이미지 생성 ({self.model}, {self.aspect_ratio}, {self.image_size})",
            lines=[
                CostLine("gemini", f"이미지 {self.image_size}", len(jobs), "장", self.per_image, self.verified,
                         f"${self.per_image:.4f}/장"),
                CostLine("gemini", "입력 토큰(대략)", input_tokens, "tok", self.input_price / 1e6, self.verified,
                         f"${self.input_price:.2f}/1M tok"),
                CostLine("gemini", "사고/텍스트 출력(대략)", extra_tokens, "tok", self.output_price / 1e6,
                         self.verified, f"${self.output_price:.2f}/1M tok"),
            ],
            notes=[f"컷 {len(jobs)}개, 캐릭터 참고 이미지 {n_refs}장 첨부"],
        )

    def _input(self, job: VisualJob) -> list[dict]:
        parts: list[dict] = [{"type": "text", "text": job.prompt}]
        for ref in self._refs(job):
            mime = "image/jpeg" if ref.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            if ref.suffix.lower() == ".webp":
                mime = "image/webp"
            parts.append({"type": "image", "data": base64.b64encode(ref.read_bytes()).decode("ascii"),
                          "mime_type": mime})
        return parts

    def _run(self, job: VisualJob):
        """백그라운드로 요청하고 끝날 때까지 짧게 나눠 확인합니다.

        SDK 기본값은 타임아웃이 없어서, 서버가 연결을 끊으면 영원히 기다릴 수 있습니다.
        그래서 모든 요청에 timeout 을 걸고, 생성은 서버 쪽 백그라운드 작업으로 돌립니다.
        """
        client = self.client()
        request = dict(
            model=self.model,
            input=self._input(job),
            response_format={
                "type": "image",
                "aspect_ratio": self.aspect_ratio,
                "image_size": self.image_size,
            },
        )
        try:
            interaction = client.interactions.create(**request, background=True, timeout=self.request_timeout)
        except Exception as exc:
            if "background" not in str(exc).lower():
                raise
            # 이 모델이 백그라운드를 지원하지 않으면(요청 자체가 거절되어 비용 없음) 동기 호출로 다시 요청
            return client.interactions.create(**request, timeout=self.max_wait)

        deadline = time.monotonic() + self.max_wait
        while getattr(interaction, "status", None) in ("queued", "in_progress"):
            if time.monotonic() > deadline:
                raise RuntimeError(f"{job.shot_id}: {self.max_wait:.0f}초 안에 이미지가 완성되지 않았습니다 "
                                   f"(interaction id={interaction.id})")
            time.sleep(self.poll_sec)
            interaction = client.interactions.get(interaction.id, timeout=self.request_timeout)
        return interaction

    def generate(self, job: VisualJob) -> tuple[Path, float]:
        interaction = self._run(job)
        status = getattr(interaction, "status", None)
        image = getattr(interaction, "output_image", None)
        if status not in (None, "completed") or image is None or not getattr(image, "data", None):
            text = (getattr(interaction, "output_text", None) or "")[:300]
            errors = getattr(interaction, "errors", None)
            if "RESOURCE_EXHAUSTED" in str(errors):
                text += (" -> 사용 한도 초과. AI Studio 에서 이 키의 프로젝트에 결제(유료 등급)가 연결됐는지, "
                         "이 모델의 사용 한도(Rate limit)가 0 이 아닌지 확인하세요.")
            raise RuntimeError(f"{job.shot_id}: 이미지를 받지 못했습니다 (status={status}) {text} {errors or ''}".strip())

        job.out_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(io.BytesIO(base64.b64decode(image.data))) as img:
            img.convert("RGB").save(job.out_path, format="PNG")
        return job.out_path, self._actual_cost(interaction)

    def _actual_cost(self, interaction) -> float:
        """사용량이 오면 토큰으로 계산하고, 없으면 장당 단가를 씁니다.

        출력 토큰(사고 토큰 포함)은 모두 이미지 출력 단가로 계산합니다 (실제보다 약간 높게 잡는 쪽).
        """
        usage = getattr(interaction, "usage", None)
        if usage is None or not usage.total_output_tokens:
            return self.per_image
        out_tokens = (usage.total_output_tokens or 0) + (usage.total_thought_tokens or 0)
        by_mod = {getattr(m, "modality", "?"): m.tokens for m in (getattr(usage, "output_tokens_by_modality", None) or [])}
        print(f"  [gemini] 토큰 입력 {usage.total_input_tokens} / 출력 {usage.total_output_tokens} {by_mod or ''}"
              f" / 사고 {usage.total_thought_tokens or 0}")
        return (usage.total_input_tokens or 0) * self.input_price / 1e6 + out_tokens * self.output_price / 1e6


class VideoAPIVisual:
    """2단계 이후: 컷 단위 영상 생성 (Kling / Seedance / Runway).  자리만 잡아 둔 상태입니다."""

    kind = "video"

    def __init__(self, settings: Settings, name: str):
        self.name = name
        self.settings = settings

    def estimate(self, jobs: list[VisualJob]) -> CostEstimate:
        raise NotConfigured(f"{self.name} 는 2단계에서 연결합니다 (초당 단가 x 컷 길이로 비용 계산 예정)")

    def generate(self, job: VisualJob) -> tuple[Path, float]:
        raise NotConfigured(f"{self.name} 는 2단계에서 연결합니다")
