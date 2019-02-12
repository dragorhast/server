System Design
=============

The service is built to connect two things: a fleet of bikes, and a number of client apps. These interact through the
system via a web server. We have chosen to separate the app and the server as much as possible and, as such, the app
is completely standalone and is built as a static javascript file or app that can be deployed anywhere.

As such the server has no front end. It communicates exclusively in terms of data which is accessed and consumed by the
app. This API leverages JSON for its IO.

.. figure:: /_static/system.png
    :align: center

    High level overview of the system.

We have opted to use Python 3.6
on the server due to the number of libraries available to it as well as the flexibility and development speed gained with
its “gradual typing” system. This will enable us to rapidly build and prototype features. Using Python, asyncio, and
aiohttp this high-performing concurrent server will be optimised for serving an io-bound API. Using the async language
feature in python allows the server to handle multiple web requests or database accesses “at once” (but not in parallel).
Additionally, aiohttp renders real-time communication trivial with the support of web-sockets allowing any 2-way
communication such as chat, real-time updates, push notifications, etc. to be implemented with ease.

API Server Architecture
-----------------------

The architecture follows a three layered approach. First, the access layer, then the service layer, and lastly the data-
access layer.

#. **Access Layer**: consists of the websocket and RESTful apis, accepts the connections and commands from the app and
   bikes. Implemented as :mod:`~server.views`, each one representing a url.
#. **Service Layer**: implements the internal API and business logic of the program. Both the websockets interface and
   REST interface communicate with the program through this interface. Implemented in :mod:`~server.service`.
#. **Data Mapping Layer**: Handles loading and saving data to and from the database. Consists of many classes that
   handle serial and de-serialization of plain python objects. Implemented in :mod:`~server.store`.

The data mapping layer and access layers are just adapters to the outside world. The data mapping layer allows us to map
between our system and any choice of persistence store such as a database or even keep it in memory.
The access layer is an adapter between our internal python API and an external HTTP api.
The direction of control always goes down the layers. The access layer makes requests to the service layer, and so on,
but never the other way around.

Data IO
-------

A number of architectures can be used for APIs however one of the most commonly used is the `REST pattern`_ defined
by Roy Fielding. It defines a set of common practices for building highly scalable systems, and establishes a common
knowledge base so that developers and consumers of the same API can both predict what will happen without having to
constantly refer to the documentation. For example, a POST request to the rentals resource means creating a rental.

REST also requires the API to be stateless. Every request must send all the needed context to the server with every
request. Less server-side state means better horizontal scaling.

All data going in and out of the system is validated with one of the many serializers in :mod:`~server.serializer`.

.. _REST pattern: https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm

Bike Connectivity
-----------------

For handling the persistent connection with the bikes, we will use the web- socket compliant response included in
aiohttp. On connection, the bike is added to the list of connected bikes at which point commands can be sent to and
from it at will. If the bike disconnects, the system updates its status, and any attempts to send commands are met
with an exception. This solution is intentionally simple. While it models a complex concept (simultaneous, asynchronous,
duplex connections), async-await and aiohttp abstract the complexity really well.


Services
--------

The service layer is the business logic within which the rules and requirements of the system are specified.
These business rules are encapsulates inside a range of managers that each handle the core components of the system:

- Rental Manager
- Reservation Manager
- Bike Connection Manager
