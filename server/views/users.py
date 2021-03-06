"""
User Related Views
-------------------------

Handles all the user CRUD
"""
from http import HTTPStatus
from typing import List

from aiohttp import web
from aiohttp_apispec import docs
from marshmallow.fields import String, Url

from server.models import User, Rental, Reservation
from server.permissions import UserMatchesToken, UserIsAdmin, requires, ValidToken
from server.serializer import JSendSchema, JSendStatus
from server.serializer.decorators import expects, returns
from server.serializer.fields import Many
from server.serializer.misc import PaymentSourceSchema
from server.serializer.models import CurrentRentalSchema, IssueSchema, UserSchema, RentalSchema, ReservationSchema, \
    CurrentReservationSchema
from server.service.access.bikes import get_bike
from server.service.access.issues import get_issues, open_issue
from server.service.access.rentals import get_rentals
from server.service.access.reservations import current_reservations, get_user_reservations
from server.service.access.users import get_users, get_user, delete_user, create_user, UserExistsError, update_user
from server.views.base import BaseView
from server.views.decorators import match_getter, GetFrom

USER_IDENTIFIER_REGEX = "(?!me)[^{}/]+"


class UsersView(BaseView):
    """
    Gets or adds to the list of users.
    """
    url = "/users"
    name = "users"
    with_user = match_getter(get_user, 'user', firebase_id=GetFrom.AUTH_HEADER)

    @with_user
    @docs(summary="Get All Users")
    @requires(UserIsAdmin())
    @expects(None)
    @returns(JSendSchema.of(users=Many(UserSchema())))
    async def get(self, user):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"users": await get_users()}
        }

    @docs(summary="Create A User")
    @requires(ValidToken())
    @expects(UserSchema(only=('first', 'email')))
    @returns(JSendSchema.of(user=UserSchema()))
    async def post(self):
        """
        Anyone who has already authenticated with firebase can then create a user in the system.
        This must be done before you use the rest of the system, but only has to be done once.
        """
        try:
            user = await create_user(**self.request["data"], firebase_id=self.request["token"])
        except UserExistsError:
            user = await get_user(firebase_id=self.request["token"])
            user = await update_user(user, **self.request["data"])

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"user": user}
        }


class UserView(BaseView):
    """
    Gets, replaces or deletes a single user.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}"
    name = "user"
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_user
    @docs(summary="Get A User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @expects(None)
    @returns(JSendSchema.of(user=UserSchema()))
    async def get(self, user: User):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"user": user.serialize()}
        }

    @with_user
    @docs(summary="Replace A User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @expects(UserSchema(only=('first', 'email')))
    @returns(JSendSchema.of(user=UserSchema()))
    async def put(self, user: User):
        user = await update_user(user, **self.request["data"])
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"user": user}
        }

    @with_user
    @docs(summary="Delete A User")
    @requires(UserMatchesToken() | UserIsAdmin())
    async def delete(self, user: User):
        if user.can_pay:
            await self.payment_manager.delete_customer(user)
        await delete_user(user)
        raise web.HTTPNoContent


class UserPaymentView(BaseView):
    """
    Allows a user to get or replace their payment details.
    """

    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/payment"
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_user
    @docs(summary="Check For Existence Of Payment Details")
    @returns(None)
    async def get(self, user: User):
        if user.can_pay:
            raise web.HTTPOk
        else:
            raise web.HTTPNoContent

    @with_user
    @docs(summary="Add Or Replace Payment Details")
    @expects(PaymentSourceSchema())
    async def put(self, user: User):
        if user.can_pay:
            await self.payment_manager.update_customer(user, self.request["data"]["token"])
        else:
            await self.payment_manager.create_customer(user, self.request["data"]["token"])

        raise web.HTTPOk

    @with_user
    @docs(summary="Delete Payment Details")
    @returns(
        active_rental=JSendSchema.of(rental=RentalSchema(), message=String(), url=Url(relative=True)),
        no_details=(None, web.HTTPNotFound),
        deleted=(None, web.HTTPNoContent),
    )
    async def delete(self, user: User):

        rental = await self.rental_manager.active_rental(user)

        if rental is not None:
            return "active_rental", {
                "status": JSendStatus.FAIL,
                "data": {
                    "message": "You cannot delete your payment details with an active rental.",
                    "url": self.request.app.router["rental"].url_for(id=str(rental.id)).path
                }
            }
        elif not user.can_pay:
            return "no_details", None
        else:
            await self.payment_manager.delete_customer(user)
            return "deleted", None


class UserRentalsView(BaseView):
    """
    Gets or adds to the users list of rentals.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/rentals"
    name = "user_rentals"
    with_user = match_getter(get_user, 'user', user_id='id')
    with_rentals = match_getter(get_rentals, 'rentals', user='id')

    @with_user
    @with_rentals
    @docs(summary="Get All Rentals For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(JSendSchema.of(rentals=Many(RentalSchema())))
    async def get(self, user, rentals: List[Rental]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {
                "rentals": [await rental.serialize(self.rental_manager, self.request.app.router) for rental in rentals]}
        }


class UserCurrentRentalView(BaseView):
    """
    Gets or ends the user's current rental.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/rentals/current"
    name = "user_current_rental"
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_user
    @docs(summary="Get Current Rental For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(
        no_rental=(JSendSchema(), web.HTTPNotFound),
        rental_exists=JSendSchema.of(rental=CurrentRentalSchema(only=(
            'id', 'bike_identifier', 'bike_url', 'user_id', 'user_url', 'start_time',
            'is_active', 'estimated_price', 'start_location', 'current_location'
        )))
    )
    async def get(self, user: User):
        if not self.rental_manager.has_active_rental(user):
            return "no_rental", {
                "status": JSendStatus.FAIL,
                "data": {"message": f"You have no current rental."}
            }

        current_rental, start_location, current_location = await self.rental_manager.active_rental(user,
                                                                                                   with_locations=True)
        return "rental_exists", {
            "status": JSendStatus.SUCCESS,
            "data": {"rental": await current_rental.serialize(
                self.rental_manager,
                self.bike_connection_manager,
                self.reservation_manager,
                self.request.app.router,
                start_location=start_location,
                current_location=current_location
            )}
        }


class UserEndCurrentRentalView(BaseView):
    """"""

    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/rentals/current/{{action}}"
    name = "user_end_current_rental"
    with_user = match_getter(get_user, 'user', user_id='id')
    actions = ("cancel", "complete")

    @with_user
    @docs(summary="End Rental For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(
        no_rental=(JSendSchema(), web.HTTPNotFound),
        invalid_action=(JSendSchema(), web.HTTPNotFound),
        rental_completed=JSendSchema.of(rental=RentalSchema(), action=String(), receipt_url=Url(allow_none=True)),
    )
    async def patch(self, user: User):
        """
        Ends a rental for a user, in one of two ways:

        - ``PATCH /users/me/rentals/current/cancel`` cancels the rental
        - ``PATCH /users/me/rentals/current/complete`` completes the rental
        """

        if not self.rental_manager.has_active_rental(user):
            return "no_rental", {
                "status": JSendStatus.FAIL,
                "data": {"message": "You have no current rental."}
            }

        end_type = self.request.match_info["action"]
        if end_type not in self.actions:
            return "invalid_action", {
                "status": JSendStatus.FAIL,
                "data": {
                    "message": f"Invalid action. Pick between {', '.join(self.actions)}",
                    "actions": self.actions
                }
            }

        if end_type == "complete":
            rental, receipt_url = await self.rental_manager.finish(user)
        elif end_type == "cancel":
            rental = await self.rental_manager.cancel(user)
            receipt_url = None
        else:
            raise Exception

        return "rental_completed", {
            "status": JSendStatus.SUCCESS,
            "data": {
                "rental": await rental.serialize(self.rental_manager, self.bike_connection_manager,
                                                 self.reservation_manager,
                                                 self.request.app.router),
                "action": "canceled" if end_type == "cancel" else "completed",
                "receipt_url": receipt_url,
            }
        }


class UserReservationsView(BaseView):
    """
    Gets the users' list of reservations.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/reservations"
    name = "user_reservations"

    with_user = match_getter(get_user, "user", user_id="id")
    with_reservations = match_getter(get_user_reservations, "reservations", user="id")

    @with_user
    @with_reservations
    @docs(summary="Get All Reservations For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(JSendSchema.of(reservations=Many(ReservationSchema())))
    async def get(self, user, reservations: List[Reservation]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"reservations": [reservation.serialize(self.request.app.router, self.reservation_manager) for
                                      reservation in reservations]}
        }


class UserCurrentReservationView(BaseView):
    """
    Gets the users' current reservation.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/reservations/current"

    with_reservation = match_getter(current_reservations, "reservations", user="id")
    with_user = match_getter(get_user, "user", user_id="id")

    @with_user
    @with_reservation
    @docs(summary="Get Current Reservations For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(JSendSchema.of(reservations=Many(CurrentReservationSchema())))
    async def get(self, user, reservations: List[Reservation]):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"reservations": [reservation.serialize(self.request.app.router, self.reservation_manager) for
                                      reservation in reservations]}
        }


class UserIssuesView(BaseView):
    """
    Gets or adds to the users' list of issues.
    """
    url = f"/users/{{id:{USER_IDENTIFIER_REGEX}}}/issues"
    name = "user_issues"
    with_issues = match_getter(get_issues, "issues", user='id')
    with_user = match_getter(get_user, 'user', user_id='id')

    @with_user
    @with_issues
    @docs(summary="Get All Issues For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @returns(JSendSchema.of(issues=Many(IssueSchema())))
    async def get(self, user, issues):
        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issues": [issue.serialize(self.request.app.router) for issue in issues]}
        }

    @with_user
    @docs(summary="Open Issue For User")
    @requires(UserMatchesToken() | UserIsAdmin())
    @expects(IssueSchema(only=('description', 'bike_identifier')))
    @returns(
        JSendSchema.of(issue=IssueSchema(only=('id', 'user_id', 'user_url', 'bike_identifier', 'description', 'opened_at'))))
    async def post(self, user):
        issue_data = {
            "description": self.request["data"]["description"],
            "user": user
        }

        if "bike_identifier" in self.request["data"]:
            issue_data["bike"] = await get_bike(identifier=self.request["data"]["bike_identifier"])

        issue = await open_issue(**issue_data)

        return {
            "status": JSendStatus.SUCCESS,
            "data": {"issue": issue.serialize(self.request.app.router)}
        }


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
                    "message": "User does not exist. Please use your jwt to create a user and try again.",
                    "url": create_user_url,
                    "method": "POST"
                }
            }), status=HTTPStatus.BAD_REQUEST)

        concrete_url = MeView._get_concrete_user_url(self.request.path, self.request.match_info.get("tail"), user)
        raise web.HTTPTemporaryRedirect(concrete_url)

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
