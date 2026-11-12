"""파이프라인 단계.  각 단계는 따로 실행할 수 있습니다.

1 script   대본        -> scripted
2 visuals  이미지/영상  -> visuals_done
3 voice    음성        -> voiced
4 edit     편집        -> pending   (output/pending/)
5 review   검수        -> approved / rejected
6 upload   업로드      -> published
7 기록은 모든 단계에서 db.py 로 남깁니다.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from studio.context import Context
from studio.cost import CostDeclined
from studio.db import Episode, Status, at_least

T = TypeVar("T")

PREVIOUS_STEP = {
    Status.CREATED: "studio new",
    Status.SCRIPTED: "studio script",
    Status.VISUALS_DONE: "studio visuals",
    Status.VOICED: "studio voice",
    Status.PENDING: "studio edit",
    Status.APPROVED: "studio review approve",
}


class StepError(RuntimeError):
    pass


def guarded(ctx: Context, episode_id: str, step: str, required: Status | None,
            body: Callable[[Episode], T]) -> T:
    """단계 실행 공통 처리: 선행 단계 확인, 실패/비용 거절 기록."""
    ep = ctx.db.get(episode_id)
    if ep.status in (Status.PUBLISHED.value, Status.PUBLISHING.value) and step != "upload":
        raise StepError(f"{episode_id} 는 이미 게시(중)되어 수정할 수 없습니다")
    if required and not at_least(ep.status, required):
        raise StepError(
            f"{episode_id} 의 현재 상태는 '{ep.status}' 입니다. 먼저 `{PREVIOUS_STEP[required]} {episode_id}` 를 실행하세요"
        )
    try:
        return body(ep)
    except CostDeclined as e:
        ctx.db.log(episode_id, step, "declined", str(e))
        raise
    except StepError:
        raise
    except Exception as e:
        ctx.db.mark_failed(episode_id, step, f"{type(e).__name__}: {e}")
        raise
