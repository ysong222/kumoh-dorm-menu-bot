# kumoh-dorm-menu-bot

금오공대 오름관3동 기숙사 식단을 평일마다 텔레그램으로 알려주는 봇입니다.
GitHub Actions가 정해진 시간에 [학교 식단 페이지](https://dorm.kumoh.ac.kr/dorm/restaurant_menu03.do)를 읽어서 메시지를 보냅니다.

## 알림 시간

평일(월~금)에만 보냅니다. GitHub Actions의 cron은 **UTC 기준**이라 한국 시간(KST = UTC + 9시간)에서 9시간을 빼서 적습니다.

| 한국 시간 (KST) | 내용 | cron (UTC) | UTC로 읽으면 |
|---|---|---|---|
| 월~금 08:00 | 오늘 중식 + 석식 미리보기 | `0 23 * * 0-4` | 일~목 23:00 |
| 월~금 11:00 | 오늘 중식 (11:30~13:30) | `0 2 * * 1-5` | 월~금 02:00 |
| 월~금 16:30 | 오늘 석식 (17:00~19:00) | `30 7 * * 1-5` | 월~금 07:30 |

08:00 알림만 요일이 `0-4`(일~목)인 이유: KST 월요일 08:00은 UTC로는 **전날인 일요일** 23:00이기 때문입니다.
이 변환이 맞는지는 `tests/test_schedule.py`가 검사합니다.

알아둘 점:

- GitHub의 예약 실행은 정시에 시작된다는 보장이 없습니다. 몇 분에서 길게는 수십 분 늦을 수 있습니다.
- 예약 실행은 **기본 브랜치(main)에 있는 워크플로만** 동작합니다. PR을 merge한 뒤부터 알림이 옵니다.
- 공개 레포는 60일 동안 활동이 없으면 GitHub가 예약 실행을 자동으로 끕니다. Actions 탭에서 다시 켤 수 있습니다.

## 메시지 예시

```
🍽 오늘의 식단 미리보기
11월 13일(금) · 오름관3동

[중식] 11:30~13:30
· 청양풍볶음면
· 맑은우동국물
· 갈비만두찜*간장

[석식] 17:00~19:00
· 참치김치찌개
· 치킨가라아게*머스타드S
```

- 칸에 메뉴 대신 "운영 없음" 같은 문구가 있으면 그 문구를 그대로 보냅니다.
- 칸이 비어 있으면 "메뉴 정보가 없어요."라고 보냅니다.
- 식단표에 오늘 날짜가 없으면(새 주 식단이 아직 안 올라온 경우) 그렇게 알려줍니다.
- 사이트 접속이나 해석에 실패하면 에러 내용을 텔레그램으로 보내고, Actions 실행도 실패로 표시됩니다.
- 메뉴의 `*`는 원문 그대로 보여줍니다. (`햄구이*케찹`처럼 곁들이는 소스를 잇는 표시로 쓰입니다.)

## 구조

```
.
├── main.py                  # 실행 파일: 종류 결정 → 가져오기 → 메시지 만들기 → 전송
├── menu_parser.py           # 식단 페이지 접속(fetch)과 HTML 해석(parse)
├── message.py               # 텔레그램 메시지 문자열 만들기
├── telegram_client.py       # 텔레그램 Bot API 전송
├── check_connection.py      # 학교 사이트 접속 테스트용 스크립트
├── requirements.txt         # 필요한 라이브러리
├── tests/
│   ├── fixtures/menu_sample.html   # 실제 식단표 HTML 샘플
│   ├── test_menu_parser.py
│   ├── test_message.py
│   └── test_schedule.py     # cron(UTC) ↔ KST 변환 검증
└── .github/workflows/
    ├── menu-notify.yml      # 식단 알림 (schedule + 수동 실행)
    └── connection-test.yml  # 학교 사이트 접속 테스트 (PR + 수동 실행)
```

실행 흐름:

1. `menu-notify.yml`이 cron 시간에 `python main.py --cron "<cron 식>"`을 실행합니다.
2. `main.py`가 cron 식을 보고 알림 종류(`preview` / `lunch` / `dinner`)를 정합니다.
3. `menu_parser.py`가 식단 페이지를 읽어 `{날짜: {끼니: 메뉴}}`로 바꿉니다.
4. `message.py`가 한국 시간 기준 오늘 날짜의 메뉴로 메시지를 만듭니다.
5. `telegram_client.py`가 메시지를 보냅니다.

## 설정 방법

### 1. 텔레그램 봇 준비

1. 텔레그램에서 [@BotFather](https://t.me/BotFather)에게 `/newbot`을 보내 봇을 만들고 **토큰**을 받습니다.
2. 만든 봇과의 대화방에서 아무 메시지나 하나 보냅니다. (봇은 먼저 말을 건 사람에게만 보낼 수 있습니다.)
3. 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates`를 열어 `chat` 안의 `id` 값(**챗 ID**)을 확인합니다.

### 2. GitHub Secrets 등록

레포의 **Settings → Secrets and variables → Actions → New repository secret**에서 두 개를 등록합니다.

| 이름 | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather에게 받은 토큰 |
| `TELEGRAM_CHAT_ID` | 메시지를 받을 챗 ID |

토큰과 챗 ID는 코드, 커밋, 이슈, PR 어디에도 직접 적지 않습니다.

### 3. 수동 실행으로 확인

**Actions 탭 → 식단 알림 → Run workflow**에서 알림 종류를 골라 실행하면 바로 메시지가 옵니다.

## 로컬에서 실행하기

```bash
pip install -r requirements.txt
```

전송하지 않고 메시지만 확인:

```bash
python main.py --mode preview --dry-run
```

사이트 접속 없이 샘플 HTML로 확인:

```bash
python main.py --mode preview --date 2026-11-13 --html-file tests/fixtures/menu_sample.html --dry-run
```

실제로 전송 (토큰은 환경변수로만 전달):

```bash
TELEGRAM_BOT_TOKEN="..." TELEGRAM_CHAT_ID="..." python main.py --mode lunch
```

테스트 실행:

```bash
python -m unittest discover -s tests -t .
```

## 알림 시간을 바꾸려면

두 군데를 **똑같이** 고쳐야 합니다. 다르면 `tests/test_schedule.py`가 실패합니다.

1. `.github/workflows/menu-notify.yml`의 `cron`
2. `main.py`의 `CRON_TO_MODE`

원하는 한국 시간이 달라지면 `tests/test_schedule.py`의 `EXPECTED_KST_TIME`도 함께 고칩니다.
