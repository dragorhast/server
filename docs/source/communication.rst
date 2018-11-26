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
        B ->> S: Signature
        Note right of S: The signature is verified against the public key.
        alt Signature Incorrect
        S ->> B: "fail"
        else
        S ->> B: "verified"
        end