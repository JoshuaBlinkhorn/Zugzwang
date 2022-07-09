import datetime

class ZugDates():

    @classmethod
    def today(cls):
        return datetime.date.today()

    @classmethod
    def yesterday(cls):
        return datetime.date.today() - datetime.timedelta(days=1)

    @classmethod
    def due_date(
            cls,
            last_study_date,
            current_due_date,
            recall_factor,
            recall_radius
    ):
        previous_diff = (current_due_date - last_study_date).days
        radius = min(previous_diff, recall_radius)
        diff = previous_diff * recall_radius
        absolute_recall_date = current_due_date + datetime.timedelta(days = diff)
        offset = randint(0, (radius*2)) - radius
        recall_date = absolute_recall_date + datetime.timedelta(days = offset)
        return recall_date


