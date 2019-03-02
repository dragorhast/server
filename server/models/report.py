from tortoise import Model, fields


class StatisticsReport(Model):
    date = fields.DateField()
    rentals_started = fields.IntField()
    rentals_ended = fields.IntField()
    reservations_started = fields.IntField()
    reservations_cancelled = fields.IntField()
    distance_travelled = fields.FloatField()
    revenue = fields.FloatField()
