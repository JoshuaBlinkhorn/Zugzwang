import pytest
import mock
import datetime

from zugzwang.dates import ZugDates

EPOCH = datetime.date(2000,1,1)

def epoch_shift(shift: int):
    return EPOCH + datetime.timedelta(days=shift)

@pytest.fixture(autouse=True)
def mock_today(monkeypatch):
    def mock_today():
        return EPOCH    
    monkeypatch.setattr(ZugDates, '_today', mock_today)

class TestZugDates:

    def test_today(self):
        assert ZugDates.today() == epoch_shift(0)

    def test_yesterday(self):
        ZugDates.yesterday() == epoch_shift(-1)

    def test_tomorrow(self):
        ZugDates.tomorrow() == epoch_shift(1)

    @pytest.mark.parametrize(
        (
            'last_study_date_offset, current_due_date_offset, recall_factor, '
            'recall_radius, expected_offset_lower_bound, expected_offset_upper_bound'
        ),
        [
            # last date t-1, recall_factor 1
            (-1, 0, 1, 0, 1, 1),
            (-1, 0, 1, 1, 1, 2),
            (-1, 0, 1, 2, 1, 3),            
            (-1, 0, 1, 10, 1, 11),
            # last date t-1, recall_factor 2            
            (-1, 0, 2, 0, 2, 2),
            (-1, 0, 2, 1, 1, 3),
            (-1, 0, 2, 2, 1, 4),
            (-1, 0, 2, 10, 1, 12),
            # last date t-1, recall_factor 5
            (-1, 0, 5, 0, 5, 5),
            (-1, 0, 5, 1, 1, 6),
            (-1, 0, 5, 2, 1, 7),
            (-1, 0, 5, 10, 1, 15),                                                
            
        ]        
    )
    def test_calculate_due_date(
            self,
            last_study_date_offset,
            current_due_date_offset,
            recall_factor,
            recall_radius,
            expected_offset_lower_bound,
            expected_offset_upper_bound
    ):
        last_study_date = epoch_shift(last_study_date_offset)
        current_due_date = epoch_shift(current_due_date_offset)

        # the function is randomised; so repeat the test many times
        for n in range(10000):
            due_date = ZugDates.due_date(
                last_study_date, current_due_date, recall_factor, recall_radius
            )
            assert epoch_shift(expected_offset_lower_bound) <= due_date
            assert epoch_shift(expected_offset_upper_bound) >= due_date
