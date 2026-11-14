"""인스타그램 릴스를 미리 올려 두고(prepare) 정해진 시간에 게시(publish)한다. 토큰 값은 출력하지 않는다.

    python scripts/ig_reel.py prepare ep003_runaway_snowball --thumb-ms 11200
    python scripts/ig_reel.py publish ep003_runaway_snowball [--not-after 2026-11-15T02:30]

읽는 파일: output/pepper_mint/<이름>.mp4, output/pepper_mint/epNNN_caption.txt
만드는 파일: epNNN_pending.json (prepare), epNNN_publish.json 과 epNNN_publish.log (publish)
인스타 API 에는 릴스 예약 기능이 없어서, publish 는 Windows 작업 스케줄러 같은 곳에서 시간에 맞춰 실행한다.
epNNN_publish.json 이 있으면 이미 게시한 것으로 보고 다시 올리지 않는다.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
load_dotenv(ROOT / ".env")
TOK = (os.getenv("INSTAGRAM_ACCESS_TOKEN") or "").strip()
UID = (os.getenv("INSTAGRAM_USER_ID") or "").strip()
G = "https://graph.facebook.com"
BASE = ROOT / "output" / "pepper_mint"

ap = argparse.ArgumentParser()
ap.add_argument("step", choices=["prepare", "publish"])
ap.add_argument("name", help="영상 파일 이름 (확장자 없이), 예: ep003_runaway_snowball")
ap.add_argument("--thumb-ms", type=int, default=0, help="표지로 쓸 장면의 위치 (밀리초)")
ap.add_argument("--not-after", default="", help="이 시각(로컬, ISO)을 넘겼으면 게시하지 않는다")
args = ap.parse_args()
ep = args.name.split("_")[0]
video, cap_file = BASE / f"{args.name}.mp4", BASE / f"{ep}_caption.txt"
pending, done, log_file = BASE / f"{ep}_pending.json", BASE / f"{ep}_publish.json", BASE / f"{ep}_publish.log"


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:
        print(line, flush=True)
    except Exception:  # 창 없이 실행되거나 콘솔이 글자를 못 찍는 경우
        pass


def call(url, data=None, headers=None, raw=None):
    body = raw if raw is not None else (urllib.parse.urlencode(data).encode() if data is not None else None)
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:  # 네트워크 문제. 주소(토큰 포함)는 남기지 않는다
        return 0, {"error": {"message": f"network: {type(e).__name__}"}}


def container_status(cid):
    _, st = call(f"{G}/{cid}?fields=status_code,status&access_token={TOK}")
    return st.get("status_code"), st


def prepare():
    """영상을 올려 게시 직전 상태(컨테이너)로 만든다. 컨테이너는 24시간 뒤 만료된다."""
    caption = cap_file.read_text(encoding="utf-8").strip()
    code, c = call(f"{G}/{UID}/media", data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                             "share_to_feed": "true", "thumb_offset": str(args.thumb_ms),
                                             "access_token": TOK})
    if code != 200 or "id" not in c:
        raise SystemExit(f"컨테이너 생성 실패 {code} {c}")
    cid, uri = c["id"], c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{c['id']}"
    data = video.read_bytes()
    code, up = call(uri, raw=data, headers={"Authorization": f"OAuth {TOK}", "offset": "0",
                                            "file_size": str(len(data)), "Content-Type": "application/octet-stream"})
    if code != 200 or not up.get("success", True):
        raise SystemExit(f"업로드 실패 {code} {up}")
    sc, st = None, {}
    for _ in range(60):
        time.sleep(5)
        sc, st = container_status(cid)
        if sc in ("FINISHED", "ERROR", "EXPIRED"):
            break
    if sc != "FINISHED":
        raise SystemExit(f"영상 처리가 끝나지 않음: {st}")
    pending.write_text(json.dumps({"container_id": cid, "created": f"{datetime.now():%Y-%m-%dT%H:%M:%S}",
                                   "thumb_ms": args.thumb_ms}, indent=2), encoding="utf-8")
    log(f"prepare: 컨테이너 {cid} 준비 완료 ({video.name}, {len(data) / 1e6:.1f} MB, 표지 {args.thumb_ms / 1000:.1f}초)")
    return cid


def record(cid, media_id):
    _, info = call(f"{G}/{media_id}?fields=permalink,media_product_type,timestamp&access_token={TOK}")
    rec = {"media_id": media_id, "container_id": cid,
           **{k: info.get(k) for k in ("permalink", "media_product_type", "timestamp")}}
    done.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    pending.unlink(missing_ok=True)
    log(f"publish: 게시 완료 {rec}")


def publish():
    if args.not_after and datetime.now() > datetime.fromisoformat(args.not_after):
        log(f"publish: {args.not_after} 을 넘겨 게시하지 않음")
        return 1
    cid = json.loads(pending.read_text(encoding="utf-8"))["container_id"] if pending.exists() else None
    for attempt in range(1, 7):
        sc, st = container_status(cid) if cid else (None, {})
        if sc == "PUBLISHED":  # 앞선 시도가 성공했는데 응답만 못 받은 경우
            _, m = call(f"{G}/{UID}/media?fields=id&limit=1&access_token={TOK}")
            record(cid, m["data"][0]["id"])
            return 0
        if sc in (None, "ERROR", "EXPIRED") and (cid is None or "error" not in st):
            log(f"publish: 준비된 컨테이너를 쓸 수 없음 ({sc}), 다시 올림")
            try:
                cid = prepare()
            except SystemExit as e:
                log(f"publish: 시도 {attempt} 다시 올리기 실패: {e}")
                time.sleep(30)
                continue
            sc = "FINISHED"
        if sc == "FINISHED":
            code, pub = call(f"{G}/{UID}/media_publish", data={"creation_id": cid, "access_token": TOK})
            if code == 200 and "id" in pub:
                record(cid, pub["id"])
                return 0
            log(f"publish: 시도 {attempt} 게시 실패 {code} {pub.get('error', {}).get('message')}")
        else:
            log(f"publish: 시도 {attempt} 상태 확인 실패 {st.get('error', {}).get('message', sc)}")
        time.sleep(30)
    log("publish: 6번 시도했지만 게시하지 못함")
    return 1


if not TOK or not UID:
    raise SystemExit(".env 에 INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ID 가 없음")
if done.exists():
    log(f"{args.step}: 이미 게시함 ({done.name}), 아무것도 하지 않음")
    raise SystemExit(0)
if not video.exists() or not cap_file.exists():
    raise SystemExit(f"파일 없음: {video.name} 또는 {cap_file.name}")
if args.step == "prepare":
    prepare()
else:
    sys.exit(publish())
