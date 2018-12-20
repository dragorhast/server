from tortoise import Model, fields


class User(Model):
    """
    Represents a User in the system.
    """

    id = fields.IntField(pk=True)
    firebase_id = fields.CharField(max_length=64)

    first = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
