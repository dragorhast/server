from tortoise import Model, fields


class Issue(Model):

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User")
    bike = fields.ForeignKeyField("models.Bike", null=True)
    time = fields.DatetimeField(auto_now_add=True)
    description = fields.TextField()
