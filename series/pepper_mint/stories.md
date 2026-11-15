# Pepper & Mint - 릴스용 스토리 (2026-11-14, 3판)

## 릴스용 공통 원칙
- 4화부터의 스토리 규칙은 docs/research/2026-11-14_ai_animation_shorts_100.md 의 '4화부터 적용할 규칙'을 따른다.
- **원테이크**: 처음부터 끝까지 컷 없이 한 장면으로 이어진다 (약 30초). 카메라는 고정된 정면 투샷.
  컷을 나눠 따로 만들어 이어 붙이는 방식은 쓰지 않는다 (1화에서 실패: 컷마다 끊기고 소품 상태가 되돌아감).
- **상태 유지**: 한번 바뀐 것(녹은 아이스크림, 언 코코아, 흘러내린 자국)은 다음 동작이 바꾸기 전까지 그대로 남는다.
  프롬프트에 시간 순서와 "되돌아가지 않는다"를 반드시 적는다.
- **첫 1초 훅**: 첫 화면부터 "어? 큰일이다" 하는 문제 상황으로 시작한다 (인사, 배경 소개 없음).
- **구조**: 문제 → 불/얼음 때문에 더 커짐 → 한 번 더 꼬임 → "펑" 김 → 귀여운 반전 → 서로 챙기는 순간.
  컷이 바뀔 때마다 새 사건이 생겨 끝까지 보게 만든다.
- **반복 장치**: 둘이 닿으면 "펑" 하고 김이 피어오른다. 매 회 이 장면을 기다리게 만든다.
- **무대사**: 표정, 몸짓, 효과음만으로 이해된다. 화면 글자 없음. 해외 누구나 아는 소재만 쓴다.
- **다시 보기(루프)**: 마지막 장면이 첫 장면과 자연스럽게 이어지면 반복 재생이 늘어난다.
- **썸네일(첫 프레임)**: 두 캐릭터 얼굴이 크게 보이고, 표정이 과장된 장면.

## 만드는 방법 (원테이크)
1. **첫 장면 이미지 1장만 만든다**: Nano Banana 2.1, 2K, 9:16, 캐릭터 참고 이미지 첨부. 사람이 보고 승인한다.
2. **영상은 그 한 장에서 시작해 끝까지 이어서 만든다**: 시간 순서대로 적은 프롬프트 하나를 쓴다.
   도구가 한 번에 15초까지만 만들면, 앞부분의 마지막 프레임을 그대로 뒷부분의 첫 장면으로 넣어 이어 만든다.
3. 장소, 빛, 카메라는 처음부터 끝까지 고정한다. 움직이는 것은 캐릭터와 소품뿐이다.

## 에피소드 후보

| # | 제목 | 한 줄 요약 | 성격 |
|---|---|---|---|
| 1 | Ice Cream Rescue | Pepper 손에서 녹는 아이스크림을 Mint가 얼려 구하지만 너무 얼려 버린다 | 웃김 + 뭉클 |
| 2 | Too Hot Cocoa | Mint 입김에 얼어 버린 코코아를 Pepper가 녹여 주다 끓어 넘치고, 김 구름이 휘핑크림이 된다 | 웃김 + 뭉클 |
| 3 | Bubble Bath | 차가운 목욕물을 Pepper 꼬리로 데우다 거품이 폭발해 둘이 양처럼 된다 | 웃김 |
| 4 | Popcorn Sneeze | Pepper의 재채기 불꽃에 팝콘이 폭발하고, Mint가 공중에서 얼려 눈송이처럼 떠다닌다 | 웃김 + 신기 |
| 5 | Mittens | 안을 때마다 김이 나자, Mint가 Pepper에게 벙어리장갑을 끼워 주고 꼭 안는다 | 뭉클 |
| 6 | Bedtime | 추운 밤 Mint가 떨자 Pepper가 꼬리 불꽃을 수면등처럼 켜 주고 함께 잠든다 | 뭉클 |

## 1화 "Ice Cream Rescue" (게시 완료 2026-11-14, @puffhatch)

> 게시본은 약 30초 원테이크 영상이다 (`output/pepper_mint/ep001_ice_cream_rescue.mp4`).
> 아래 7컷 구성은 처음 시도했다가 버린 안이다. 이야기 흐름 참고용으로만 남긴다.

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

## 2화 "Too Hot Cocoa" (게시 완료 2026-11-14, @puffhatch)

> 게시본은 30초 원테이크 영상이다 (`output/pepper_mint/ep002_too_hot_cocoa.mp4`, 2차 영상).
> 아래 계획과 다른 점: 김 구름이 화면을 다 가릴 만큼 크고 크림은 생기지 않는다. 구름이 걷히면 넘친 코코아 자국이 사라져 있다.
> 남은 결함: 15.4~16.2초에 Mint 한쪽 눈이 회색으로 비어 보이고, 21~24초에 하트 모양 김이 떠오른다.

1화와 반대로 이번에는 **Mint가 곤란해지고 Pepper가 도와주다 일을 키운다.**

### 시간 순서

| 시간 | 일어나는 일 | 소품 상태 | 소리 |
|---|---|---|---|
| 0~5초 | (훅) Mint가 김 나는 코코아 머그를 들어 한 모금 마시려는 순간, 입김이 닿아 코코아가 쩍 얼어 버린다. 머그를 뒤집어 흔들어도 안 나온다. 귀가 축 처진다 | 코코아 = 갈색 얼음 덩어리, 머그에 서리 | 쩍 어는 소리, 톡톡 |
| 5~9초 | 옆에서 자기 코코아를 마시던 Pepper가 보고, 머그를 내려놓고 가슴을 펴며 끄덕인다 | 그대로 얼어 있음 | 작은 "흠!" |
| 9~15초 | Pepper가 머그 바닥에 작은 불꽃을 "후~" 분다. 서리가 녹고 다시 김이 올라 Mint 얼굴이 밝아진다. 그런데 계속 불어서 코코아가 부글부글 끓어 넘친다 | 녹음 → 끓어 넘침, 머그 옆면에 코코아가 흘러내림 | 화르륵, 부글부글 |
| 15~19초 | Mint가 "앗 뜨거" 하며 머그를 이 손 저 손으로 옮기다 둘 사이 담요 위에 내려놓는다. 둘 다 당황해서 쳐다본다 | 계속 부글거림, 흘러내린 자국 그대로 | "힉", 부글부글 |
| 19~22초 | 둘이 동시에 머그를 향해 "후~" 분다. Pepper의 따뜻한 숨과 Mint의 찬 숨이 코코아 위에서 만나 "펑!" 하고 머그에서 김 구름이 솟는다. 구름은 머그 바로 위, 턱 아래 높이에 머문다 | 머그 위 김 구름 | 큰 "POOF" |
| 22~26초 | 김 구름이 줄어들며 머그 안으로 다시 내려앉아 **코코아 위 하얀 크림**이 된다. 부글거림이 멈추고 김만 잔잔히 난다 | 딱 좋은 코코아 + 크림 (머그 안), 옆면 흘러내린 자국은 그대로 | 폭신 "퐁" |
| 26~30초 | Mint가 머그를 들어 Pepper에게 먼저 내민다. 한 모금씩 조심히 마시고 웃는다 (얼굴은 깨끗하게). 머리를 맞대고 킥킥 웃는다. 마지막에 Mint가 만족해서 숨을 내쉬자 머그 가장자리에 서리가 살짝 낀다 (루프) | 머그에 서리 살짝 | 후루룩, 킥킥 |

- **반복 장치**: 불과 얼음이 만나면 "펑". 이번에는 둘의 숨이 코코아 위에서 만나고, 김 구름이 머그 안 크림이 된다.
- **주의 (1차 영상 실패)**: 볼이 닿아 김이 나게 했더니 구름이 머리 높이에 생겨 크림이 Mint 머리 위에 올라갔다.
  김은 반드시 소품(머그)에서 나오고 소품으로 돌아가게 적는다. 얼굴/머리에 붙는 것은 넣지 않는다.
- **썸네일**: 22~26초, 크림이 올라간 머그를 사이에 둔 두 얼굴.
- **계절**: 11~12월(추수감사절~크리스마스)에 맞는 소재.

### 첫 장면 이미지 (1장만 만든다)

```
Use the attached reference images of PEPPER (fluffy orange fox-like baby fire dragon boy, green eyes, plush
flame-tuft tail) and MINT (his little sister, same character model in snow-white fur with icy-blue ears,
wings and horns, sapphire-blue eyes, snowflake ice-crystal tail tip). Keep both designs exactly the same.
Front-facing medium two-shot, vertical 9:16: Pepper (left) and Mint (right) sit side by side on a cream and
soft-red plaid picnic blanket on a meadow, under a big tree with golden autumn leaves. Mint holds a big
sky-blue mug of steaming hot cocoa in both paws, just about to take a sip, smiling. Pepper sips from a small
orange mug. A wicker basket and a thermos softly blurred behind them, a few fallen leaves on the blanket,
warm low afternoon sunlight from the left. Cozy 3D animated family-film look, matte velvety textures (never
glossy or plastic), realistic soft fur, big expressive faces, gentle shallow depth of field. No text.
```

### 영상 프롬프트 (첫 장면 이미지 + 캐릭터 참고 이미지와 함께)

```
The first attached image is the exact first frame. Continue from it as ONE CONTINUOUS TAKE of 30 seconds:
a single unbroken shot, no cuts, no scene changes, no time skips. The camera is locked: the same front-facing
medium two-shot from start to end. Only the characters and the mug move.
Keep PEPPER (orange baby fire dragon, left) and MINT (white baby ice dragon, right) exactly on-model.
Their faces, noses, heads and fur stay completely clean and bare from start to end: nothing ever lands on them
or sticks to them. The only props are the two mugs and the cocoa.
Continuity rule: every change to the cocoa and the mug stays until the next action changes it. Frozen cocoa
stays frozen until the flame melts it. Cocoa that ran down the side of the mug stays there to the end.
Pepper's own orange mug stays on the blanket where he puts it.

The action flows in this order without interruption. Steps 1-3 fill the first half of the video, steps 4-7
the second half:
1) Mint lifts her big blue mug to take a sip. As her frosty breath touches it, the cocoa freezes solid with a
crackle: frost covers the mug, the steam stops. She blinks, turns the mug upside down and gives it a shake.
Nothing comes out. She turns it upright again and her ears droop.
2) Pepper notices, puts his own mug down on the blanket, puffs out his chest and gives a confident nod.
3) Pepper leans in and breathes a small gentle flame from his mouth under Mint's mug. The frost melts away,
the cocoa turns liquid and steams again, and Mint's face lights up. But he keeps going: the cocoa bubbles and
a little foam rises over the rim, with a few drips running down the side of the mug.
4) Mint squeaks and quickly sets the hot mug down on the blanket between them. It keeps bubbling a little.
Both stare at it, worried.
5) Both lean down toward the mug at the same moment and blow on it. Pepper's warm breath and Mint's frosty
breath meet right on the cocoa, and with a POOF a fluffy white cloud of steam bursts up out of the mug.
The cloud stays low between them, just above the mug and below their chins. They pull their heads back
in surprise.
6) The cloud shrinks and sinks back down into the blue mug, and settles there as a small soft swirl of white
cream on top of the cocoa, inside the mug. The bubbling has stopped: the cocoa is calm and gently steaming,
just right. Nothing from the cloud touches Pepper or Mint. Both blink at the mug, amazed.
7) Mint picks up the blue mug with both paws and offers Pepper the first sip. He takes a small careful sip and smiles.
Then she takes a small careful sip and smiles. Their faces stay clean. They giggle and lean their heads together. Mint lets out a happy sigh
and a little frost starts to creep along the rim of the mug.

Cozy 3D animated family-film look, matte velvety textures (never glossy or plastic), realistic soft fur,
bouncy squash-and-stretch acting, big expressive faces. Vertical 9:16.
No speech, no words, no music, no text on screen. Sound effects only: ice crackle, small fire whoosh,
bubbling, a tiny squeak, a big steam POOF, a soft plop, sips, baby-dragon giggles.
```

### 인스타그램 게시 문구 (영어, 안)

```
She froze it. He boiled it. Somehow… perfect. ☕🔥❄️

Pepper & Mint, baby dragon siblings · Ep. 2 "Too Hot Cocoa"

#babydragon #cutedragon #cuteanimation #aianimation #puffhatch
```

## 3화부터의 게시 기록

3화부터는 사용자가 Claude 앱에서 완성본을 만들어 왔고, 여기에는 프롬프트 없이 게시한 내용만 적는다.
위 "에피소드 후보" 표의 3~6번은 쓰지 않았다. 완성본, 캡션, 게시 기록은 `output/pepper_mint/epNNN_*`.

| 화 | 제목 | 게시 (한국 시간) | 내용 | 길이 |
|---|---|---|---|---|
| 3 | Runaway Snowball | 2026-11-15 02:00 (예약 게시) | 작은 눈덩이가 언덕 아래로 굴러가고 둘이 쫓아간다 | 30초 |
| 4 | Race Day | 2026-11-15 10:18 | 달리기 시합. Mint가 길을 얼리고 Pepper가 녹이며 반칙이 커지다, 김이 걷히면 달팽이가 먼저 결승 리본을 끊는다 | 35초 |
| 5 | Balloon Battle | 2026-11-15 17:00 (예약) | 빨간 풍선을 서로 가지려다 얼리고 녹이는 사이 풍선이 커져 둘이 떠오르고, "펑" 뒤에 달팽이가 풍선을 타고 날아간다 | 30초 |

- 4화부터 달팽이가 매번 화면 구석에 있다가 마지막 반전을 가져간다.
- 4화: 20~21초에 김 구름이 화면 전체를 약 1.5초 가리고, 그 사이 결승 리본이 나타난다.
