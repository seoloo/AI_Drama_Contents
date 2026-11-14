# 프로젝트 브리프: AI 숏폼 드라마 + 인스타그램 반자동 업로드

## 목표
AI로 숏폼 드라마를 만들어 인스타그램 릴스에 올린다. 최종 목표는 실사풍 AI 드라마 시리즈.
처음 목표는 **영상 1개를 끝까지 만들어서, 사람이 승인하면 인스타에 올라가는 것**.

## 정해진 원칙
- Python. API 키는 `.env` 에만 두고 절대 커밋하지 않는다.
- **반자동**: AI가 만들고, 사람이 확인해 승인한 것만 업로드한다 (플랫폼 정책 대응).
- **유료 API 호출 전에는 예상 비용을 보여 주고 확인을 받는다** (`cost.require_approval`). mock 은 비용 0.
- 단계별로 따로 실행/테스트할 수 있어야 한다. 이미 만든 결과물은 다시 돈을 쓰지 않도록 건너뛴다.
- 대본은 처음부터 드라마 구조(회차 → 장면 → 컷, 대사/카메라/움직임)로 만든다.
  형식을 넓힐 때는 visual provider 만 바꾼다 (image_api → kling/seedance).
- 캐릭터 일관성: `series/<id>/characters/*.yaml` 의 `appearance` 를 모든 컷 프롬프트에 붙인다 (`prompts.build_visual_prompt`).

## 단계 (src/studio/steps)
1 script(대본, Claude) → 2 visuals(이미지) → 3 voice(ElevenLabs) → 4 edit(FFmpeg, 1080x1920)
→ 5 review(사람 승인, output/pending → approved) → 6 upload(Instagram Graph API) → 7 기록(SQLite, db.py)

## 현재 상태 (2026-11-10)
- 뼈대 완료. 모든 단계 mock 으로 끝까지 동작, ffmpeg 렌더링 확인, pytest 20개 통과.
- llm=claude 구현됨 (claude-opus-5-5, 구조화 출력, refusal fallback). 실제 호출은 아직 안 함.
- tts=elevenlabs 구현됨, 실제 호출 미검증 (pcm_24000 → WAV).
- visual=image_api 구현됨 (2026-11-12): Nano Banana 2.1 (`gemini-nano-banana-2.1`), google-genai SDK 의
  `client.interactions.create`, 9:16 / 2K, 캐릭터 참고 이미지 최대 4장. 실제 호출 확인 (2K 장당 실측 ~$0.07~0.09, 사고 토큰 포함).
- 방향 전환 (2026-11-12): 드라마 대신 대사 없는 3D 캐릭터 숏폼 (해외 타겟, 한국 정서 배제).
  시리즈 `series/pepper_mint` (불·얼음 남매 아기 용 Pepper & Mint). 디자인 확정 (2026-11-13):
  Pepper = 2차 시안 10, Mint = Pepper 와 같은 모델의 흰 털 버전 (5차 2번 + 1번 색). 질감은 @antaryaan 같은
  무광 벨벳 + 실제 같은 털, 나중에 인형으로 만들기 쉬운 둥근 형태. 2K 기준 이미지 `series/pepper_mint/refs/*.jpg`.
- 영상 (2026-11-13 시험): Gemini API 의 Veo 3.1 은 2026-10-22 종료. 대체 모델 `gemini-omni-1.2-flash` 는
  v1beta 에서만 보임 (`http_options={"api_version": "v1beta"}`). `client.interactions.create` +
  `response_format={"type":"video","aspect_ratio":"9:16","resolution":"720p","duration":"15s"}`, 참고 이미지 최대 6장,
  3~15초, 24fps, 소리 포함. 720p 15초 실측 $1.06 (8초 $0.58). 아직 provider 로 연결 안 함 (스크립트로만 시험).
  다음: 영상 provider + 무음 형식(voice/자막 생략).
- 영상은 **원테이크**로 만든다 (2026-11-14 확정): 컷을 나눠 따로 만들고 이어 붙이면 컷마다 끊기고 소품 상태가
  되돌아간다 (7컷 시도 실패). 카메라 고정, 처음부터 끝까지 한 장면, 소품 상태(녹음/얼음)는 끝까지 유지.
- 1화 "Ice Cream Rescue" 게시 완료 (2026-11-14): 인스타 계정 @puffhatch, 약 30초 원테이크 영상 (사용자가 직접 만든 완성본).
  완성본/캡션/게시 기록은 `output/pepper_mint/ep001_*`, 시험 영상은 `output/test/pepper_mint/`.
- 2화 "Too Hot Cocoa" 게시 완료 (2026-11-14). 3화 "Runaway Snowball" 은 2026-11-15 02:00 (한국 시간) 게시 예약.
  영상은 사용자가 Claude 앱(힉스필드 연결)에서 만들고, 여기서는 프롬프트 준비, 확인, 게시를 맡는다.
  해시태그는 게시물당 5개까지: `#babydragon #cutedragon #cuteanimation #aianimation #puffhatch`.
- 4화부터의 스토리 규칙은 `docs/research/2026-11-14_ai_animation_shorts_100.md` 의 "4화부터 적용할 규칙"을 따른다.
- publish=instagram 은 아직 provider 로 연결 안 함. 게시는 Graph API resumable upload 로 확인됨
  (`/{ig-id}/media` 에 `media_type=REELS&upload_type=resumable` → 돌려받은 `uri` 로 파일 전송 → `media_publish`).
  "AI 정보" 라벨과 프로필 소개글은 API 로 못 바꾸고 앱에서 직접 설정.
- 예약 게시 (2026-11-14): 인스타 API 에는 릴스 예약이 없다. `scripts/ig_reel.py prepare <이름> --thumb-ms N` 으로
  영상을 미리 올려 두고(24시간 유효), Windows 작업 스케줄러의 1회용 작업이 정해진 시간에
  `scripts/ig_reel.py publish <이름> --not-after <시각>` 을 실행한다. PC 가 켜져 있고 로그인된 상태여야 한다.
  결과는 `output/pepper_mint/epNNN_publish.json` 과 `epNNN_publish.log`.

## 단가 (config/settings.yaml 의 pricing)
- Claude (공식, 2026-11): Opus 5.5 $4/$20, Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50 (100만 토큰당 입력/출력)
- 이미지 (Google 공식, 2026-11): Nano Banana 2.1 1K $0.0336 / 2K $0.0504 / 4K $0.113 (입력 $1.50/1M),
  Nano Banana 2 1K $0.067 / 2K $0.101. 무료 사용량 없음, Batch 는 반값. 회당 9장 2K ≈ $0.45
- ElevenLabs 1천자당 ~$0.08 → 제3자 자료, 공식 가격 확인 필요
- 영상(2단계 이후, 미확인): Kling 3.0 초당 $0.084~0.168, Seedance 2.0 $0.15~0.37, Runway Gen-4.5 ~$0.12
- 예상: 이미지+내레이션 60초 회당 ~$0.6 / 2D 애니 $2~8 / 실사풍 90초 1화 $30~100

## 플랫폼 정책 메모
- 인스타: 실사처럼 보이는 AI 인물 계정은 "AI 생성" 라벨 필요 (`ai_generated_realistic_people` 로 승인 시 확인 강제).
  API 게시는 프로페셔널 계정 + 연결된 페이스북 페이지 + 게시 권한 필요.
  24시간 게시 한도는 문서마다 50/100 → `content_publishing_limit` 으로 실제 확인 (publishing_limit()).
  릴스 예약 게시는 자체 스케줄(`upload --at` + `upload --due`)로 처리.
- 유튜브(나중): 템플릿으로 찍어 낸 반복 영상은 "진정성 없는 콘텐츠"로 수익 창출 불가, 채널 단위 판단.
  사람의 창작 개입이 필요 → script.json 직접 수정/검수 과정을 유지. API 업로드는 심사 전 비공개 제한 가능성 확인 필요.

## 확장 후보 (2단계 이후, 미확인 정보 포함)
- Kling 3.0 (캐릭터 일관성, 여러 장면 이어 만들기), Seedance 2.0, Runway Gen-4.5
- Veo 3.1 Gemini API 종료 확인됨 (2026-10-22) → Gemini Omni 1.2 Flash 사용 (영상 출력 $12/1M tok, 720p 약 $0.07/초)

## 개발 메모
- 가상환경: `.venv` (Python 3.14). `pip install -e ".[dev,ffmpeg]"`
- 테스트: `pytest` (mock + ffmpeg 렌더링). 명령: `studio --help`
- 새 provider 는 `providers/base.py` 인터페이스를 지키고 `create()` 에 등록.
