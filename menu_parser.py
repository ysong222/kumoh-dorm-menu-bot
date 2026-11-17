"""기숙사 식단 페이지를 가져와서(fetch) 파이썬 자료구조로 바꾸는(parse) 모듈.

식단표 HTML 구조 (tests/fixtures/menu_sample.html 참고):
- <thead>의 <th> 7개: "월(11.09)" 처럼 요일과 날짜가 들어 있음
- <tbody>의 <tr> 한 줄이 끼니 하나(중식 줄, 석식 줄)
- 각 <td> 안에 <p>중식</p> 과 <li>메뉴</li> 목록
"""

from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

import requests
from bs4 import BeautifulSoup

MENU_URL = "https://dorm.kumoh.ac.kr/dorm/restaurant_menu03.do"

# 일부 사이트는 브라우저가 아닌 요청을 차단하므로 브라우저처럼 보이는 헤더를 붙입니다.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}

# "월(11.09)" 에서 요일, 월, 일을 뽑아내는 정규식
HEADER_PATTERN = re.compile(r"([월화수목금토일])\s*\(\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\)")

MEAL_LABELS = ("조식", "중식", "석식")


class MenuError(Exception):
    """식단을 가져오거나 해석하다가 생긴 문제."""


class MenuFetchError(MenuError):
    """사이트 접속 실패."""


class MenuParseError(MenuError):
    """HTML 구조가 예상과 달라서 해석 실패."""


@dataclass
class Meal:
    """한 끼 식단.

    items: 메뉴 이름 목록
    note:  메뉴 목록이 없을 때 칸에 적혀 있던 문구 (예: "운영 없음")
    """

    items: list[str] = field(default_factory=list)
    note: str = ""


# {날짜: {"중식": Meal, "석식": Meal}} 형태
WeekMenu = dict[date, dict[str, Meal]]


def fetch_menu_html(day: date, url: str = MENU_URL, attempts: int = 3) -> str:
    """day가 속한 주의 식단 페이지 HTML을 가져옵니다.

    사이트는 srDt 파라미터의 날짜가 속한 주(월~일)의 표를 보여줍니다.
    일시적 오류에 대비해 몇 번 재시도합니다.
    """
    params = {"mode": "menuList", "srDt": day.isoformat()}
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url, params=params, headers=REQUEST_HEADERS, timeout=30
            )
            response.raise_for_status()  # 404, 500 같은 응답이면 예외 발생
        except requests.RequestException as error:
            last_error = error
            if attempt < attempts:
                time.sleep(5)
            continue

        # 서버가 인코딩을 알려주지 않으면 한글이 깨질 수 있어서 내용으로 추정합니다.
        if "charset" not in response.headers.get("Content-Type", "").lower():
            response.encoding = response.apparent_encoding
        return response.text

    raise MenuFetchError(
        f"식단 페이지 접속 실패 ({attempts}회 시도): "
        f"{type(last_error).__name__}: {last_error}"
    )


def parse_menu(html: str, today: date) -> WeekMenu:
    """식단표 HTML을 {날짜: {끼니: Meal}} 로 바꿉니다.

    today는 연도를 정하는 데 씁니다. 표에는 "11.09"처럼 월/일만 있기 때문입니다.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = _find_menu_table(soup)
    dates = _parse_header_dates(table, today)

    week: WeekMenu = {day: {} for day in dates}
    row_count = 0

    for row in table.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue  # 헤더 줄 등 td가 없는 줄은 건너뜀
        if len(cells) == 1 and cells[0].get("colspan"):
            continue  # 표 전체를 차지하는 안내 문구 줄은 아래에서 따로 처리
        if len(cells) != len(dates):
            raise MenuParseError(
                f"식단 줄의 칸 수({len(cells)})가 날짜 수({len(dates)})와 다릅니다."
            )

        # 칸마다 "중식"/"석식" 표시가 있지만, 미운영 칸에는 없을 수도 있으니
        # 그 줄에서 가장 많이 나온 표시를 줄 전체의 끼니로 봅니다.
        labels = [_cell_label(cell) for cell in cells]
        found = [label for label in labels if label]
        if not found:
            raise MenuParseError("식단 줄에서 중식/석식 구분을 찾지 못했습니다.")
        row_label = Counter(found).most_common(1)[0][0]

        for day, cell in zip(dates, cells):
            week[day][row_label] = _parse_cell(cell, row_label)
        row_count += 1

    if row_count == 0:
        # 식단이 아직 안 올라온 주는 표 본문에 줄(<tr>) 없이
        # "등록된 메뉴가 없습니다." 문구만 들어 있습니다.
        body = table.find("tbody")
        notice = " ".join(body.get_text(" ", strip=True).split()) if body else ""
        if not notice:
            raise MenuParseError("식단표 본문이 비어 있습니다.")
        for day in dates:
            week[day] = {label: Meal(note=notice) for label in ("중식", "석식")}
    return week


def _find_menu_table(soup: BeautifulSoup):
    """날짜 헤더("월(11.09)" 형태)가 있는 표를 식단표로 봅니다."""
    for table in soup.find_all("table"):
        if any(HEADER_PATTERN.search(th.get_text()) for th in table.find_all("th")):
            return table
    raise MenuParseError("날짜 헤더(예: '월(11.09)')가 있는 식단표를 찾지 못했습니다.")


def _parse_header_dates(table, today: date) -> list[date]:
    dates = []
    for th in table.find_all("th"):
        text = th.get_text(strip=True)
        match = HEADER_PATTERN.search(text)
        if not match:
            raise MenuParseError(f"날짜 헤더를 해석하지 못했습니다: '{text}'")
        month, day = int(match.group(2)), int(match.group(3))
        dates.append(_closest_date(month, day, today))
    return dates


def _closest_date(month: int, day: int, today: date) -> date:
    """월/일만 보고 today와 가장 가까운 연도의 날짜를 고릅니다.

    연말연시에 12월 표를 1월에 보거나 그 반대인 경우를 처리하기 위해서입니다.
    """
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, month, day))
        except ValueError:
            pass  # 2월 29일처럼 그 해에 없는 날짜
    if not candidates:
        raise MenuParseError(f"잘못된 날짜입니다: {month}.{day}")
    return min(candidates, key=lambda candidate: abs((candidate - today).days))


def _cell_label(cell) -> str | None:
    """칸 맨 앞의 끼니 표시(중식/석식)를 찾습니다. 없으면 None."""
    paragraph = cell.find("p")
    text = (paragraph or cell).get_text(" ", strip=True)
    for label in MEAL_LABELS:
        if text.startswith(label):
            return label
    return None


def _parse_cell(cell, label: str) -> Meal:
    items = [li.get_text(strip=True) for li in cell.find_all("li")]
    items = [item for item in items if item]
    if items:
        return Meal(items=items)

    # 메뉴 목록이 없으면 칸에 적힌 문구("운영 없음" 등)를 그대로 보관합니다.
    note = " ".join(cell.get_text(" ", strip=True).split())
    if note.startswith(label):
        note = note[len(label):].strip()
    return Meal(note=note)
