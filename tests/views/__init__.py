"""
Houses the tests for the REST api layer of the program. This layer is what manages the external API, and is
what external interface should use to speak through when communicating with the rest of the system.

These tests do not need to be marked with the pytest async marker, and will be run automatically by aiohttp.
"""