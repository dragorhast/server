import pytest
from aiohttp.web_request import Request
from aiohttp.web_urldispatcher import View

from server.permissions import Permission


class BoolPermission(Permission):

    def __init__(self, expected_bool):
        self.expected_bool = expected_bool

    async def __call__(self, request: Request, view: View) -> bool:
        if request == self.expected_bool:
            return True
        else:
            raise PermissionError


class TestPermissionBoolean:
    true_permission = BoolPermission(True)
    false_permission = BoolPermission(False)

    or_permission = true_permission | false_permission
    and_permission = true_permission & false_permission

    not_true_permission = ~true_permission
    not_false_permission = ~false_permission

    async def test_permission_passes(self):
        assert await self.true_permission(True, None)

    async def test_permission_fails(self):
        with pytest.raises(PermissionError):
            await self.true_permission(False, None)

    async def test_or_permission(self):
        assert await self.or_permission(True, None)

    async def test_or_permission_fail(self):
        try:
            assert await self.or_permission("FAIL", None)
        except PermissionError as e:
            assert len(e.args) == 2
            assert (isinstance(error, PermissionError) for error in e.args)
        else:
            pytest.fail()

    async def test_and_permission(self):
        try:
            assert await self.and_permission(True, None)
        except PermissionError as e:
            assert len(e.args) == 1
            assert (isinstance(error, PermissionError) for error in e.args)
        else:
            pytest.fail()
