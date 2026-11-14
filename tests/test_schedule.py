"""cron(UTC)이 의도한 한국 시간에 맞는지 검증합니다."""

import re
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from main import CRON_TO_MODE

KST = ZoneInfo("Asia/Seoul")
WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "menu-notify.yml"

# 알림 종류별로 원하는 한국 시간 (시, 분)
EXPECTED_KST_TIME = {"preview": (8, 0), "lunch": (11, 0), "dinner": (16, 30)}
KST_WEEKDAYS = {0, 1, 2, 3, 4}  # date.weekday() 기준 월~금


def kst_runs(cron: str) -> set[tuple[int, int, int]]:
    """cron 식이 실행되는 시각들을 KST의 (요일, 시, 분) 집합으로 바꿉니다.

    이 프로젝트에서 쓰는 "분 시 * * 요일범위" 형태만 지원합니다.
    """
    minute, hour, day_of_month, month, day_of_week = cron.split()
    assert day_of_month == "*" and month == "*"
    first, last = (int(n) for n in day_of_week.split("-"))

    runs = set()
    for cron_weekday in range(first, last + 1):
        # 2026-11-01은 일요일. cron 요일은 일요일이 0이라 날짜를 그만큼 더하면 됩니다.
        utc = datetime(2026, 11, 1, int(hour), int(minute), tzinfo=timezone.utc)
        utc += timedelta(days=cron_weekday)
        kst = utc.astimezone(KST)
        runs.add((kst.weekday(), kst.hour, kst.minute))
    return runs


class ScheduleTest(unittest.TestCase):
    def test_each_cron_runs_at_expected_kst_time_on_weekdays(self):
        for cron, mode in CRON_TO_MODE.items():
            hour, minute = EXPECTED_KST_TIME[mode]
            expected = {(weekday, hour, minute) for weekday in KST_WEEKDAYS}
            self.assertEqual(kst_runs(cron), expected, f"{mode}: {cron}")

    def test_all_three_modes_are_scheduled(self):
        self.assertEqual(set(CRON_TO_MODE.values()), set(EXPECTED_KST_TIME))

    def test_workflow_crons_match_code(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        workflow_crons = set(re.findall(r'cron:\s*"([^"]+)"', text))
        self.assertEqual(workflow_crons, set(CRON_TO_MODE))


if __name__ == "__main__":
    unittest.main()
