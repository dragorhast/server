from tortoise import Model, fields


class LocationUpdate(Model):
    """
    A location update places a bike
    at some set of coordinates
    at a specific point in time.

    .. note:: Currently the location is a :class:`tortoise.fields.CharField`
        because there is no native GIS support.
        This will be eventually changed,
        and storing it as a sting is a "brute force" solution.
    """
    id = fields.IntField(pk=True)
    location = fields.CharField(max_length=63)  # 52.432,-34.432
    bike = fields.ForeignKeyField("models.Bike")
    time = fields.DatetimeField(auto_now_add=True)
