"""
Handles all the user CRUD
"""
from typing import Optional

from aiohttp import web
from aiohttp.abc import Request
from aiohttp.web_routedef import UrlDispatcher

from server.models import User, Rental
from server.serializer import JSendSchema, JSendStatus, UserSchema, RentalSchema
from server.service.users import get_users, get_user
from server.token_verify import verifier, TokenVerificationError
from server.views.base import BaseView
from server.views.utils import getter


class UsersView(BaseView):
    """
    Gets or adds to the list of users.
    """
    url = "/users"
    name = "users"

    async def get(self):
        return web.json_response(get_users())

    async def post(self):
        pass


class UserView(BaseView):
    """
    Gets, replaces or deletes a single user.
    """
    url = "/users/{id:[0-9]+}"
    name = "user"
    user_getter = getter(get_user, 'id', 'user_id')

    @user_getter
    async def get(self, user: User):
        response_schema = JSendSchema.of(UserSchema())
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": user.serialize()
        })
        return web.json_response(response_data)

    @user_getter
    async def put(self, user: User):
        pass

    @user_getter
    async def delete(self, user: User):
        await user.delete()
        response_schema = JSendSchema.of(UserSchema())
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": "deleted"
        })
        return web.json_response(response_data, status=204)


class UserRentalsView(BaseView):
    """
    Gets or adds to the users list of rentals.
    """
    url = "/users/{id:[0-9]+}/rentals"
    name = "user_rentals"

    async def get(self):
        response_schema = JSendSchema.of(RentalSchema(), many=True)
        rentals = await Rental.filter(user__id=self.request.match_info.get("id"))
        response_data = response_schema.dump({
            "status": JSendStatus.SUCCESS,
            "data": (rental.serialize() for rental in rentals)
        })

        return web.json_response(response_data)


class UserReservationsView(BaseView):
    """
    Gets or adds to the users' list of reservations.
    """
    url = "/users/{id:[0-9]+}/reservations"
    name = "user_reservations"

    async def get(self):
        pass

    async def post(self):
        pass


class UserIssuesView(BaseView):
    """
    Gets or adds to the users' list of issues.
    """
    url = "/users/{id:[0-9]+}/issues"
    name = "user_issues"

    async def get(self):
        pass

    async def post(self):
        pass


class MeView(BaseView):
    """
    Gets the data for the currently authenticated user.
    """

    url = "/users/me{tail:.*}"
    name = "me"

    @staticmethod
    async def me_handler(request: Request):
        """
        Accepts all types of request, does some checking against the user, and forwards them on to the appropriate user.
        """
        if "Authorization" not in request.headers or not request.headers["Authorization"].startswith("Bearer "):
            response_schema = JSendSchema()
            return web.json_response(response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"json": "You must supply your firebase token."}
            }), status=401)

        try:
            token = verifier.verify_token(request.headers["Authorization"][7:])
        except TokenVerificationError as error:
            response_schema = JSendSchema()
            return web.json_response(response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {"token": error.args}
            }), status=401)

        user = await get_user(firebase_id=token)

        if user is None:
            response_schema = JSendSchema()
            create_user_url = str(request.app.router['users'].url_for())
            return web.json_response(response_schema.dump({
                "status": JSendStatus.FAIL,
                "data": {
                    "authorization": "User does not exist. Please use your token to create a user and try again.",
                    "url": create_user_url,
                    "method": "POST"
                }
            }), status=401)

        concrete_url = MeView._get_concrete_user_url(request.path, request.match_info.get("tail"), user)
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
        id = user.id
        user_url = url_without_tail[:-2] + str(id)
        return user_url + tail

    @classmethod
    def register(cls, router: UrlDispatcher, base: Optional[str] = None):
        """Overrides the register function to register the me_handler for all request types."""
        url = base + cls.url if base is not None else cls.url
        router.add_route("*", url, cls.me_handler, name=cls.name)
