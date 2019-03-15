"""
Issue
---------------------------
"""
from enum import Enum
from typing import Any, Dict

from tortoise import Model, fields

from server.models.fields import EnumField


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"


class Issue(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="issues")
    bike = fields.ForeignKeyField("models.Bike", null=True, related_name="issues")
    opened_at = fields.DatetimeField(auto_now_add=True)
    closed_at = fields.DatetimeField(null=True)
    description = fields.TextField()
    resolution = fields.TextField(null=True)
    status = EnumField(IssueStatus, default=IssueStatus.OPEN)

    def serialize(self, router) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "user_url": router["user"].url_for(id=str(self.user_id)).path,
            "opened_at": self.opened_at,
            "description": self.description,
            "status": self.status
        }

        if self.bike_id is not None:
            data["bike_identifier"] = self.bike.identifier
            data["bike_url"] = router["bike"].url_for(identifier=str(self.bike.identifier)).path

        if self.status == IssueStatus.CLOSED:
            data["closed_at"] = self.closed_at

        return data
