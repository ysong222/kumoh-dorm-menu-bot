# CLAUDE.md

금오공대 오름관3동 식단을 텔레그램으로 알려주는 봇. 구조와 사용법은 README.md 참고.

## 사용자

- Git/GitHub를 배우는 중인 컴퓨터공학과 1학년. 코드와 Git 작업을 할 때 무엇을 왜 하는지 한국어로 설명한다.
- 코드 주석, 커밋 메시지, PR, 문서는 한국어로 쓴다.

## 작업 규칙

- main에 직접 push하지 않는다. 브랜치에서 작업하고 PR로 올린다. (PR 리뷰 연습 목적)
- 커밋은 단계별로 작게 나눈다. 한 커밋에 한 가지 변경.
- 텔레그램 토큰과 챗 ID는 코드, 로그, 커밋, PR에 절대 적지 않는다.
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 환경변수(GitHub Secrets)로만 받는다.
- 텔레그램 API URL에는 토큰이 들어 있다. `requests` 예외 메시지를 그대로 출력하면 토큰이 로그에 남으므로
  `telegram_client.py`처럼 에러 종류만 남긴다.
- 의존성은 `requests`, `beautifulsoup4`만 쓴다. 테스트는 표준 라이브러리 `unittest`.

## 검증

코드를 바꾸면 push 전에 실행한다.

```bash
python -m unittest discover -s tests -t .
python main.py --mode preview --date 2026-11-13 --html-file tests/fixtures/menu_sample.html --dry-run
```

## 알아둘 것

- Claude 클라우드 세션에서는 기본 환경(Default)이면 `dorm.kumoh.ac.kr` 접속이 막혀 있다.
  이 주소를 허용한 `kumoh-dorm-menu-bot` 환경에서는 `python main.py --mode preview --dry-run`으로 실제 페이지를 확인할 수 있다.
- 식단 페이지는 `?mode=menuList&srDt=YYYY-MM-DD`로 그 날짜가 속한 주(월~일)의 표를 준다.
  식단이 아직 등록되지 않은 주는 표 본문이 `<td colspan="7">등록된 메뉴가 없습니다.</td>` 한 칸뿐이다.
- 파서 동작은 `tests/fixtures/menu_sample.html`(실제 페이지에서 복사한 표)로 검증한다.
  사이트 구조가 바뀌면 이 샘플부터 새로 받아서 교체한다.
- 날짜는 항상 한국 시간(`Asia/Seoul`) 기준으로 계산한다. Actions 러너의 시간대는 UTC다.
- 오늘 칸은 표의 위치가 아니라 헤더의 날짜(`월(11.09)`)로 찾는다. 식단표는 주 단위로 갱신된다.
- cron은 UTC다. `.github/workflows/menu-notify.yml`의 cron과 `main.py`의 `CRON_TO_MODE`는 항상 같아야 하고,
  `tests/test_schedule.py`가 일치 여부와 KST 변환을 검사한다.
- GitHub 예약 실행은 몇 시간씩 늦거나 빠질 수 있다(실제로 16:30 → 다음 날 01:58). cron은 매시 :00/:30을 피하고,
  `main.py`의 `check_schedule`이 예정 시각~마감(`SEND_DEADLINE`) 밖의 예약 실행은 보내지 않는다.
- 메뉴의 `*`는 소스를 잇는 표시다(`햄구이*케찹`). 돈육 표시로 해석하지 않고 원문 그대로 보여준다.
- 알림은 평일만. 미운영/메뉴 없음/식단 미등록/접속·파싱 실패는 모두 텔레그램으로 알린다.
