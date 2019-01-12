Rentals
=======

Starting a Rental
-----------------

It is most logical that a rental is created on a bike resource.
This metaphor matches real life the best, as it resembles picking bike off the rack.
A user may start a rental on any bike that is not currently in use, by simply
sending a POST request to the bike's rentals resource ``/api/v1/bikes/rentals``
with the user's firebase token.

.. note :: If the user already has an active rental, the request will fail.

If the request correctly goes through, the system will return a
:class:`~server.serializer.models.RentalSchema`.

Ending a Rental
---------------

To end a rental, send a DELETE request to ``/api/v1/users/me/rentals/current``.
The system then returns a :class:`~server.serializer.models.RentalSchema`
with the final price and end time included.