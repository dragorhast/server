"""
User
---------------------------
"""
from enum import Enum

from tortoise import Model, fields

from server.models.fields import EnumField


class UserType(Enum):
    USER = "user"
    OPERATOR = "operator"
    MANAGER = "manager"


class User(Model):
    """
    Represents a User in the system.
    """

    id = fields.IntField(pk=True)
    firebase_id = fields.CharField(max_length=64, unique=True)

    first = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)

    type: UserType = EnumField(UserType, default=UserType.USER)
    stripe_id = fields

    def serialize(self):
        return {
            "firebase_id": self.firebase_id,
            "first": self.first,
            "email": self.email
        }

    def __str__(self):
        return f"[{self.id}] {self.first} ({self.email})"
