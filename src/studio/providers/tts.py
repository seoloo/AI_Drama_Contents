"""3. 음성 구현체.  결과는 모두 16bit mono WAV (settings 의 tts.sample_rate)."""

from __future__ import annotations

import math
import struct
from pathlib import Path

from studio.config import Settings, require_env
from studio.cost import CostEstimate, CostLine
from studio.media import write_wav
from studio.providers.base import NotConfigured, SpeechJob


def create(name: str, settings: Settings):
    if name == "mock":
        return MockTTS(settings)
    if name == "elevenlabs":
        return ElevenLabsTTS(settings)
    raise NotConfigured(f"알 수 없는 tts provider: {name}")


class MockTTS:
    """글자 수로 길이를 맞춘 작은 톤 소리를 만듭니다 (내레이터는 낮은 음, 캐릭터는 높은 음)."""

    name = "mock"

    def __init__(self, settings: Settings):
        self.rate = int(settings.get("tts.sample_rate", 24000))
        self.cps = float(settings.get("tts.chars_per_second", 7.0))

    def estimate(self, jobs: list[SpeechJob]) -> CostEstimate:
        return CostEstimate(step="음성 (mock)")

    def synthesize(self, job: SpeechJob) -> tuple[Path, float]:
        seconds = max(1.0, len(job.text.replace(" ", "")) / self.cps)
        n = int(seconds * self.rate)
        freq = 180.0 if job.speaker == "narrator" else 260.0
        frames = bytearray()
        for i in range(n):
            env = min(1.0, i / 800, (n - i) / 800)
            frames += struct.pack("<h", int(600 * env * math.sin(2 * math.pi * freq * i / self.rate)))
        write_wav(job.out_path, bytes(frames), self.rate)
        return job.out_path, 0.0


class ElevenLabsTTS:
    """ElevenLabs text-to-speech.  PCM 으로 받아 WAV 로 감쌉니다.

    아직 실제 호출로 검증하지 않았습니다. 처음 연결할 때 엔드포인트/출력 형식(pcm_24000)이
    요금제에서 지원되는지 확인하세요.
    """

    name = "elevenlabs"
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.rate = int(settings.get("tts.sample_rate", 24000))
        self.model = str(settings.get("tts.elevenlabs_model", "eleven_multilingual_v2"))
        self.price = float(settings.get("pricing.elevenlabs.per_1k_chars", 0.08))
        self.verified = bool(settings.get("pricing.elevenlabs.verified", False))

    def estimate(self, jobs: list[SpeechJob]) -> CostEstimate:
        chars = sum(len(j.text) for j in jobs)
        missing = sorted({j.speaker for j in jobs if not j.voice_id})
        if missing:
            raise NotConfigured(f"ElevenLabs 보이스 ID 가 비어 있습니다: {', '.join(missing)} (series/*.yaml)")
        return CostEstimate(
            step=f"3. 음성 생성 ({self.model})",
            lines=[CostLine("elevenlabs", "글자 수", chars, "자", self.price / 1000, self.verified,
                            f"${self.price:.3f}/1천자")],
            notes=[f"대사/내레이션 {len(jobs)}개"],
        )

    def synthesize(self, job: SpeechJob) -> tuple[Path, float]:
        import requests

        key = require_env("ELEVENLABS_API_KEY")
        resp = requests.post(
            self.URL.format(voice_id=job.voice_id),
            params={"output_format": f"pcm_{self.rate}"},
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": job.text, "model_id": self.model},
            timeout=120,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs 오류 {resp.status_code}: {resp.text[:500]}")
        write_wav(job.out_path, resp.content, self.rate)
        return job.out_path, len(job.text) * self.price / 1000
