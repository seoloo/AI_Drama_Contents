# Pepper & Mint - 릴스용 스토리 (2026-11-13, 2판)

## 릴스용 공통 원칙
- **품질이 먼저, 길이는 자유**: 한 번에 긴 영상을 뽑지 않고, **컷 하나에 동작 하나**(5~8초)로 나눠 만든 뒤 이어 붙인다.
  AI 영상은 한 클립에 사건이 많을수록 캐릭터가 뭉개지고 동작이 어색해진다. 컷을 나누면 이상한 컷만 다시 만들면 된다.
- **첫 1초 훅**: 첫 화면부터 "어? 큰일이다" 하는 문제 상황으로 시작한다 (인사, 배경 소개 없음).
- **구조**: 문제 → 불/얼음 때문에 더 커짐 → 한 번 더 꼬임 → "펑" 김 → 귀여운 반전 → 서로 챙기는 순간.
  컷이 바뀔 때마다 새 사건이 생겨 끝까지 보게 만든다.
- **반복 장치**: 둘이 닿으면 "펑" 하고 김이 피어오른다. 매 회 이 장면을 기다리게 만든다.
- **무대사**: 표정, 몸짓, 효과음만으로 이해된다. 화면 글자 없음. 해외 누구나 아는 소재만 쓴다.
- **다시 보기(루프)**: 마지막 장면이 첫 장면과 자연스럽게 이어지면 반복 재생이 늘어난다.
- **썸네일(첫 프레임)**: 두 캐릭터 얼굴이 크게 보이고, 표정이 과장된 장면.

## 컷이 이어져 보이게 만드는 방법
1. **장소, 빛, 소품을 고정한다**: 모든 컷 프롬프트 앞에 아래 "공통 설정"을 그대로 붙인다.
2. **컷마다 첫 장면 이미지(키프레임)를 먼저 만든다**: Nano Banana 2.1, 2K, 9:16, 캐릭터 참고 이미지 첨부.
   사람이 키프레임을 보고 승인한 뒤에만 영상으로 만든다 (영상이 이미지보다 훨씬 비싸다).
3. **동작이 바로 이어지는 컷**(4→5→6→7)은 앞 컷의 마지막 프레임을 다음 컷의 시작 참고 이미지로 쓴다.
4. 컷별 영상을 FFmpeg 로 이어 붙이고, 컷 사이 소리를 짧게 겹쳐 끊김을 없앤다.

## 에피소드 후보

| # | 제목 | 한 줄 요약 | 성격 |
|---|---|---|---|
| 1 | Ice Cream Rescue | Pepper 손에서 녹는 아이스크림을 Mint가 얼려 구하지만 너무 얼려 버린다 | 웃김 + 뭉클 |
| 2 | Too Hot Cocoa | Pepper가 데운 코코아가 너무 뜨거워 Mint가 식혀 주고, 둘이 마시멜로 수염을 단다 | 뭉클 |
| 3 | Bubble Bath | 차가운 목욕물을 Pepper 꼬리로 데우다 거품이 폭발해 둘이 양처럼 된다 | 웃김 |
| 4 | Popcorn Sneeze | Pepper의 재채기 불꽃에 팝콘이 폭발하고, Mint가 공중에서 얼려 눈송이처럼 떠다닌다 | 웃김 + 신기 |
| 5 | Mittens | 안을 때마다 김이 나자, Mint가 Pepper에게 벙어리장갑을 끼워 주고 꼭 안는다 | 뭉클 |
| 6 | Bedtime | 추운 밤 Mint가 떨자 Pepper가 꼬리 불꽃을 수면등처럼 켜 주고 함께 잠든다 | 뭉클 |

## 1화 "Ice Cream Rescue" (7컷, 약 43초, 9:16)

### 컷 구성

| 컷 | 시간 | 길이 | 장면 (동작 하나) | 카메라 | 소리 |
|---|---|---|---|---|---|
| 1 | 0:00~0:06 | 6초 | (훅) Pepper가 큰 와플콘(위 딸기, 아래 바닐라)을 두 앞발로 들고 신나게 핥는다. 녹은 방울이 발에 뚝 떨어지고, 눈이 동그래진다 | 얼굴 클로즈업, 천천히 다가감 | 뚝, 작은 "힉" |
| 2 | 0:06~0:12 | 6초 | 식히려고 "후~" 부는데 작은 불꽃이 나가 위 덩어리가 주르륵 미끄러진다. 콘을 돌리며 허둥지둥 핥는다 | 가슴 위까지, 살짝 흔들림 | 화르륵, 후루룩 |
| 3 | 0:12~0:17 | 5초 | Mint가 오른쪽에서 통통 뛰어 들어와 상황을 보고, 가슴을 펴며 "내가 할게" 하듯 끄덕인다 | 둘 다 보이는 중간 샷 | 톡톡 발소리 |
| 4 | 0:17~0:24 | 7초 | Mint가 반짝이는 서리 입김을 불자 콘이 얼어붙는다. 너무 세게 불어 아이스크림이 Pepper 머리보다 큰 반짝이는 얼음 덩어리가 된다. 둘 다 입이 떡 | 옆에서 보다가 뒤로 빠짐 | 쉬익, 쩍쩍 얼음 |
| 5 | 0:24~0:30 | 6초 | Pepper가 얼음을 핥다가 혀가 쩍 달라붙는다. 당기면서 작은 날개를 파닥이고 다리를 버둥거린다 | Pepper 얼굴 클로즈업 | "쩍!", 끙끙 |
| 6 | 0:30~0:35 | 5초 | Mint가 뒤에서 Pepper를 안아 끌어당기다 둘의 볼이 꾹 붙는다. "펑!" 큰 김 구름이 화면을 가린다 | 둘 클로즈업 → 김으로 화면 가득 | 톡, 큰 "POOF" |
| 7 | 0:35~0:43 | 8초 | 김이 걷히면 혀는 떨어졌고, 아이스크림은 딱 먹기 좋은 소프트아이스크림이 되어 있다. Pepper가 콘을 Mint에게 먼저 내밀고, 둘이 한 입씩 먹으며 킥킥 웃는다 (코끝에 아이스크림). 콘에서 다시 한 방울이 흐른다 (루프) | 둘 얼굴 따뜻한 클로즈업 | 킥킥, 뚝 |

- **총 길이**: 약 43초 (컷별 길이는 만들어 보고 1~2초씩 다듬는다. 최종 40~45초 예상)
- **루프**: 7컷 마지막의 흐르는 방울이 1컷의 녹는 방울로 이어진다.
- **썸네일**: 1컷 마지막, 녹는 아이스크림을 든 Pepper의 놀란 얼굴.

### 공통 설정 (모든 컷 프롬프트 앞에 붙인다, 영어)

```
Use the attached reference images of PEPPER (fluffy orange fox-like baby fire dragon boy, green eyes, plush
flame-tuft tail) and MINT (his little sister, same character model in snow-white fur with icy-blue ears,
wings and horns, sapphire-blue eyes, ice-crystal tail tip). Keep both designs exactly the same.
Same place in every shot: a small sunny meadow with soft green grass and tiny white flowers, a pastel wooden
ice-cream cart with a striped awning softly blurred in the background, warm late-afternoon sunlight from the left.
Prop: one big waffle cone with a pink strawberry scoop on top of a vanilla scoop.
Cozy 3D animated family-film look, matte velvety textures (never glossy or plastic), realistic soft fur,
bouncy squash-and-stretch acting, big expressive faces, gentle shallow depth of field. Vertical 9:16.
One clear action only. No speech, no music, no text on screen.
```

### 컷별 프롬프트 (공통 설정 뒤에 붙인다)

```
SHOT 1 (6s): Close-up of Pepper happily licking the big ice cream cone he holds in both front paws. A melted drip
runs down the cone onto his paw; he notices it and his eyes go wide. Slow push-in.
Sound: soft drip, tiny surprised squeak.

SHOT 2 (6s): Pepper blows on the ice cream to cool it, but a tiny puff of orange flame comes out; the top
strawberry scoop slumps and starts sliding. He spins the cone and licks frantically to save it.
Sound: tiny fire whoosh, quick slurps.

SHOT 3 (5s): Mint trots in from the right, sees the melting mess, puffs out her fluffy chest and gives a
confident little nod, like "I've got this". Medium shot of both.
Sound: soft paw patter.

SHOT 4 (7s): Mint blows a sparkly frosty breath at the cone. Frost spreads and the ice cream freezes way too much,
growing into a big sparkling block of ice bigger than Pepper's head, the scoops visible inside. Both stare with
their mouths open. Side view, camera pulls back to reveal the size.
Sound: frosty whoosh, ice crackle.

SHOT 5 (6s): Pepper licks the ice block and his tongue sticks to it. He tugs back, tiny wings flapping and little
legs wiggling, eyes squeezed shut. Close-up on Pepper.
Sound: sticky "thwip", muffled whine.

SHOT 6 (5s): Mint hugs Pepper from behind and pulls; their cheeks squish together and a huge fluffy cartoon cloud
of white steam bursts with a big POOF, filling the frame.
Sound: tiny boop, big steam POOF.

SHOT 7 (8s): The steam clears: Pepper's tongue is free and the ice cream has become a perfect soft-serve swirl.
Pepper looks at it, then offers it to Mint first. She takes a bite, he takes a bite, and they giggle with little
ice cream dots on their noses. A single drip starts to run down the cone. Warm close-up of both faces.
Sound: baby-dragon giggles, soft drip.
```

- 참고 이미지: `refs/pair.jpg`, `refs/pepper_front.jpg`, `refs/mint_front.jpg` (+ 측면 2장) + 그 컷의 키프레임
- 모델: Gemini Omni 1.2 Flash (컷당 15초 이하, 720p) 또는 힉스필드 Seedance 2.5 (크레딧이 생기면)

### 예상 비용 (1화)
- 키프레임 7장 (Nano Banana 2.1, 2K): 약 $0.6
- 영상 43초 (Gemini Omni, 720p 약 $0.07/초): 한 번씩이면 약 $3.0, 일부 컷을 다시 만들면 $4.5~6
- 참고: 힉스필드 Seedance 2.5 는 초당 7 크레딧 → 43초 약 300 크레딧 (현재 크레딧 0)

### 인스타그램 게시 문구 (영어, 안)
- 캡션: `He melts it. She saves it. Teamwork? 🍦🔥❄️ #PepperAndMint`
- 해시태그: `#babydragon #cuteanimation #3danimation #siblings #icecream #aianimation`
- AI 고지: 인스타의 "AI 정보" 라벨을 켠다 (실사 인물은 아니지만 AI 생성 영상임을 밝힌다).
