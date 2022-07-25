import pytest
import mock
import datetime

from zugzwang.dates import ZugDates

EPOCH = datetime.date(2000,1,1)  # fixes a mock today
REPETITIONS = 10000  # were testing randomised functions, so we repeat each many times

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
            (-1, 0, 5, 1, 4, 6),
            (-1, 0, 5, 2, 3, 7),
            (-1, 0, 5, 10, 1, 15),                                                
            # last date t-2, recall_factor 1
            (-2, 0, 1, 0, 2, 2),
            (-2, 0, 1, 1, 1, 3),
            (-2, 0, 1, 2, 1, 4),
            (-2, 0, 1, 10, 1, 12),                                                      
            # last date t-2, recall_factor 2
            (-2, 0, 2, 0, 4, 4),
            (-2, 0, 2, 1, 3, 5),
            (-2, 0, 2, 2, 2, 6),
            (-2, 0, 2, 10, 1, 14),                                                      
            # last date t-2, recall_factor 5
            (-2, 0, 5, 0, 10, 10),
            (-2, 0, 5, 1, 9, 11),
            (-2, 0, 5, 2, 8, 12),
            (-2, 0, 5, 10, 1, 20),                                                      
            # last date t-5, recall_factor 1
            (-5, 0, 1, 0, 5, 5),
            (-5, 0, 1, 1, 4, 6),
            (-5, 0, 1, 2, 3, 7),
            (-5, 0, 1, 10, 1, 15),                                                      
            # last date t-5, recall_factor 2
            (-5, 0, 2, 0, 10, 10),
            (-5, 0, 2, 1, 9, 11),
            (-5, 0, 2, 2, 8, 12),
            (-5, 0, 2, 10, 1, 20),                                                      
            # last date t-5, recall_factor 5
            (-5, 0, 5, 0, 25, 25),
            (-5, 0, 5, 1, 24, 26),
            (-5, 0, 5, 2, 23, 27),
            (-5, 0, 5, 10, 15, 35),                                                      
            # last date t-100, recall_factor 1
            (-100, 0, 1, 0, 100, 100),
            (-100, 0, 1, 1, 99, 101),
            (-100, 0, 1, 2, 98, 102),
            (-100, 0, 1, 10, 90, 110),
            # last date t-100, recall_factor 2
            (-100, 0, 2, 0, 200, 200),
            (-100, 0, 2, 1, 199, 201),
            (-100, 0, 2, 2, 198, 202),
            (-100, 0, 2, 10, 190, 210),
            # last date t-100, recall_factor 5
            (-100, 0, 5, 0, 365, 365),
            (-100, 0, 5, 1, 365, 365),
            (-100, 0, 5, 2, 365, 365),
            (-100, 0, 5, 200, 300, 365),
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
        # the function is randomised; so repeat the test many times
        repetitions = 10000
        last_study_date = epoch_shift(last_study_date_offset)
        current_due_date = epoch_shift(current_due_date_offset)
        lower_bound = epoch_shift(expected_offset_lower_bound)
        upper_bound = epoch_shift(expected_offset_upper_bound)        
        due_date_lambda = lambda: ZugDates.due_date(
            last_study_date, current_due_date, recall_factor, recall_radius
        )
        due_dates = [due_date_lambda() for n in range(REPETITIONS)]
        
        # all calucated due dates occur in expected range;
        # i.e. the expected range covers the actual range
        assert all(due_date >= lower_bound for due_date in due_dates)
        assert all(due_date <= upper_bound for due_date in due_dates)

        # each endpoint is hit by at least one endpoint due date;
        # i.e. the actual range covers the expected range
        assert any(due_date == lower_bound for due_date in due_dates)        
        assert any(due_date == lower_bound for due_date in due_dates)

    @pytest.mark.parametrize(
        'recall_max, expected_offset_lower_bound, expected_offset_upper_bound',
        [
            (1, 1, 1),
            (10, 10, 10),
            (100, 100, 100),
            (1000, 197, 203),
        ]
    )
    def test_calculate_due_date_maximum(
            self,
            recall_max,
            expected_offset_lower_bound,
            expected_offset_upper_bound
    ):
        repetitions = 10000        
        last_study_date = epoch_shift(-100)
        current_due_date = epoch_shift(0)
        lower_bound = epoch_shift(expected_offset_lower_bound)
        upper_bound = epoch_shift(expected_offset_upper_bound)
        due_date_lambda = lambda: ZugDates.due_date(
            last_study_date, current_due_date, recall_max = recall_max
        )
        due_dates = [due_date_lambda() for n in range(REPETITIONS)]
        
        # all calucated due dates occur in expected range;
        # i.e. the expected range covers the actual range
        assert all(due_date >= lower_bound for due_date in due_dates)
        assert all(due_date <= upper_bound for due_date in due_dates)

        # each endpoint is hit by at least one endpoint due date;
        # i.e. the actual range covers the expected range
        assert any(due_date == lower_bound for due_date in due_dates)        
        assert any(due_date == lower_bound for due_date in due_dates)

    @pytest.mark.parametrize(
        'recall_factor, expected_offset_lower_bound, expected_offset_upper_bound',
        [
            (0.5, 9, 15),
            (1.5, 34, 40),
            (2.5, 59, 65),
            (3.5, 84, 90),
        ]
    )
    def test_calculate_due_date_fractional_recall_factor(
            self,
            recall_factor,
            expected_offset_lower_bound,
            expected_offset_upper_bound
    ):
        last_study_date = epoch_shift(-25)
        current_due_date = epoch_shift(0)
        lower_bound = epoch_shift(expected_offset_lower_bound)
        upper_bound = epoch_shift(expected_offset_upper_bound)
        due_date_lambda = lambda: ZugDates.due_date(
            last_study_date, current_due_date, recall_factor = recall_factor
        )
        due_dates = [due_date_lambda() for n in range(REPETITIONS)]
        
        # all calucated due dates occur in expected range;
        # i.e. the expected range covers the actual range
        assert all(due_date >= lower_bound for due_date in due_dates)
        assert all(due_date <= upper_bound for due_date in due_dates)

        # each endpoint is hit by at least one endpoint due date;
        # i.e. the actual range covers the expected range
        assert any(due_date == lower_bound for due_date in due_dates)        
        assert any(due_date == lower_bound for due_date in due_dates)
