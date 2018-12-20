System Design
=============

The server is exclusively going to provide endpoints for use by the web and mobile apps. We have opted to use Python 3.7
on the server due to the number of libraries available to it as well as the flexibility and development speed gained with
its “gradual typing” system. This will enable us to rapidly build and prototype features. Using Python, asyncio, and
aiohttp this high-performing concurrent server will be optimised for serving an io-bound API. Using the async language
feature in python allows the server to handle multiple web requests or database accesses “at once” (but not in parallel).
Additionally, aiohttp renders real-time communication trivial with the support of web-sockets allowing any 2-way
communication such as chat, real-time updates, push notifications, etc. to be implemented with ease.

High Level
----------

The service is built to connect two things: a fleet of bikes, and a number of client apps. These interact through the
system via a web server.

Rest API
~~~~~~~~

A number of design patterns can be used for APIs however one of the most commonly used is the REST pattern defined
by Roy Fielding. Using a logical, structured, hierarchical structure we hope to make the API as intuitive as possible.
Additionally, a versioned, stateless, and immutable API will allow for independent development between the server and
the app. When breaking changes are made, a version is published and the changes are made in the application at the app
developers leisure (hopefully sooner rather than later).

Bike Connection
~~~~~~~~~~~~~~~

For handling the persistent connection with the bikes, we will use the web- socket compliant response included in
aiohttp. On connection, the bike is added to the list of connected bikes at which point commands can be sent to and
from it at will. If the bike disconnects, the system updates its status, and any attempts to send commands are met
with an exception. This solution is intentionally simple. While it models a complex concept (simultaneous, asynchronous,
duplex connections), async-await and aiohttp abstract the complexity really well.

Architecture
------------

The architecture follows a three layered approach. First, the access layer, then the service layer, and lastly the data-
access layer.

#. **Access Layer**: consists of the websocket and RESTful apis, accepts the connections and commands from the app and
   bikes. Implemented as :mod:`~server.views`, each one representing a url.
#. **Service Layer**: implements the internal API and business logic of the program. Both the websockets interface and
   REST interface communicate with the program through this interface. Implemented in :mod:`~server.service`.
#. **Data Mapping Layer**: Handles loading and saving data to and from the database. Consists of many classes that
   handle serial and de-serialization of plain python objects. Implemented in :mod:`~server.store`.

The data mapping layer and access layers are just adapters to the outside world. The data mapping layer allows us to map
between our system and any choice of persistence store such as :mod:`~server.store.postgres`, or even keep it in
:mod:`~server.store.memory`. The access layer is an adapter between our internal python API and an external HTTP api.
The direction of control always goes down the layers. The access layer makes requests to the service layer, and so on,
but never the other way around.

With this in mind, :mod:`~server.permissions` and :mod:`~server.models` are primarily an implementation detail of the
service layer. The access layer may need to do some operations on models given to it from the service layer, but will
never create them itself.