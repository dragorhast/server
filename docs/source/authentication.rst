Client Authentication
=====================

The system uses Firebase to handle authentication and session management. This is done for a few reasons:

- time constraints
- reduced server-side state

To do this, the client authenticates with firebase, and simply hands the server its ID token which is then verified
against Google's cryptographic key using RS256. A valid token means the client has a valid session.

A token is refreshed every hour

Revocation
----------

These tokens are completely stateless and as such contain no information about their validity. It is plausible that,
under specific conditions, the system would like to revoke a token.

This cannot be handled without a request to the server.
