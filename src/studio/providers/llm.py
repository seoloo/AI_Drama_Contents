"""1. 대본 생성 구현체."""

from __future__ import annotations

from studio.config import Settings, require_env
from studio.cost import CostEstimate, CostLine, claude_price
from studio.models import DialogueLine, EpisodeScript, Scene, Shot
from studio.prompts import build_script_prompt
from studio.providers.base import NotConfigured, ScriptRequest


def create(name: str, settings: Settings):
    if name == "mock":
        return MockLLM()
    if name == "claude":
        return ClaudeLLM(settings)
    raise NotConfigured(f"알 수 없는 llm provider: {name}")


# ---------------------------------------------------------------------------
class MockLLM:
    """돈이 들지 않는 가짜 대본. 파이프라인 연결 확인용."""

    name = "mock"

    def estimate(self, req: ScriptRequest) -> CostEstimate:
        return CostEstimate(step="대본 (mock)")

    def write_script(self, req: ScriptRequest) -> tuple[EpisodeScript, float]:
        ids = [c.id for c in req.series.characters] or ["narrator"]
        lead = ids[0]
        other = ids[1] if len(ids) > 1 else ids[0]
        plan = [
            ("편의점 계산대", "밤 11시 59분", [
                ("rain-streaked convenience store window at night, clock reads 11:59, close-up",
                 [lead], "오늘도 시계가 열한 시 오십구 분을 가리켰다.", [], "11시 59분"),
                ("the automatic door slides open, a silhouette steps in from the rain, wide shot",
                 [other], "그리고 어김없이, 그 사람이 들어왔다.", [], "그 사람이 왔다"),
                ("cashier glancing up from behind the counter, medium shot",
                 [lead], "", [(lead, "어서 오세요.", "무심하게")], "어서 오세요"),
            ]),
            ("라면 진열대", "자정", [
                ("hand picking the same cup noodle from a shelf, macro shot",
                 [other], "언제나 같은 컵라면. 언제나 하나.", [], "언제나 같은 라면"),
                ("man checking his silver wristwatch, side profile",
                 [other], "그는 계산하기 전에 꼭 시계를 본다.", [], "시계를 보는 남자"),
                ("cashier scanning a cup noodle, receipt printing, close-up",
                 [lead, other], "", [(other, "영수증은 버려 주세요.", "낮게")], "영수증은 버려 주세요"),
            ]),
            ("편의점 밖", "자정 이후", [
                ("cashier unfolding a crumpled receipt, neon light on her face",
                 [lead], "오늘은 이상하게 영수증을 버릴 수가 없었다.", [], "버리지 못한 영수증"),
                ("receipt in hand, printed date is tomorrow, extreme close-up",
                 [lead], "영수증에 찍힌 날짜는, 내일이었다.", [], "날짜가 내일이다"),
                ("empty rainy street, the man is gone, wide shot",
                 [lead], "", [(lead, "...당신, 누구예요?", "떨리는 목소리로")], "당신, 누구예요?"),
            ]),
        ]
        scenes = []
        for si, (loc, tod, shots) in enumerate(plan, start=1):
            scene_shots = []
            for ci, (prompt, chars, narration, dialogue, subtitle) in enumerate(shots, start=1):
                scene_shots.append(Shot(
                    shot_id=f"s{si:02d}_c{ci:02d}",
                    duration_sec=6.0,
                    characters=chars,
                    visual_prompt=prompt,
                    camera="slow push-in",
                    motion="",
                    narration=narration,
                    dialogue=[DialogueLine(speaker=s, text=t, emotion=e) for s, t, e in dialogue],
                    subtitle=subtitle,
                ))
            scenes.append(Scene(scene_id=f"s{si:02d}", location=loc, time_of_day=tod,
                                summary=f"[mock] {loc}", shots=scene_shots))
        script = EpisodeScript(
            title=f"[mock] {req.series.title} {req.episode_number}화",
            logline=f"[mock] {req.topic}",
            hook="11시 59분을 가리키는 시계",
            scenes=scenes,
            cliffhanger="영수증의 날짜가 내일이다",
            caption=f"[mock] {req.topic}",
            hashtags=["숏폼드라마", "미스터리", "편의점", "AI드라마", "웹드라마"],
        )
        return script, 0.0


# ---------------------------------------------------------------------------
class ClaudeLLM:
    """Claude API 로 대본(JSON)을 받습니다.  구조화 출력으로 EpisodeScript 스키마를 강제합니다."""

    name = "claude"
    # 서버 측 거절(refusal) 대체 모델을 지원하는 모델 (Haiku 5.5 는 미지원)
    _FALLBACK_MODELS = ("claude-opus-5", "claude-sonnet-5-5", "claude-fable-5")

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = str(settings.get("llm.model", "claude-opus-5-5"))
        self.effort = str(settings.get("llm.effort", "medium"))
        self.max_tokens = int(settings.get("llm.max_tokens", 16000))
        self.est_output = int(settings.get("llm.estimated_output_tokens", 8000))
        self._client = None

    def client(self):
        if self._client is None:
            import anthropic

            require_env("ANTHROPIC_API_KEY")
            self._client = anthropic.Anthropic()
        return self._client

    def _messages(self, req: ScriptRequest):
        system, user = build_script_prompt(req.series, req.episode_number, req.topic, req.previous_summary)
        return system, [{"role": "user", "content": user}]

    def estimate(self, req: ScriptRequest) -> CostEstimate:
        system, messages = self._messages(req)
        in_price, out_price, verified = claude_price(self.settings, self.model)
        # 입력 토큰은 count_tokens(무료)로 정확히 셉니다. 출력 스키마 몫으로 여유분을 더합니다.
        counted = self.client().messages.count_tokens(model=self.model, system=system, messages=messages)
        input_tokens = counted.input_tokens + 1500
        return CostEstimate(
            step=f"1. 대본 생성 ({self.model}, effort={self.effort})",
            lines=[
                CostLine("claude", "입력 토큰", input_tokens, "tok", in_price / 1e6, verified,
                         f"${in_price:.2f}/1M tok"),
                CostLine("claude", "출력 토큰(예상)", self.est_output, "tok", out_price / 1e6, verified,
                         f"${out_price:.2f}/1M tok"),
            ],
            notes=[f"출력은 사고 토큰을 포함한 대략치입니다. 최대 {self.max_tokens:,} 토큰까지 나올 수 있습니다."],
        )

    def write_script(self, req: ScriptRequest) -> tuple[EpisodeScript, float]:
        system, messages = self._messages(req)
        kwargs = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
            output_format=EpisodeScript,
            output_config={"effort": self.effort},
        )
        if self.model.startswith(self._FALLBACK_MODELS):
            kwargs.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        response = self.client().beta.messages.parse(**kwargs)

        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            raise RuntimeError(f"Claude 가 요청을 거절했습니다: {details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("출력이 max_tokens 에서 잘렸습니다. settings.yaml 의 llm.max_tokens 를 늘리세요")
        script = response.parsed_output
        if script is None:
            raise RuntimeError("대본 JSON 을 해석하지 못했습니다")

        in_price, out_price, _ = claude_price(self.settings, self.model)
        usage = response.usage
        cost = usage.input_tokens * in_price / 1e6 + usage.output_tokens * out_price / 1e6
        return script, cost
