Client Authentication
=====================

The system uses Firebase to handle authentication and session management. This is done for a few reasons:

- time constraints
- reduced server-side state

To do this, the client authenticates with firebase, and simply hands the server its ID token which is then verified
against Google's cryptographic key using RS256. A valid token means the client has a valid session. All authenticated
requests are made by sending this token to the server, which is then checked against a series of constraints
(for more info see `Firebase Verification`_).

.. _Firebase Verification: https://firebase.google.com/docs/auth/admin/verify-id-tokens#verify_id_tokens_using_a_third-party_jwt_library

Revocation
----------

These tokens are completely stateless and as such contain no information about their validity. It is plausible that,
under specific conditions, the system would like to revoke a token. If a user revokes all sessions, the tokens would
still be valid for at most one hour. The only way around this is to check every authenticated request against Firebase
which is infeasible. At this point, we have decided to accept this window of vulnerability, given how little risk
a compromised account poses.
