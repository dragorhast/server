from tortoise import Model, fields


class LocationUpdate(Model):
    id = fields.IntField(pk=True)
    location = fields.CharField(max_length=63)  # 52.432,-34.432
    bike = fields.ForeignKeyField("models.Bike")
    time = fields.DatetimeField(auto_now_add=True)
