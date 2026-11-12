# AI Drama Contents

AI로 숏폼 드라마를 만들고, **사람이 검수해서 승인한 것만** 인스타그램 릴스에 올리는 파이프라인입니다.

- 1단계 (지금): 정지 이미지 + 내레이션 숏폼
- 2단계: 2D 캐릭터 애니메이션 (Kling / Seedance 등으로 컷 단위 영상 생성)
- 3단계: 실사풍 AI 드라마

대본은 처음부터 드라마 구조(회차 → 장면 → 컷, 대사/카메라/움직임 포함)로 만들기 때문에,
형식을 넓힐 때는 **이미지/영상 생성 단계(provider)만 바꾸면** 됩니다.

## 빠른 시작

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,ffmpeg]"     # ffmpeg 를 따로 설치했다면 ,ffmpeg 는 빼도 됩니다
Copy-Item .env.example .env        # API 키는 .env 에만. 절대 커밋하지 않습니다

pytest                              # 비용 0 으로 전체 흐름 테스트
```

API 키 없이(비용 0) 영상 1개를 끝까지 만들어 보기:

```powershell
studio --mock new --series sample --topic "영수증에 내일 날짜가 찍혀 있다"
studio --mock make sample-ep001          # 1~4단계: 대본 -> 이미지 -> 음성 -> 편집
studio review show sample-ep001 --open   # 5단계: 대본/캡션 확인, 영상 열기
studio review approve sample-ep001
studio --mock upload sample-ep001        # 6단계: (mock) 게시
studio status                            # 7단계: 상태/비용 기록
```

## 파이프라인

| 단계 | 명령 | 결과 | 상태 |
|---|---|---|---|
| 1. 대본 | `studio script <회차>` | `output/work/<회차>/script.json` | scripted |
| 2. 이미지 | `studio visuals <회차>` | `.../images/*.png` | visuals_done |
| 3. 음성 | `studio voice <회차>` | `.../audio/*.wav` | voiced |
| 4. 편집 | `studio edit <회차>` | `output/pending/<회차>.mp4` (1080x1920) | pending |
| 5. 검수 | `studio review approve/reject <회차>` | `output/approved/` | approved / rejected |
| 6. 업로드 | `studio upload <회차> [--at "2026-11-12 19:00"]` | `output/published/` | published |
| 7. 기록 | `studio status [<회차>]` | `output/studio.db` (SQLite) | - |

- 단계마다 따로 실행할 수 있고, `studio make <회차>` 는 1~4단계를 이어서 실행합니다.
- **사람의 창작 개입:** `script.json` 은 직접 고칠 수 있습니다. 고친 뒤 필요한 단계를 `--force` 로 다시 실행하세요.
- 이미 만든 이미지/음성은 다시 실행해도 새로 만들지 않습니다 (돈이 두 번 나가지 않음). 다시 만들려면 `--force`.
- 승인하지 않은 영상과 이미 게시한 영상은 업로드할 수 없습니다.
- 예약 게시: `--at` 으로 시각을 기록하고, `studio upload --due` 를 주기적으로 실행하면 시각이 지난 것만 게시합니다.

## 비용 확인

실제 유료 API를 쓰는 단계는 실행 전에 예상 비용 표를 보여 주고 `y` 를 입력해야 진행합니다.

- 1회 실행 상한: `config/settings.yaml` 의 `max_cost_per_run_usd` (넘으면 묻지 않고 중단)
- 단가표: `config/settings.yaml` 의 `pricing` (공식 가격표로 확인하지 않은 단가는 `*` 로 표시)
- mock 단계는 비용이 0 이라 묻지 않습니다.

## 실제 API로 바꾸기

`config/settings.yaml` 의 `providers` 에서 한 단계씩 바꿉니다.

| 단계 | 지금 | 실제 |
|---|---|---|
| llm | mock | `claude` (연결됨, `.env` 의 `ANTHROPIC_API_KEY` 필요) |
| visual | mock | `image_api` = Nano Banana 2.1 (연결됨, `GEMINI_API_KEY` 필요, 9:16 2K 장당 $0.05), 2단계에 `kling` / `seedance` |
| tts | mock | `elevenlabs` (구현됨, 실제 호출 미검증. 보이스 ID 를 시리즈/캐릭터 YAML 에 입력) |
| render | ffmpeg | ffmpeg 가 PATH 에 없으면 `pip install imageio-ffmpeg` 로 받은 ffmpeg 를 사용 |
| publish | mock | `instagram` (기존에 확인한 게시 코드를 옮겨 올 예정) |

## 새 시리즈 만들기

`series/sample/` 을 복사해 고칩니다.

- `series.yaml`: 세계관, 톤, 화풍(`visual_style`), 형식(`format`), 내레이터 보이스
- `characters/*.yaml`: 캐릭터 바이블. `appearance` 는 그 캐릭터가 나오는 모든 컷 프롬프트에 자동으로 붙어 일관성을 지킵니다.
  `reference_images` 에 캐릭터 기준 이미지(시리즈 폴더 기준 경로)를 넣으면 이미지 생성 때 함께 보내 얼굴을 맞춥니다 (컷당 최대 4장).
- 실사풍 AI 인물이 나오면 `ai_generated_realistic_people: true` → 승인할 때 AI 라벨 확인(`--ai-label-confirmed`)을 요구합니다.

## 폴더 구조

```
config/settings.yaml     provider 선택, 단가표, 비용 상한, 렌더 설정
series/<시리즈>/          시리즈/캐릭터 바이블 (사람이 쓰는 원작 설정)
src/studio/
  cli.py                 명령줄
  models.py              대본/시리즈 데이터 구조
  prompts.py             대본 생성 프롬프트
  cost.py  db.py         비용 확인, 상태 기록
  steps/                 1~6단계
  providers/             단계별 실제/가짜 구현 (교체 가능)
assets/bgm, assets/fonts 배경음악, 폰트 (저작권 확인된 것만)
output/                  작업물, pending/approved/published (커밋 안 함)
tests/                   mock 으로 전체 흐름 테스트
```
