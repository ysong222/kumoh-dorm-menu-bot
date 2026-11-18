"""예약 실행이 늦게 시작됐을 때 보낼지 말지 판단하는 로직을 검증합니다."""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from main import CRON_TO_MODE, check_schedule, cron_kst_time

KST = ZoneInfo("Asia/Seoul")
CRON_FOR = {mode: cron for cron, mode in CRON_TO_MODE.items()}


def kst(month, day, hour, minute):
    return datetime(2026, month, day, hour, minute, tzinfo=KST)


def on_time(mode, month=11, day=18):
    """그 알림이 예정 시각에 정확히 실행된 경우의 시각 (2026-11-18은 수요일)"""
    scheduled = cron_kst_time(CRON_FOR[mode])
    return kst(month, day, scheduled.hour, scheduled.minute)


class CheckScheduleTest(unittest.TestCase):
    def test_on_time_sends_without_delay(self):
        for mode, cron in CRON_FOR.items():
            self.assertEqual(check_schedule(cron, on_time(mode)), (True, 0), mode)

    def test_late_but_before_deadline_sends_with_delay(self):
        # 실제 사례: 미리보기가 12:55에 실행됨
        should_send, late = check_schedule(CRON_FOR["preview"], kst(11, 18, 12, 55))
        self.assertTrue(should_send)
        scheduled = cron_kst_time(CRON_FOR["preview"])
        self.assertEqual(late, (12 * 60 + 55) - (scheduled.hour * 60 + scheduled.minute))

    def test_dinner_running_after_midnight_is_skipped(self):
        # 실제 사례: 화요일 석식 알림이 수요일 01:58에 실행됨
        self.assertEqual(check_schedule(CRON_FOR["dinner"], kst(11, 18, 1, 58)), (False, 0))

    def test_lunch_after_service_ends_is_skipped(self):
        self.assertFalse(check_schedule(CRON_FOR["lunch"], kst(11, 18, 13, 31))[0])

    def test_dinner_after_service_ends_is_skipped(self):
        self.assertFalse(check_schedule(CRON_FOR["dinner"], kst(11, 18, 19, 1))[0])

    def test_weekend_is_skipped(self):
        # 금요일 석식 알림이 토요일까지 밀린 경우
        self.assertFalse(check_schedule(CRON_FOR["dinner"], on_time("dinner", day=21))[0])

    def test_cron_kst_time_crosses_midnight(self):
        # UTC 23:00 은 KST 다음 날 08:00
        self.assertEqual(cron_kst_time("0 23 * * 0-4").strftime("%H:%M"), "08:00")


if __name__ == "__main__":
    unittest.main()
