"""대본 생성 프롬프트.  톤/형식을 바꾸고 싶으면 이 파일을 고치세요."""

from __future__ import annotations

from studio.models import SeriesBible

FORMAT_RULES = {
    "image_narration": (
        "이번 형식은 '정지 이미지 + 내레이션' 입니다. 컷마다 이미지 1장이 화면에 나오고 "
        "내레이션이 이야기를 끌고 갑니다. 대사는 꼭 필요한 순간에만 짧게 넣으세요. "
        "인물의 큰 움직임보다 표정, 소품, 분위기로 장면을 보여 주세요."
    ),
    "anime": (
        "이번 형식은 '2D 캐릭터 애니메이션' 입니다. 컷마다 3~8초 영상이 만들어집니다. "
        "대사 중심으로 쓰고 camera 와 motion 을 구체적으로 적으세요."
    ),
    "live_action": (
        "이번 형식은 '실사풍 AI 드라마' 입니다. 컷마다 3~8초 영상이 만들어집니다. "
        "대사 중심으로 쓰고 camera 와 motion 을 구체적으로 적으세요."
    ),
}


def build_script_prompt(series: SeriesBible, episode_number: int, topic: str,
                        previous_summary: str = "") -> tuple[str, str]:
    chars = "\n".join(
        f"- id: {c.id} / 이름: {c.name} / 역할: {c.role} / 성격: {c.personality}"
        for c in series.characters
    ) or "- (등록된 캐릭터 없음)"
    target = series.target_duration_sec
    format_rule = FORMAT_RULES.get(series.format, FORMAT_RULES["image_narration"])

    system = f"""당신은 인스타그램 릴스용 한국어 숏폼 드라마 작가입니다.

[시리즈 바이블]
제목: {series.title}
장르: {series.genre}
로그라인: {series.logline.strip()}
세계관: {series.world.strip()}
톤: {series.tone}
내레이션 스타일: {series.narration_style}

[등장인물]
{chars}

[형식]
{format_rule}

[작성 규칙]
- 세로 9:16 화면, 전체 길이 약 {target}초. 장면 3~4개, 컷은 모두 8~10개, 컷 하나는 4~8초.
- 첫 컷(첫 3초)에서 바로 궁금증을 만드세요. 인사나 배경 설명으로 시작하지 마세요.
- 한국어 낭독은 초당 약 7글자입니다. 컷의 내레이션과 대사를 합친 길이가 duration_sec 안에 읽히게 쓰세요.
- visual_prompt 는 영어로, 행동/표정/구도/배경/조명만 쓰세요. 캐릭터의 고정 외모(머리, 옷 등)는 쓰지 마세요.
  고정 외모와 화풍은 프로그램이 캐릭터 바이블에서 자동으로 붙입니다. 화면에 글자가 나오게 하지 마세요.
- characters 에는 위 등장인물 id 만 쓰세요. 대사의 speaker 도 등장인물 id 입니다.
- subtitle 은 화면에 띄울 짧은 자막(20자 안팎)입니다.
- 마지막 컷은 다음 화가 궁금해지는 장면으로 끝내세요 (cliffhanger).
- 실존 인물, 기존 작품의 캐릭터/설정, 상표를 쓰지 마세요. 사람이 쓴 것 같은 고유한 이야기로 쓰세요.
- caption 은 해시태그 없이 1~3문장, hashtags 는 '#' 없이 5~10개.
- shot_id 는 s01_c01 처럼 장면번호_컷번호 형식으로 쓰세요."""

    user = f"{episode_number}화를 써 주세요.\n주제/줄거리: {topic.strip()}"
    if previous_summary.strip():
        user += f"\n\n[지난 화 요약]\n{previous_summary.strip()}"
    return system, user


def build_visual_prompt(series: SeriesBible, character_ids: list[str], shot_prompt: str) -> str:
    """컷 프롬프트 + 화풍 + 캐릭터 고정 외모 -> 이미지/영상 모델에 보낼 최종 프롬프트."""
    looks = []
    for cid in character_ids:
        c = series.character(cid)
        if c and c.appearance.strip():
            looks.append(f"{c.name} ({cid}): {c.appearance.strip()}")
    parts = [shot_prompt.strip()]
    if looks:
        parts.append("Characters: " + "; ".join(looks))
    if series.visual_style.strip():
        parts.append("Style: " + series.visual_style.strip())
    parts.append("No text, no captions, no watermark.")
    return "\n".join(parts)
