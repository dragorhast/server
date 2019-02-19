"""
Issue
---------------------------
"""
from typing import Any, Dict

from tortoise import Model, fields


class Issue(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="issues")
    bike = fields.ForeignKeyField("models.Bike", null=True, related_name="issues")
    time = fields.DatetimeField(auto_now_add=True)
    description = fields.TextField()
    is_active = fields.BooleanField(default=True)

    def serialize(self, router) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "user_url": router["user"].url_for(id=str(self.user_id)).path,
            "time": self.time,
            "description": self.description
        }

        if self.bike_id is not None:
            data["bike_identifier"] = self.bike.identifier
            data["bike_url"] = router["bike"].url_for(identifier=str(self.bike.identifier)).path

        return data
