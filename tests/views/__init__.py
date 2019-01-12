"""
Houses the tests for the REST api layer of the program. This layer is what manages the external API, and is
what external interface should use to speak through when communicating with the rest of the system.

This module is intended simply to test the REST interface.
The tests are set up primarily to assert that
the formatting of the responses remains stable,
and that the system throws the expected errors
when interacted with incorrectly.
This means that the service layer is replaced
with a mock version that returns predictable
responses such that (ideally) it will never catch errors
with the rest of the system, only the views.
"""
