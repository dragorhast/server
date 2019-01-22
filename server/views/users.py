"""
User Related Views
-------------------------

Handles all the user CRUD
"""
from http import HTTPStatus

from aiohttp import web

from server.models import User
from server.permissions import UserMatchesFirebase
from server.permissions.decorators import requires
from server.permissions.permissions import ValidToken
from server.serializer import JSendSchema, JSendStatus, UserSchema, RentalSchema
from server.serializer.decorators import expects, returns
from server.serializer.models import CurrentRentalSchema, IssueSchema
from server.service.issues import get_issues, create_issue
from server.service.rentals import get_rentals
from server.service.users import get_users, get_user, delete_user, create_user, UserExistsError, update_user
from server.views.base import BaseView
from server.views.utils import match_getter


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
    @returns(JSendSchema.of(UserSchema()), HTTPStatus.CREATED)
    async def post(self):
        try:
            user = await create_user(**self.request["data"], firebase_id=self.request["token"])
        except UserExistsError:
            user = await User.get(firebase_id=self.request["token"])
            user = await update_user(user, **self.request["data"])

        return {
            "status": JSendStatus.SUCCESS,
            "data": user
        }


class UserView(BaseView):
    """
    Gets, replaces or deletes a single user.
    """
    url = "/users/{id:[0-9]+}"
    name = "user"
    user_getter = match_getter(get_user, 'user', user_id='id')

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
    @expects(UserSchema(only=('first', 'email')))
    @returns(JSendSchema.of(UserSchema()))
    async def put(self, user: User):
        user = await update_user(user, **self.request["data"])
        return {
            "status": JSendStatus.SUCCESS,
            "data": user
        }

    @user_getter
    @requires(UserMatchesFirebase())
    async def delete(self, user: User):
        await delete_user(user)
        raise web.HTTPNoContent


class UserRentalsView(BaseView):
    """
    Gets or adds to the users list of rentals.
    """
    url = "/users/{id:[0-9]+}/rentals"
    name = "user_rentals"
    with_user = match_getter(get_user, 'user', user_id='id')
    with_rentals = match_getter(get_rentals, 'rentals', user='id')

    @with_user
    @with_rentals
    @requires(UserMatchesFirebase())
    @returns(JSendSchema.of(RentalSchema(), many=True))
    async def get(self, user, rentals):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [await rental.serialize(self.rental_manager, self.request.app.router) for rental in rentals]
        }


class UserCurrentRentalView(BaseView):
    """
    Gets or ends the user's current rental.
    """
    url = "/users/{id:[0-9]+}/rentals/current"
    name = "user_current_rental"
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_user
    @requires(UserMatchesFirebase())
    @returns(
        no_rental=(JSendSchema(), HTTPStatus.NOT_FOUND),
        rental_exists=JSendSchema.of(CurrentRentalSchema(only=(
            'id', 'bike_id', 'bike_url', 'user_id', 'user_url', 'start_time',
            'is_active', 'estimated_price', 'start_location', 'current_location'
        )))
    )
    async def get(self, user: User):
        if user.id not in self.rental_manager.active_rental_ids:
            return "no_rental", {
                "status": JSendStatus.FAIL,
                "data": {"message": f"You have no current rental."}
            }

        current_rental, start_location, current_location = await self.rental_manager.active_rental(user,
                                                                                                   with_locations=True)
        return "rental_exists", {
            "status": JSendStatus.SUCCESS,
            "data": await current_rental.serialize(
                self.rental_manager,
                self.request.app.router,
                start_location=start_location,
                current_location=current_location
            )
        }

    @with_user
    @requires(UserMatchesFirebase())
    @returns(
        no_rental=(JSendSchema(), HTTPStatus.NOT_FOUND),
        rental_deleted=(JSendSchema.of(RentalSchema())),
    )
    async def delete(self, user: User):
        """Ends a rental."""
        if user.id not in self.rental_manager.active_rental_ids:
            return "no_rental", {
                "status": JSendStatus.FAIL,
                "data": {"message": f"You have no current rental."}
            }

        current_rental = await self.rental_manager.active_rental(user)
        await self.rental_manager.finish(current_rental)
        return "rental_deleted", {
            "status": JSendStatus.SUCCESS,
            "data": await current_rental.serialize(self.rental_manager, self.request.app.router)
        }


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
    with_issues = match_getter(get_issues, "issues", user_id='id')
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_issues
    @returns(JSendSchema.of(IssueSchema(), many=True))
    async def get(self, issues):
        return {
            "status": JSendStatus.SUCCESS,
            "data": [issue.serialize() for issue in issues]
        }

    @with_user
    @expects(IssueSchema(only=('bike_id', 'description')))
    @returns(JSendSchema.of(IssueSchema()))
    async def post(self):
        kwargs = {
            "description": self.request["data"]["description"]
        }
        if "bike_id" in self.request["data"]:
            kwargs["bike"] = self.request["data"]["bike_id"]

        return {
            "status": JSendStatus.SUCCESS,
            "data": (await create_issue(**kwargs)).serialize(self.request.app.router)
        }

    async def patch(self):
        """Allows someone to close their issue."""
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
                    "message": "User does not exist. Please use your token to create a user and try again.",
                    "url": create_user_url,
                    "method": "POST"
                }
            }), status=HTTPStatus.BAD_REQUEST)

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
