Data Design
===========

.. mermaid ::

    classDiagram
    User <|-- Issue : Created By
    User <|-- Rental : Created By
    Bike <|-- Rental : Uses
    Bike <|-- Issue : References
    User <|-- Reservation : Created By
    PickupPoint <|-- Reservation : Reserved At
    Rental <|-- RentalUpdate : Describes
    Bike <|-- LocationUpdate : Describes

    Bike : int id
    Bike : bytes public_key
    Bike : type
    Bike : bool locked
    Bike : is_connected()
    Bike : set_locked()

    LocationUpdate : int id
    LocationUpdate : Point location
    LocationUpdate : Bike bike
    LocationUpdate : datetime time

    User : int id
    User : bytes firebase_id
    User : str first
    User : str email

    Issue : int id
    Issue : User user
    Issue : Bike bike
    Issue : datetime time
    Issue : str description

    Rental : int id
    Rental : User user
    Rental : Bike bike
    Rental : float price

    RentalUpdate : int id
    RentalUpdate : Rental rental
    RentalUpdate : type
    RentalUpdate : datetime time

To support our design decisions we need to make accommodations in the way we store our data. We have opted to built an
event-sourced database for the bike state and location updates so that we minimize the chances of database inconsistency.
Having an immutable append-only database state at all times ensures that we can rely on the database as the sole source
of truth. This approach is not really appropriate for all cases, only situations where history is important.

Event Sourcing
--------------

System uses event-based approach for continuous data such as bike location and state. This means the location and the
current state of each bike is derived from a list of locations or state changes. Each event is a “delta” and “now” is
the result of applying each delta to some start state :math:`S_0`.

With this system, state can be mathematically expressed in the following way, where :math:`S_n` is the state after a given
number of updates “n”, and :math:`Δ_n` is the nth update:

:math:`S_n = Δ_n(Δ_{n-1}(Δ_{n-2}(...(Δ_1(S_0)))))`

Optimizations
-------------

Event sourcing provides some benefits such as full replayability of data (no data is overwritten only appended) and
safety guarantees which prevent inconsistent state. Full replayability also allows us to track bikes over time, and
do more in-depth analysis on patterns and usage than if we only had instantaneous location. There are some costs.
Naturally, saving every piece of data can be expensive, and filtering through thousands of points will also have a
performance cost. These can be mitigated by caching. If performance does become a problem, some potential solutions
are to:

- cache every 24 hours
- cache the current status every time there is a change
- cache the pickup point when entering and exiting

Geospatial Systems
------------------

There is a fairly large chunk of the system centered around spatial data, and we need to make sure that that is being
handled correctly. Bikes are expected to be issuing location updates quite frequently which need to be queryable
from the app, and pick-up points need to have the ability to determine their locations and the locations of bikes
within them.

Using geospatial data requires a few considerations. The most obvious of these is the database and persistence layer.
There are two convenient extensions that we can make use of for this purpose: PostGIS (a postgres extension) and
Spatialite (sqlite extension). The ORM we use (tortoise) does not support GIS data, so we'll need to come up with an
alternative for now.

Main packages for geospatial work:

- geopandas: an extension of pandas to support geo data
- shapely: manipulation and analysis of geometric objects
- fiona: reading / writing data into a wide array of formats

.. _`Rough Diagram`: https://www.draw.io/?sync=auto#G19cywQg9haU56ooBHvOwxTKpP9u3oMNoG

