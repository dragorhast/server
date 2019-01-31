Bike Communication Protocol
===========================

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

.. mermaid ::

    sequenceDiagram
    participant B as Bike
    participant S as Server
    Note left of B: POST request with public key.
    B ->> S: Public Key
    Note right of S: The key is checked against the known bike public keys.
    alt Foreign Public Key
    S ->> B: 401 Unauthorized
    else
    Note right of S: Auth ticket is made with IP, public key, and challenge.
    S ->> B: Challenge
    end
    Note left of B: The bike signs the challenge.
    Note left of B: The bike opens a web socket with the server.
    B ->> S: Public Key
    B ->> S: Signature
    Note right of S: The signature is verified against the public key.
    alt Signature Incorrect
    S ->> B: "fail"
    else
    S ->> B: "verified"
    B ->> S: "current-status"
    end

The last message in the pair process updates the server with the status of the bike, via a simple json update. Currently
this is only the locked status of the bike.

Communication
------------------

To handle the actual communication after the connection is made, we need to implement an application level protocol
on top of web sockets. A light-weight option is JSON RPC which supports both remote procedure calls and what they
call "notifications" or, simply, updates. Version 2 is explicitly designed for client-server communication, and has
increased resilience due to decoupling of the protocol and the transport.

The entire spec is available at `jsonrcp.org`_.

The bikes will implement a number of procedures such as ``lock`` and ``unlock`` as well as transmit ``location`` notifications
to the server whenever possible.

.. _`jsonrcp.org`: https://www.jsonrpc.org/specification
