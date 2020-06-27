from marshmallow import Schema
from marshmallow.fields import Bool, String

from server.models.issue import IssueStatus
from server.models.util import BikeType
from server.serializer import BytesField, EnumField


class PaymentSourceSchema(Schema):
    token = String(required=True)


class MasterKeySchema(Schema):
    master_key = BytesField(required=True, description="The bike registration master key.")


class BikeRegisterSchema(MasterKeySchema):
    """The schema of the bike register request."""
    public_key = BytesField(required=True, description="The public key of the bike.")
    type = EnumField(BikeType, description="The type of bike.", default=BikeType.ROAD)


class BikeModifySchema(Schema):
    """"""
    locked = Bool()
    in_circulation = Bool()


class IssueUpdateSchema(Schema):
    status = EnumField(IssueStatus, required=True, default=IssueStatus.OPEN)
    resolution = String(allow_none=True)
