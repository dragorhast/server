"""
Issue
---------------------------
"""

from tortoise import Model, fields


class Issue(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User")
    bike = fields.ForeignKeyField("models.Bike", null=True)
    time = fields.DatetimeField(auto_now_add=True)
    description = fields.TextField()

    def serialize(self, router):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_url": router["user"].url_for(id=str(self.user_id)).path,
            "bike_id": self.bike_id,
            "bike_url": router["bike"].url_for(id=str(self.bike_id)).path,
            "time": self.time,
            "description": self.description
        }
