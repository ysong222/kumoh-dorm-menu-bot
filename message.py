"""파싱한 식단을 텔레그램 메시지 문자열로 만드는 모듈."""

from __future__ import annotations

from datetime import date

from menu_parser import Meal, WeekMenu

DORM_NAME = "오름관3동"
WEEKDAYS = "월화수목금토일"  # date.weekday()는 월요일이 0

# 알림 종류(mode)별 제목과 보여줄 끼니
MODES = {
    "preview": ("🍽 오늘의 식단 미리보기", ("중식", "석식")),
    "lunch": ("🍚 오늘의 중식", ("중식",)),
    "dinner": ("🌙 오늘의 석식", ("석식",)),
}

# 평일 운영 시간
MEAL_HOURS = {"중식": "11:30~13:30", "석식": "17:00~19:00"}

# 텔레그램 메시지 한 개의 최대 길이는 4096자라서 에러 내용은 적당히 자릅니다.
MAX_ERROR_LENGTH = 1000


def build_menu_message(mode: str, today: date, week: WeekMenu) -> str:
    title, meal_names = MODES[mode]
    lines = [title, f"{_format_date(today)} · {DORM_NAME}", ""]

    if today not in week:
        lines.append("식단표에 오늘 날짜가 없어요.")
        lines.append("이번 주 식단이 아직 등록되지 않았을 수 있어요.")
        if week:
            first, last = min(week), max(week)
            lines.append(f"(현재 식단표: {_format_date(first)} ~ {_format_date(last)})")
        return "\n".join(lines)

    is_weekday = today.weekday() < 5
    sections = []
    for name in meal_names:
        header = f"[{name}]"
        if is_weekday:
            header += f" {MEAL_HOURS[name]}"
        sections.append(header + "\n" + _format_meal(week[today].get(name)))
    lines.append("\n\n".join(sections))
    return "\n".join(lines)


def build_error_message(mode: str, error: Exception) -> str:
    title = MODES[mode][0]
    detail = f"{type(error).__name__}: {error}"
    if len(detail) > MAX_ERROR_LENGTH:
        detail = detail[:MAX_ERROR_LENGTH] + "…"
    return f"⚠️ 식단을 가져오지 못했어요\n({title} 알림)\n\n{detail}"


def _format_date(day: date) -> str:
    return f"{day.month}월 {day.day}일({WEEKDAYS[day.weekday()]})"


def _format_meal(meal: Meal | None) -> str:
    if meal is None or (not meal.items and not meal.note):
        return "메뉴 정보가 없어요."
    if not meal.items:
        return meal.note  # "운영 없음" 같은 안내 문구
    return "\n".join(f"· {item}" for item in meal.items)
