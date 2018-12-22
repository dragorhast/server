"""
Houses the tests for the service layer of the program. This layer is what manages the internal API, and is
what any interface should use to speak through when communicating with the rest of the system.

Asynchronous tests (those using "await") must be marked with an asynchronous marker ``@pytest.mark.asyncio``
to signify to pytest that the function is async. Otherwise it will not run correctly.
"""