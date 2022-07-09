import pytest
import datetime

from zugzwang import ZugDates


class TestZugDates:

    def test_today():
        ZugDates.today()

    def test_yesterday():
        ZugDates.yesterday()

    def test_calculate_due_date():
        pass
