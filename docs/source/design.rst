System Design
=============

The server is exclusively going to provide endpoints for use by the web and mobile apps. We have opted to use Python 3.7
on the server due to the number of libraries available to it as well as the flexibility and development speed gained with
its “gradual typing” system. This will enable us to rapidly build and prototype features. Using Python, asyncio, and
aiohttp this high-performing concurrent server will be optimised for serving an io-bound API. Using the async language
feature in python allows the server to handle multiple web requests or database accesses “at once” (but not in parallel).
Additionally, aiohttp renders real-time communication trivial with the support of web-sockets allowing any 2-way
communication such as chat, real-time updates, push notifications, etc. to be implemented with ease.

Rest API
--------

A number of design patterns can be used for APIs however one of the most commonly used is the REST pattern defined
by Roy Fielding. Using a logical, structured, hierarchical structure we hope to make the API as intuitive as possible.
Additionally, a versioned, stateless, and immutable API will allow for independent development between the server and
the app. When breaking changes are made, a version is published and the changes are made in the application at the app
developers leisure (hopefully sooner rather than later).

Bike Connection
---------------

For handling the persistent connection with the bikes, we will use the web- socket compliant response included in
aiohttp. On connection, the bike is added to the list of connected bikes at which point commands can be sent to and
from it at will. If the bike disconnects, the system updates its status, and any attempts to send commands are met
with an exception. This solution is intentionally simple. While it models a complex concept (simultaneous, asynchronous,
duplex connections), async-await and aiohttp abstract the complexity really well.

Open Source
-----------

Additionally we believe that our platform should be open, and that our work— while needing to turn a small profit—can
also benefit the community. With this in mind, we are also enabling CORS on the server to allow others unrestricted
access to our APIs. This does not mean, however, that anyone can access any data from the server, only that others may
develop apps on our platform if, for example, they really wanted an android wear app. Using revocable API keys we
provide a powerful authentication system independent of any GUI.
