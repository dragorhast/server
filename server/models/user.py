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
    stripe_id = fields.CharField(max_length=32, unique=True, null=True)

    first = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)

    type: UserType = EnumField(UserType, default=UserType.USER)

    def serialize(self):
        return {
            "firebase_id": self.firebase_id,
            "first": self.first,
            "email": self.email
        }

    @property
    def can_pay(self):
        """Whether the customer can be charged."""
        return self.stripe_id is not None

    @property
    def is_admin(self):
        """Whether the user is an admin."""
        return self.type is UserType.MANAGER or self.type is UserType.OPERATOR

    def __str__(self):
        return f"[{self.id}] {self.first} ({self.email})"
