import unittest
from datetime import date
from pathlib import Path

from menu_parser import MenuParseError, parse_menu

SAMPLE_HTML = (Path(__file__).parent / "fixtures" / "menu_sample.html").read_text(
    encoding="utf-8"
)
TODAY = date(2026, 11, 13)  # 샘플 표(11.09~11.15) 안의 금요일


class ParseSampleTest(unittest.TestCase):
    def setUp(self):
        self.week = parse_menu(SAMPLE_HTML, TODAY)

    def test_seven_days_from_monday_to_sunday(self):
        days = sorted(self.week)
        self.assertEqual(len(days), 7)
        self.assertEqual(days[0], date(2026, 11, 9))
        self.assertEqual(days[-1], date(2026, 11, 15))

    def test_every_day_has_lunch_and_dinner(self):
        for meals in self.week.values():
            self.assertEqual(set(meals), {"중식", "석식"})

    def test_friday_lunch_items(self):
        lunch = self.week[date(2026, 11, 13)]["중식"]
        self.assertEqual(
            lunch.items,
            ["청양풍볶음면", "맑은우동국물", "갈비만두찜*간장", "양파간장절임", "쌀밥", "깍두기"],
        )

    def test_monday_dinner_items(self):
        dinner = self.week[date(2026, 11, 9)]["석식"]
        self.assertEqual(dinner.items[0], "부추국수")
        self.assertEqual(len(dinner.items), 5)

    def test_html_entity_is_decoded(self):
        saturday_lunch = self.week[date(2026, 11, 14)]["중식"]
        self.assertIn("딸기&초코우유", saturday_lunch.items)


class ParseEdgeCaseTest(unittest.TestCase):
    def test_closed_day_keeps_notice_text(self):
        # 금요일 중식 칸을 "운영 없음" 문구로 바꾼 표
        start = SAMPLE_HTML.index("<li>청양풍볶음면</li>")
        end = SAMPLE_HTML.index("</ul>", start)
        ul_start = SAMPLE_HTML.rindex("<ul", 0, start)
        html = SAMPLE_HTML[:ul_start] + "운영 없음" + SAMPLE_HTML[end + len("</ul>"):]

        lunch = parse_menu(html, TODAY)[date(2026, 11, 13)]["중식"]
        self.assertEqual(lunch.items, [])
        self.assertEqual(lunch.note, "운영 없음")

    def test_empty_cell_has_no_items_and_no_note(self):
        # 금요일 중식 칸을 메뉴 목록 없이 "중식" 표시만 남긴 표
        # (목요일 메뉴 '누룽지닭죽' 다음에 나오는 <p>중식</p>이 금요일 칸)
        start = SAMPLE_HTML.index("<p>중식</p>", SAMPLE_HTML.index("누룽지닭죽"))
        end = SAMPLE_HTML.index("</td>", start)
        html = SAMPLE_HTML[:start] + "<p>중식</p>" + SAMPLE_HTML[end:]

        lunch = parse_menu(html, TODAY)[date(2026, 11, 13)]["중식"]
        self.assertEqual(lunch.items, [])
        self.assertEqual(lunch.note, "")

    def test_year_boundary_picks_closest_year(self):
        html = SAMPLE_HTML.replace("월(11.09)", "월(12.28)").replace("일(11.15)", "일(01.03)")
        week = parse_menu(html, date(2026, 12, 30))
        self.assertIn(date(2026, 12, 28), week)
        self.assertIn(date(2027, 1, 3), week)

    def test_week_without_menu_keeps_site_notice(self):
        # 식단이 아직 등록되지 않은 주의 실제 응답 형태
        start = SAMPLE_HTML.index("<tbody>") + len("<tbody>")
        end = SAMPLE_HTML.index("</tbody>")
        html = (
            SAMPLE_HTML[:start]
            + '<td colspan="7">등록된 메뉴가 없습니다.</td>'
            + SAMPLE_HTML[end:]
        )
        week = parse_menu(html, TODAY)
        self.assertEqual(len(week), 7)
        self.assertEqual(week[TODAY]["중식"].note, "등록된 메뉴가 없습니다.")
        self.assertEqual(week[TODAY]["석식"].items, [])

    def test_page_without_menu_table_raises(self):
        with self.assertRaises(MenuParseError):
            parse_menu("<html><body><p>점검 중입니다</p></body></html>", TODAY)

    def test_wrong_cell_count_raises(self):
        html = SAMPLE_HTML.replace('<th scope="col">\n\t\t\t\t\t\t\t일(11.15)\n\t\t\t\t\t\t</th>', "")
        with self.assertRaises(MenuParseError):
            parse_menu(html, TODAY)


if __name__ == "__main__":
    unittest.main()
