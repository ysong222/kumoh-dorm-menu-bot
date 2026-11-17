import unittest
from datetime import date

from menu_parser import Meal, MenuFetchError
from message import build_error_message, build_menu_message

FRIDAY = date(2026, 11, 13)
WEEK = {
    FRIDAY: {
        "중식": Meal(items=["청양풍볶음면", "깍두기"]),
        "석식": Meal(items=["참치김치찌개", "쌀밥"]),
    }
}


class MenuMessageTest(unittest.TestCase):
    def test_preview_shows_both_meals(self):
        text = build_menu_message("preview", FRIDAY, WEEK)
        self.assertEqual(
            text,
            "🍽 오늘의 식단 미리보기\n"
            "11월 13일(금) · 오름관3동\n"
            "\n"
            "[중식] 11:30~13:30\n"
            "· 청양풍볶음면\n"
            "· 깍두기\n"
            "\n"
            "[석식] 17:00~19:00\n"
            "· 참치김치찌개\n"
            "· 쌀밥",
        )

    def test_lunch_shows_only_lunch(self):
        text = build_menu_message("lunch", FRIDAY, WEEK)
        self.assertIn("청양풍볶음면", text)
        self.assertNotIn("참치김치찌개", text)

    def test_dinner_shows_only_dinner(self):
        text = build_menu_message("dinner", FRIDAY, WEEK)
        self.assertIn("참치김치찌개", text)
        self.assertNotIn("청양풍볶음면", text)

    def test_closed_notice_is_shown_as_is(self):
        week = {FRIDAY: {"중식": Meal(note="운영 없음"), "석식": Meal(items=["쌀밥"])}}
        text = build_menu_message("lunch", FRIDAY, week)
        self.assertIn("[중식] 11:30~13:30\n운영 없음", text)

    def test_empty_meal_says_no_menu(self):
        week = {FRIDAY: {"중식": Meal(), "석식": Meal(items=["쌀밥"])}}
        self.assertIn("메뉴 정보가 없어요.", build_menu_message("lunch", FRIDAY, week))

    def test_missing_meal_says_no_menu(self):
        week = {FRIDAY: {"중식": Meal(items=["쌀밥"])}}
        self.assertIn("메뉴 정보가 없어요.", build_menu_message("dinner", FRIDAY, week))

    def test_date_not_in_table(self):
        next_monday = date(2026, 11, 16)
        text = build_menu_message("preview", next_monday, WEEK)
        self.assertIn("11월 16일(월)", text)
        self.assertIn("아직 등록되지 않았을 수 있어요", text)
        self.assertNotIn("청양풍볶음면", text)


class ErrorMessageTest(unittest.TestCase):
    def test_contains_error_detail(self):
        text = build_error_message("lunch", MenuFetchError("접속 실패"))
        self.assertIn("MenuFetchError: 접속 실패", text)
        self.assertIn("오늘의 중식", text)

    def test_long_error_is_truncated(self):
        text = build_error_message("lunch", MenuFetchError("x" * 5000))
        self.assertLess(len(text), 1200)


if __name__ == "__main__":
    unittest.main()
