import pytest

from server.service.verify_token import DummyVerifier, TokenVerificationError, FirebaseVerifier

keys = None


@pytest.fixture
async def firebase_verifier(loop):
    global keys
    verifier = FirebaseVerifier("dragorhast-420")
    if keys is None:
        await verifier.get_keys()
        keys = verifier._certificates
    else:
        verifier._certificates = keys
    return verifier


@pytest.fixture
async def dummy_verifier(loop):
    return DummyVerifier()


class TestFirebaseVerifier:

    @pytest.mark.parametrize(('token', 'passes'), [
        ("eyJhbGciOiJSUzI1NiIsImtpZCI6IjkxZmM2MDg1OGUxYzQxMzNjODIyMTZkNTNkZDE3OWZhNDFmODQzMGMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZHJhZ29yaGFzdC00MjAiLCJhdWQiOiJkcmFnb3JoYXN0LTQyMCIsImF1dGhfdGltZSI6MTU0NzcyMjgwOCwidXNlcl9pZCI6IlhtejZ2VENiblpickM3bHFYaVhUQWE3RnBlVDIiLCJzdWIiOiJYbXo2dlRDYm5aYnJDN2xxWGlYVEFhN0ZwZVQyIiwiaWF0IjoxNTQ4MDY4NjczLCJleHAiOjE1NDgwNzIyNzMsImVtYWlsIjoidGVzdDFAdGVzdC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsidGVzdDFAdGVzdC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ.klTschPiOp259_vDPGlDE4d0yO0pAWxgGBORLobbw6kOSaKrTH3bTjkZh_20USbb3zbv40VwTUbP7ZicNEbSO0uUEy3odkFYdVhQ5J2294v1Cexej78duGClqF-g9b8iSnNTrcfrfi_6qS_G2C062Ws-dz6hjHupc1cByajw2edSWSRy8ZXKQFX9W4KXhhEJt51q0M0mbfx7yKn3Q4Imns26_4GSdLTnKdWoPenYHdJR7Ztu8PxGWMn2Em5KgDFlLygLixc4wgKDuEo2rGvn7LLM6rUXvLw96YjFKjhCk6yS7QePCAKF4VdhKxgTy6dDztPIDkx2Xd4Kb_fD_8uj6w", True),
        ("shit", False),
        (None, False),
        (False, False),
        (213, False)
    ])
    async def test_verify(self, loop, firebase_verifier, token, passes: bool):
        try:
            firebase_verifier.verify_token(token, verify_exp=False)
            assert passes
        except TokenVerificationError as e:
            assert not passes
        except TypeError:
            assert not passes


class TestDummyVerifier:

    @pytest.mark.parametrize(('token', 'passes'), [
        ("abcd", True),
        (1234, False),
        (None, False),
        ("xp123", False),
        ("", True)
    ])
    async def test_verify(self, loop, dummy_verifier, token, passes: bool):
        try:
            dummy_verifier.verify_token(token)
            assert passes
        except TokenVerificationError:
            assert not passes
