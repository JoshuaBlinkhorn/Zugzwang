import datetime
from random import randint
import datetime


def _today():
    return datetime.date.today()


def today():
    return _today()


def yesterday():
    return _today() - datetime.timedelta(days=1)


def tomorrow():
    return _today() + datetime.timedelta(days=1)


class ZugDates:
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
        recall_radius,
        recall_max,
    ):
        # calculate the diff based on recall factor and radius
        previous_diff = (current_due_date - last_study_date).days
        absolute_diff = int(previous_diff * recall_factor)
        offset = randint(-recall_radius, recall_radius)

        # impose minimum and maximum values
        diff = max(1, min(absolute_diff + offset, recall_max))
        return cls.today() + datetime.timedelta(days=diff)
