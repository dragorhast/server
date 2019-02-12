import pytest

from server.service.verify_token import DummyVerifier, TokenVerificationError, FirebaseVerifier

keys = {
    '97fcbca368fe77808830c8100121ec7bde22cf0e': """-----BEGIN CERTIFICATE-----
MIIDHDCCAgSgAwIBAgIICakczwC7SlUwDQYJKoZIhvcNAQEFBQAwMTEvMC0GA1UE
AxMmc2VjdXJldG9rZW4uc3lzdGVtLmdzZXJ2aWNlYWNjb3VudC5jb20wHhcNMTkw
MjA1MjEyMDQ3WhcNMTkwMjIyMDkzNTQ3WjAxMS8wLQYDVQQDEyZzZWN1cmV0b2tl
bi5zeXN0ZW0uZ3NlcnZpY2VhY2NvdW50LmNvbTCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAIVcuVyRNv4E/5cU70ZfWrocgTlExMSsvFEGpsZ2POkpHCIg
/xdRKZ1OGpvsMI9V1j03lCVYHquYibC4ui7QL3e5pE+UYWtn7NvKfyt/UbXPOJF9
3eCuoKl4+iBD9eUkV2TvkWBLk1zX55pJnCiY5igpgwYfoidS6PpbbzlUTBP/avNu
DfPvVv6wKj09EcSkST3xCsKS1hJL3N1AbgnDoMDxIIcwp68KtlmVky5GYbMwYfan
kzoJQeDoXeCDPUR/0DMPdK45RwWoSpE1gWfdcBk5X8o/XuPTUN5ER3l5ogL87dhH
m1qtbyvArbJ801/e5xqtB8KPc6UmXAjihhThgTcCAwEAAaM4MDYwDAYDVR0TAQH/
BAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwDQYJ
KoZIhvcNAQEFBQADggEBACb1vhk2sGa4x8fwzOaSMxLBLVwQ79AQoQj3wMfYCopN
ox56/QCPDrOe0qPQ53UrvBXpa7jRJLBnRsIkBfJZ70SAUX7HsM2PAtcWl5wu5+nn
9v/ePboAJHnxMnv3ot/pgdSYL2XzUL7YMbqVvIyPDZ+b2kwn+fa/bEMHjBXiBRTb
ohBmu3Qoicl2fvatGVx+5jx9cMZQP3mlvxAl1MkMsXbtYFLhuS/AP2kX3alImWHU
hlg+7qvazybKScAYQsx8lL0ZoRnYauF25W7a9uimv/uEMCub7mVJ9gl5PtccauxZ
XQvqhmBcMI82kLOjy5KNeo/IoR7FUxWRa12VIQtcVUI=
-----END CERTIFICATE-----""",
    'b2e460ff3a3d46dfec724d8484f73476c13e20cf': """-----BEGIN CERTIFICATE-----
MIIDHDCCAgSgAwIBAgIIOCX6XCjtRIIwDQYJKoZIhvcNAQEFBQAwMTEvMC0GA1UE
AxMmc2VjdXJldG9rZW4uc3lzdGVtLmdzZXJ2aWNlYWNjb3VudC5jb20wHhcNMTkw
MTI4MjEyMDQ3WhcNMTkwMjE0MDkzNTQ3WjAxMS8wLQYDVQQDEyZzZWN1cmV0b2tl
bi5zeXN0ZW0uZ3NlcnZpY2VhY2NvdW50LmNvbTCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAM73bq2rKx7EhDfMCJ0lgHcUpZh/9YQOTbYifIYKPBT5dkyq
7jqz8niwgfvkR+Gn2+Fm/SguAe58kEEuKzoSJO7zUoIq+W0Dr6fcpHcCWRMbCEmF
KcnmczAiu2OrdA0gmIoobnHaJZNISNXpyIabTFAP+wUVStJVI+RqubsQqhH/siro
/dQyA2gD71rGh7HWB7mEQfu4Nq58j97QtzEOBbJLmiaDr+eR/N0/w8qqwqRBGCta
xpD/cTT10Z30DaUCBf7yuFbftZPYPaaVqVeWVmTR8cOIBjY8TRK28e7p2v52L54X
QNrcOjoZDAOmv4zFv5VCPcaYn9ZS9WU/vaXtpaUCAwEAAaM4MDYwDAYDVR0TAQH/
BAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwIwDQYJ
KoZIhvcNAQEFBQADggEBAGC1Zcz6GYensl10+IJzHFTOcbh7ubhPby7jNV+WN4ET
Fmv1ZAY29DQ/EjRIzbJcXof6O+XyIun9iCfmFRkRcFvX6OP1cTgUn+6axMZF+Mzk
rVH7IyPPrDXv6P2GcUtZerESk9IdmaqvT2ypv01emdFdPgOn3LzKz/G2ihSboGUR
mRVZmEKh2aVk1x5PVZ8tMeEwf9CSXAei/1fbynFGV6vGjqxiLKlnkhBktqcLIcVr
rFKYlJJTei7dAib+NRKpGOVPG+8K8TpLcSKrizKgl7R2vkP3fbWowjXzR/8PAw8k
4tKg21lg9MVOCgDNq27018p+fSTcDbdz2t7eTZF0Ov0=
-----END CERTIFICATE-----"""
}


@pytest.fixture
async def firebase_verifier(loop):
    verifier = FirebaseVerifier("dragorhast-420")
    verifier._certificates = keys
    return verifier


@pytest.fixture
async def dummy_verifier(loop):
    return DummyVerifier()


class TestFirebaseVerifier:

    @pytest.mark.parametrize(('token', 'passes'), [
        (
        "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijk3ZmNiY2EzNjhmZTc3ODA4ODMwYzgxMDAxMjFlYzdiZGUyMmNmMGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZHJhZ29yaGFzdC00MjAiLCJhdWQiOiJkcmFnb3JoYXN0LTQyMCIsImF1dGhfdGltZSI6MTU0OTgzOTEzNywidXNlcl9pZCI6Ik95d3NVeTRSRUpmcmNaMG1UQmI0ejRLQzBHSzIiLCJzdWIiOiJPeXdzVXk0UkVKZnJjWjBtVEJiNHo0S0MwR0syIiwiaWF0IjoxNTQ5ODM5MTM3LCJleHAiOjE1NDk4NDI3MzcsImVtYWlsIjoiYXJseW9uQG1lLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJhcmx5b25AbWUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.L97xPMoz1f2eJGpC4TmUgNL5G9WT_BM2eIEzqfFOUmeJUohozd6AG4di5fBuiuQmnSrnUpJ6hq_JPjmSWcnhjEou4qmY5ho2pZkuHnKI5UCs116UXUYykbM_Mynihzp6goDVc8UCCAnro6dr5gyQ6So4LssnRkaYku7EvHGP8txlsny-3c2yoOtnpqOaQnBUMy59XIjtXgRRRDJHtMma4CFtmEI4ZcvlJE7iDzkUIH3Y-JjDXfOYJjBHUU62i6zdblUPqUspR7_h1KQcWCz5M68Woy8Emt9k-r2mB5mGg5OrpsUmnp7EbgBbin6TZ1Y_zplyOJlcRAyyXIp6hUUenQ",
        True),
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
