"""
Pick-up Related Views
---------------------------

Handles all the pick-up point CRUD

- Customer can reserve a bike from a rack
- Admin must be able to get bikes in use / available at each location
"""
from aiohttp import web

from server.models import PickupPoint
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import returns
from server.serializer.models import PickupPointSchema, BikeSchema
from server.service.pickup_point import get_pickup_points, get_pickup_point
from server.views.base import BaseView
from server.views.utils import match_getter


class PickupsView(BaseView):
    """
    Gets or adds to the list of all pick-up points.
    """
    url = "/pickups"

    @returns(JSendSchema.of(PickupPointSchema(), many=True))
    async def get(self):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [pickup.serialize() for pickup in await get_pickup_points()]
        }

    async def post(self):
        raise NotImplementedError()


class PickupView(BaseView):
    """
    Gets, updates or deletes a single pick-up point.
    """
    url = "/pickups/{id:[0-9]+}"
    pickup_getter = match_getter(get_pickup_point, 'pickup', pickup_id='id')

    @pickup_getter
    async def get(self, pickup):
        return {
            "status": JSendStatus.SUCCESS,
            "data": pickup.serialize()
        }

    @pickup_getter
    async def delete(self, pickup: PickupPoint):
        await pickup.delete()
        raise web.HTTPNoContent

    async def put(self):
        raise NotImplementedError()


class PickupBikesView(BaseView):
    """
    Gets list of bikes currently at a pickup point.
    """
    url = "/pickups/{id:[0-9]+}/bikes"
    pickup_getter = match_getter(get_pickup_point, 'pickup', pickup_id='id')

    @pickup_getter
    @returns(JSendSchema.of(BikeSchema(), many=True))
    async def get(self, pickup: PickupPoint):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [bike.serialize(self.bike_connection_manager) for bike in await pickup.bikes()]
        }


class PickupReservationsView(BaseView):
    """
    Gets or adds to a pickup point's list of reservations.
    """
    url = "/pickups/{id:[0-9]+}/reservations"

    async def get(self):
        raise NotImplementedError()

    async def post(self):
        raise NotImplementedError()
