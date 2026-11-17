"""학교 기숙사 사이트 접속 테스트 스크립트.

GitHub Actions(해외 서버)에서 학교 사이트에 접속이 되는지,
그리고 식단표 HTML이 어떤 구조인지 확인하기 위한 용도입니다.

실행: python check_connection.py
"""

import sys

import requests
from bs4 import BeautifulSoup

URL = "https://dorm.kumoh.ac.kr/dorm/restaurant_menu03.do"

# 일부 사이트는 브라우저가 아닌 요청을 차단하므로 브라우저처럼 보이는 헤더를 붙입니다.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def main() -> int:
    print(f"요청 URL: {URL}")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
    except requests.RequestException as error:
        # 접속 자체가 안 되는 경우 (타임아웃, 연결 거부, 인증서 오류 등)
        print(f"접속 실패: {type(error).__name__}: {error}")
        return 1

    print(f"상태 코드: {response.status_code}")
    print(f"응답 인코딩: {response.encoding} (추정: {response.apparent_encoding})")
    print(f"응답 크기: {len(response.content)} bytes")

    if response.status_code != 200:
        print("200이 아닌 응답입니다. 본문 앞부분:")
        print(response.text[:1000])
        return 1

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    print(f"table 개수: {len(tables)}")

    if not tables:
        print("표를 찾지 못했습니다. 본문 앞부분:")
        print(response.text[:3000])
        return 1

    # 파서를 만들 때 참고하려고 표의 HTML 원본을 그대로 출력합니다.
    for index, table in enumerate(tables):
        print(f"\n===== table #{index} 원본 HTML =====")
        print(table.prettify())

    print("\n접속 성공!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
