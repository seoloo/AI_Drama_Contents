"""명령줄 진입점.  `studio --help` 또는 `python -m studio --help`."""

from __future__ import annotations

import argparse
import sys

from studio.config import ConfigError
from studio.context import Context
from studio.cost import CostDeclined
from studio.db import Status
from studio.providers.base import NotConfigured
from studio.steps import StepError
from studio.steps import edit, review, script, upload, visuals, voice

STATUS_KO = {
    Status.CREATED.value: "등록됨",
    Status.SCRIPTED.value: "대본 완료",
    Status.VISUALS_DONE.value: "이미지 완료",
    Status.VOICED.value: "음성 완료",
    Status.PENDING.value: "검수 대기",
    Status.APPROVED.value: "승인",
    Status.REJECTED.value: "반려",
    Status.PUBLISHING.value: "업로드 중",
    Status.PUBLISHED.value: "게시됨",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studio", description="AI 숏폼 드라마 제작 파이프라인")
    p.add_argument("--mock", action="store_true", help="모든 유료 단계를 가짜 구현으로 실행 (비용 0)")
    p.add_argument("--force", action="store_true", help="이미 만든 결과물도 다시 생성")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="새 회차 등록")
    n.add_argument("--series", required=True, help="series/ 아래 폴더 이름")
    n.add_argument("--topic", required=True, help="이번 화 주제/줄거리")

    for name, help_ in [("script", "1. 대본 생성"), ("visuals", "2. 이미지 생성"),
                        ("voice", "3. 음성 생성"), ("edit", "4. 편집 (MP4)"),
                        ("make", "1~4 단계를 이어서 실행")]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("episode")

    r = sub.add_parser("review", help="5. 검수")
    rs = r.add_subparsers(dest="action", required=True)
    rs.add_parser("list", help="검수 대기 목록")
    sh = rs.add_parser("show", help="대본/캡션/비용 보기")
    sh.add_argument("episode")
    sh.add_argument("--open", action="store_true", help="영상 파일 열기")
    ap = rs.add_parser("approve", help="승인 -> 업로드 가능")
    ap.add_argument("episode")
    ap.add_argument("--ai-label-confirmed", action="store_true",
                    help="실사풍 AI 인물 시리즈: AI 생성 라벨/고지를 확인했음")
    rj = rs.add_parser("reject", help="반려")
    rj.add_argument("episode")
    rj.add_argument("--reason", default="")

    u = sub.add_parser("upload", help="6. 승인된 영상 업로드")
    u.add_argument("episode", nargs="?")
    u.add_argument("--at", help='예약 시각 (예: "2026-11-12 19:00", 로컬 시간)')
    u.add_argument("--due", action="store_true", help="예약 시각이 지난 승인 영상을 모두 업로드")

    st = sub.add_parser("status", help="7. 회차 상태/비용 기록 보기")
    st.add_argument("episode", nargs="?")

    ul = sub.add_parser("unlock", help="업로드가 중간에 멈춘 회차를 승인 상태로 되돌림 (직접 확인 후)")
    ul.add_argument("episode")
    return p


def cmd_status(ctx: Context, episode_id: str | None) -> None:
    if episode_id:
        ep = ctx.db.get(episode_id)
        print(f"{ep.id} [{STATUS_KO.get(ep.status, ep.status)}] {ep.title or ''}")
        if ep.error:
            print(f"  실패: {ep.failed_step} - {ep.error}")
        for ev in ctx.db.events(episode_id):
            cost = f" ${ev['cost_usd']:.4f}" if ev["cost_usd"] else ""
            print(f"  {ev['at']}  {ev['step']:<8} {ev['result']:<8}{cost}  {ev['message'] or ''}")
        print(f"  누적 비용 ${ctx.db.total_cost(episode_id):.4f}")
        return
    episodes = ctx.db.list()
    if not episodes:
        print("등록된 회차가 없습니다. `studio new --series sample --topic \"...\"` 로 시작하세요")
        return
    for ep in episodes:
        flag = f"  (실패: {ep.failed_step})" if ep.error else ""
        sched = f"  예약 {ep.scheduled_at}" if ep.scheduled_at and ep.status == Status.APPROVED.value else ""
        print(f"{ep.id:<18} {STATUS_KO.get(ep.status, ep.status):<8} ${ctx.db.total_cost(ep.id):>7.4f}  "
              f"{ep.title or ep.topic}{flag}{sched}")
    print(f"전체 누적 비용 ${ctx.db.total_cost():.4f}")


def dispatch(ctx: Context, args: argparse.Namespace) -> None:
    if args.cmd == "new":
        ctx.series(args.series)  # 시리즈 설정이 있는지 먼저 확인
        ep = ctx.db.create_episode(args.series, args.topic)
        print(f"[등록] {ep.id}  다음: `studio make {ep.id}` (또는 script/visuals/voice/edit 를 하나씩)")
    elif args.cmd == "script":
        script.run(ctx, args.episode)
    elif args.cmd == "visuals":
        visuals.run(ctx, args.episode)
    elif args.cmd == "voice":
        voice.run(ctx, args.episode)
    elif args.cmd == "edit":
        edit.run(ctx, args.episode)
    elif args.cmd == "make":
        for step in (script, visuals, voice, edit):
            step.run(ctx, args.episode)
    elif args.cmd == "review":
        if args.action == "list":
            review.list_pending(ctx)
        elif args.action == "show":
            review.show(ctx, args.episode, open_file=args.open)
        elif args.action == "approve":
            review.approve(ctx, args.episode, ai_label_confirmed=args.ai_label_confirmed)
        elif args.action == "reject":
            review.reject(ctx, args.episode, reason=args.reason)
    elif args.cmd == "upload":
        if args.due:
            upload.run_due(ctx)
        elif args.episode:
            upload.run(ctx, args.episode, at=args.at)
        else:
            raise StepError("회차 id 또는 --due 를 지정하세요")
    elif args.cmd == "status":
        cmd_status(ctx, args.episode)
    elif args.cmd == "unlock":
        ep = ctx.db.get(args.episode)
        if ep.status != Status.PUBLISHING.value:
            raise StepError(f"{ep.id} 는 업로드 중 상태가 아닙니다 (현재 {ep.status})")
        ctx.db.set_status(ep.id, Status.APPROVED)
        ctx.db.log(ep.id, "unlock", "ok", "publishing -> approved (manual)")
        print(f"[정리] {ep.id} 를 승인 상태로 되돌렸습니다")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    ctx = Context.create(force_mock=args.mock, force=args.force)
    try:
        dispatch(ctx, args)
        return 0
    except CostDeclined as e:
        print(f"[중단] {e}")
        return 2
    except (StepError, NotConfigured, ConfigError, KeyError, FileNotFoundError) as e:
        print(f"[오류] {e}")
        return 1
    finally:
        ctx.db.close()
