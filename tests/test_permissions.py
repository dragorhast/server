import pytest

from server.permissions import Permission


class BoolPermission(Permission):

    def __init__(self, expected_bool):
        self.expected_bool = expected_bool

    async def __call__(self, actual: bool, **kwargs) -> None:
        if not actual == self.expected_bool:
            raise PermissionError(f"Got {actual}, expected {self.expected_bool}!")


class TestPermissionBoolean:
    true_permission = BoolPermission(True)
    false_permission = BoolPermission(False)

    or_permission = true_permission | false_permission
    and_permission = true_permission & false_permission

    not_true_permission = ~true_permission

    async def test_permission_passes(self):
        assert await self.true_permission(True) is None

    async def test_permission_fails(self):
        with pytest.raises(PermissionError):
            await self.true_permission(False)

    async def test_or_permission(self):
        assert await self.or_permission(True) is None

    async def test_or_permission_fail(self):
        try:
            assert await self.or_permission("FAIL")
        except PermissionError as e:
            assert len(e.args) == 2
            assert (isinstance(error, PermissionError) for error in e.args)
        else:
            pytest.fail()

    async def test_and_permission(self):
        try:
            assert await self.and_permission(True)
        except PermissionError as e:
            assert len(e.args) == 1
            assert (isinstance(error, PermissionError) for error in e.args)
        else:
            pytest.fail()

    async def test_not_permission(self):
        assert await self.not_true_permission(False) is None
        assert await self.not_true_permission("PASS") is None

    async def test_not_permission_fail(self):
        with pytest.raises(PermissionError):
            assert await self.not_true_permission(True)
