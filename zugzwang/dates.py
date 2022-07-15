import datetime
from random import randint

class ZugDates():

    @classmethod
    def _today(cls):
        return datetime.date.today()

    @classmethod
    def today(cls):
        return cls._today()

    @classmethod
    def yesterday(cls):
        return cls._today() - datetime.timedelta(days=1)

    @classmethod
    def tomorrow(cls):
        return cls._today() + datetime.timedelta(days=1)

    @classmethod
    def due_date(
            cls,
            last_study_date,
            current_due_date,
            recall_factor,
            recall_radius
    ):
        previous_diff = (current_due_date - last_study_date).days
        diff = previous_diff * recall_factor
        absolute_recall_date = cls.today() + datetime.timedelta(days=diff)
        offset = randint(-recall_radius, recall_radius)
        recall_date = absolute_recall_date + datetime.timedelta(days=offset)
        return recall_date if recall_date >= cls.tomorrow() else cls.tomorrow()


