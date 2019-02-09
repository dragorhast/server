"""
JSON RPC
--------

JSON RPC is a light remote procedure calling protocol which is used by
the system to facilitate the websocket requests. JSON RPC has two primary
types of data: the request and the notification. Requests define an "id"
which can be responded to in a later response. This means the order of
request and response is arbitrary.

In the system, we use it to communicate with the bikes, handling locking,
unlocking, and location updates using it.
"""

from marshmallow import Schema, fields


class JsonRPCRequest(Schema):
    jsonrpc = fields.String(required=True)
    method = fields.String(required=True)
    params = fields.Raw()
    id = fields.Int()


class ErrorObject(Schema):
    code = fields.Int()
    message = fields.String()
    data = fields.Raw()


class JsonRPCResponse(Schema):
    jsonrpc = fields.String(required=True)
    id = fields.Int(required=True)
    result = fields.Raw()
    error = fields.Nested(ErrorObject())
