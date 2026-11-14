"""텔레그램 Bot API로 메시지를 보내는 모듈."""

from __future__ import annotations

import requests

MAX_MESSAGE_LENGTH = 4096  # 텔레그램 메시지 한 개의 최대 길이


class TelegramError(Exception):
    """텔레그램 전송 실패."""


def send_message(text: str, token: str, chat_id: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text[:MAX_MESSAGE_LENGTH]}

    try:
        response = requests.post(url, json=payload, timeout=30)
    except requests.RequestException as error:
        # 주의: requests의 에러 메시지에는 요청 URL이 들어가는데, 그 URL에 봇 토큰이
        # 포함돼 있습니다. 로그에 토큰이 찍히지 않도록 에러 종류만 남깁니다.
        raise TelegramError(f"텔레그램 접속 실패: {type(error).__name__}") from None

    if response.status_code != 200:
        # 텔레그램은 실패 이유를 JSON의 description에 담아 줍니다. (토큰은 들어 있지 않음)
        try:
            reason = response.json().get("description", "")
        except ValueError:
            reason = ""
        raise TelegramError(f"텔레그램 전송 실패: HTTP {response.status_code} {reason}")
