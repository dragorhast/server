"""
Handles all the user CRUD
"""

from aiohttp import web
from aiohttp.abc import Request

from server.models import User, Rental
from server.permissions import UserMatchesFirebase
from server.permissions.decorators import requires
from server.permissions.permissions import ValidToken
from server.serializer import JSendSchema, JSendStatus, UserSchema, RentalSchema
from server.serializer.decorators import expects, returns
from server.service.users import get_users, get_user, delete_user, create_user, UserExistsError, update_user
from server.service.verify_token import verifier, TokenVerificationError
from server.views.base import BaseView
from server.views.utils import getter


class UsersView(BaseView):
    """
    Gets or adds to the list of users.
    """
    url = "/users"
    name = "users"

    @expects(None)
    @returns(JSendSchema.of(UserSchema(), many=True))
    async def get(self):
        return {
            "status": JSendStatus.SUCCESS,
            "data": await get_users()
        }

    @requires(ValidToken())
    @expects(UserSchema(only=('first', 'email')))
    async def post(self):
        try:
            user = await create_user(**self.request["data"], firebase_id=self.request["token"])
        except UserExistsError as err:
            response_schema = JSendSchema()
            response_data = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": err.errors
            })
            return web.json_response(response_data, status=409)

        response_schema = JSendSchema.of(UserSchema())
        return web.json_response(response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": user.serialize()
        }), status=201)


class UserView(BaseView):
    """
    Gets, replaces or deletes a single user.
    """
    url = "/users/{id:[0-9]+}"
    name = "user"
    user_getter = getter(get_user, 'id', 'user_id', 'user')

    @user_getter
    @requires(UserMatchesFirebase())
    @expects(None)
    @returns(JSendSchema.of(UserSchema()))
    async def get(self, user: User):
        return {
            "status": JSendStatus.SUCCESS,
            "data": user.serialize()
        }

    @user_getter
    @requires(UserMatchesFirebase())
    @expects(UserSchema(exclude=('id', 'firebase_id')))
    @returns(JSendSchema.of(UserSchema()))
    async def put(self, user: User):
        user = await update_user(user, **self.request["data"])
        return {
            "status": JSendStatus.SUCCESS,
            "data": user.serialize()
        }

    @user_getter
    @requires(UserMatchesFirebase())
    async def delete(self, user: User):
        await delete_user(user)
        raise web.HTTPNoContent()


class UserRentalsView(BaseView):
    """
    Gets or adds to the users list of rentals.
    """
    url = "/users/{id:[0-9]+}/rentals"
    name = "user_rentals"
    with_user = getter(get_user, 'id', 'user_id', 'user')

    @with_user
    @requires(UserMatchesFirebase())
    @returns(JSendSchema.of(RentalSchema(), many=True))
    async def get(self, user):
        rentals = await Rental.filter(user__id=user.id)
        return {
            "status": JSendStatus.SUCCESS,
            "data": [await rental.serialize(self.request.app["rental_manager"]) for rental in rentals]
        }


class UserCurrentRentalView(BaseView):
    """
    Gets or ends the user's current rental.
    """
    url = "/users/{id:[0-9]+}/rentals/current"
    name = "user_current_rental"
    with_user = getter(get_user, 'id', 'user_id', 'user')

    @with_user
    @requires(UserMatchesFirebase())
    async def get(self, user: User):
        if user.id not in self.request.app["rental_manager"].active_rental_ids:
            response_schema = JSendSchema()
            response_data = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"rental": f"You have no current rental."}
            })
            return web.json_response(response_data, status=404)

        current_rental = await self.request.app["rental_manager"].active_rental(user)
        response_schema = JSendSchema.of(RentalSchema())
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": await current_rental.serialize(self.request.app["rental_manager"])
        })

        return web.json_response(response_data)

    @with_user
    @requires(UserMatchesFirebase())
    async def delete(self, user: User):
        """Ends a rental."""
        if user.id not in self.request.app["rental_manager"].active_rental_ids:
            response_schema = JSendSchema()
            response_data = response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"rental": f"You have no current rental."}
            })
            return web.json_response(response_data, status=404)

        current_rental = await self.request.app["rental_manager"].active_rental(user)
        await self.request.app["rental_manager"].finish(current_rental)
        response_schema = JSendSchema.of(RentalSchema())
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": await current_rental.serialize(self.request.app["rental_manager"])
        })

        return web.json_response(response_data)


class UserReservationsView(BaseView):
    """
    Gets or adds to the users' list of reservations.
    """
    url = "/users/{id:[0-9]+}/reservations"
    name = "user_reservations"

    async def get(self):
        raise NotImplementedError()

    async def post(self):
        raise NotImplementedError()


class UserIssuesView(BaseView):
    """
    Gets or adds to the users' list of issues.
    """
    url = "/users/{id:[0-9]+}/issues"
    name = "user_issues"

    async def get(self):
        raise NotImplementedError()

    async def post(self):
        raise NotImplementedError()


class MeView(BaseView):
    """
    Gets the data for the currently authenticated user.
    """

    url = "/users/me{tail:.*}"
    name = "me"

    async def get(self):
        return await self._me_handler()

    async def post(self):
        return await self._me_handler()

    async def put(self):
        return await self._me_handler()

    async def patch(self):
        return await self._me_handler()

    async def delete(self):
        return await self._me_handler()

    @requires(ValidToken())
    async def _me_handler(self):
        """
        Accepts all types of request, does some checking against the user, and forwards them on to the appropriate user.
        """
        user = await get_user(firebase_id=self.request["token"])

        if user is None:
            response_schema = JSendSchema()
            create_user_url = str(self.request.app.router['users'].url_for())
            return web.json_response(response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {
                    "authorization": "User does not exist. Please use your token to create a user and try again.",
                    "url": create_user_url,
                    "method": "POST"
                }
            }), status=401)

        concrete_url = MeView._get_concrete_user_url(self.request.path, self.request.match_info.get("tail"), user)
        raise web.HTTPFound(concrete_url)

    @staticmethod
    def _get_concrete_user_url(path, tail, user) -> str:
        """
        Given a relative "me" url, and a user, rewrites the url to a concrete user.

        :param path: The current path of the "me" url.
        :param tail: The tail section of the url (after the "me")
        :param user: The user to rewrite to.
        """
        url_without_tail = path[:-len(tail)]
        user_id = user.id
        user_url = url_without_tail[:-2] + str(user_id)
        return user_url + tail
