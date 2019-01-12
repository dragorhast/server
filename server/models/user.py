"""
User
---------------------------
"""

from tortoise import Model, fields


class User(Model):
    """
    Represents a User in the system.
    """

    id = fields.IntField(pk=True)
    firebase_id = fields.CharField(max_length=64, unique=True)

    first = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)

    def serialize(self):
        return {
            "firebase_id": self.firebase_id,
            "first": self.first,
            "email": self.email
        }
