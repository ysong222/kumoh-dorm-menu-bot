"""기숙사 식단 알림 봇 실행 파일.

사용 예:
  python main.py --mode preview              # 오늘 중식+석식을 텔레그램으로 전송
  python main.py --mode lunch --dry-run      # 전송하지 않고 화면에 출력만
  python main.py --cron "0 2 * * 1-5"        # GitHub Actions가 넘겨준 cron으로 종류 결정
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from menu_parser import fetch_menu_html, parse_menu
from message import MODES, build_error_message, build_menu_message
from telegram_client import TelegramError, send_message

KST = ZoneInfo("Asia/Seoul")

# GitHub Actions의 cron은 UTC 기준입니다. KST = UTC + 9시간.
# 이 표는 .github/workflows/menu-notify.yml 의 cron과 똑같아야 하며,
# tests/test_schedule.py 가 둘이 일치하는지와 KST 변환이 맞는지 검사합니다.
CRON_TO_MODE = {
    "0 23 * * 0-4": "preview",  # UTC 일~목 23:00 = KST 월~금 08:00
    "0 2 * * 1-5": "lunch",  # UTC 월~금 02:00 = KST 월~금 11:00
    "30 7 * * 1-5": "dinner",  # UTC 월~금 07:30 = KST 월~금 16:30
}


def main() -> int:
    args = _parse_args()

    if args.mode:
        mode = args.mode
    elif args.cron in CRON_TO_MODE:
        mode = CRON_TO_MODE[args.cron]
    else:
        print(f"알 수 없는 cron입니다: {args.cron!r}. --mode 를 지정하세요.")
        return 2

    # 서버 시간대(UTC)가 아니라 한국 시간 기준의 "오늘"을 씁니다.
    today = args.date or datetime.now(KST).date()

    failed = False
    try:
        if args.html_file:
            html = Path(args.html_file).read_text(encoding="utf-8")
        else:
            html = fetch_menu_html()
        week = parse_menu(html, today)
        text = build_menu_message(mode, today, week)
    except Exception as error:  # 접속/파싱 실패는 물론 예상 못 한 오류도 알림으로 보냄
        failed = True
        text = build_error_message(mode, error)

    if args.dry_run:
        print(text)
    else:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            print("환경변수 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 가 필요합니다.")
            return 2
        try:
            send_message(text, token, chat_id)
        except TelegramError as error:
            print(error)
            return 1
        print("텔레그램 전송 완료")

    # 식단을 못 가져왔으면 실패로 끝내서 Actions 화면에도 빨간불이 뜨게 합니다.
    return 1 if failed else 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="기숙사 식단 텔레그램 알림")
    parser.add_argument("--mode", choices=sorted(MODES), help="알림 종류")
    parser.add_argument("--cron", default="", help="실행을 일으킨 cron 식 (mode가 없을 때 사용)")
    parser.add_argument(
        "--date", type=date.fromisoformat, help="테스트용: 오늘 대신 쓸 날짜 (예: 2026-11-13)"
    )
    parser.add_argument("--html-file", help="테스트용: 사이트 대신 읽을 HTML 파일")
    parser.add_argument("--dry-run", action="store_true", help="전송하지 않고 출력만")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
