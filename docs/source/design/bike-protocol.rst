Bike Communication Protocol
===========================

Every bike is connected to the server with a long-lasting websocket link. This allows us to always issue commands to the
bike from the server and is critical to the ease of use of the system, when compared with competitors. Being able to
issue commands such as "lock now" powers the system's flexibility. Websockets has no application layer protocols, which
has meant that we have had to build a communication protocol.

Authentication
--------------

To ensure the authenticity of the bikes, we use a public key cryptographic signature scheme called Ed25519. This allows
us to ensure that the bike has the secret key (read: is genuine) without having to ever share the password.

Websockets, unlike typical HTTP, doesn't provide authentication built in. So, to ensure that we are communicating with a
genuine bike, we need a method to securely establish proof of identity. This is done via a private key. This allows us
to assign a unique key to each bike and have them prove that they are who they are when the session is opened.

This provides improved security over a password, by preventing something called a replay attack in which an attacker
captures your authentication packets and re-uses them to authenticate in the future without ever seeing the
password. Requiring the bikes to sign a one time challenge stops that entirely, because no useful information is ever
sent.

Once the bike connects, it sends its current state to the server as which point we are now able to send JSON-RPC calls
over the socket.

.. mermaid::

    sequenceDiagram
    participant B as Bike
    participant S as Server
    Note left of B: POST Public Key
    B ->> S: Public Key
    alt Foreign Public Key
    S ->> B: 401 Unauthorized
    else
    Note right of S: Create Ticket
    S ->> B: Challenge
    end
    Note left of B: Sign Challenge
    Note left of B: Websocket
    B ->> S: Public Key
    B ->> S: Signature
    Note right of S: Verify Signature
    alt Signature Incorrect
    S ->> B: "fail"
    else
    S ->> B: "verified"
    B ->> S: "current-status"
    end

JSON RPC
------------------

To handle the actual communication after the connection is made, we need to implement an application level protocol
on top of web sockets. A light-weight option is JSON RPC which supports both remote procedure calls and what they
call "notifications" or, simply, updates. Version 2 is explicitly designed for client-server communication, and has
increased resilience due to decoupling of the protocol and the transport.

The entire spec is available at `jsonrpc.org`_.

The bikes implement a number of procedures such as ``lock`` and ``unlock`` as well as transmitting ``locationUpdate``
notifications to the server whenever possible. These updates are archived and used to query the location of the bike.

.. _`jsonrpc.org`: https://www.jsonrpc.org/specification
