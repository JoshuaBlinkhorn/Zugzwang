import pytest
import datetime

from zugzwang.dates import ZugDates

# Mock 'today' as January 1st 2000, which we call the EPOCH.
# All logic in the dates module is made relative to this date by mocking
# out the unique point where that module calls datetime.date.today(), i.e.
# ZugDates._today().
# For test files, we provide the function epoch_shift(), which returns a datetime.date
# relative to EPOCH.

EPOCH = datetime.date(2000, 1, 1)


def epoch_shift(shift: int):
    return EPOCH + datetime.timedelta(days=shift)


@pytest.fixture(autouse=True)
def mock_today(monkeypatch):
    def mock_today():
        return EPOCH

    monkeypatch.setattr(ZugDates, "_today", mock_today)
