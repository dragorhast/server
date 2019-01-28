import pytest

from server.permissions import Permission
from server.permissions.permission import RoutePermissionError


@pytest.fixture
def true_permission():
    return BoolPermission(True)


@pytest.fixture
def false_permission():
    return BoolPermission(False)


class BoolPermission(Permission):

    def __init__(self, expected_bool):
        self.expected_bool = expected_bool

    async def __call__(self, actual: bool, **kwargs) -> None:
        if not actual == self.expected_bool:
            raise RoutePermissionError(f"Got {actual}, expected {self.expected_bool}!")


class TestPermissionBoolean:

    true_permission = BoolPermission(True)
    false_permission = BoolPermission(False)

    async def test_permission_passes(self, true_permission):
        """Assert that calling a permission that passes does not raise."""
        assert await true_permission(True) is None

    async def test_permission_fails(self, true_permission):
        """Assert that calling a permission that fails raises a RoutePermissionError"""
        with pytest.raises(RoutePermissionError):
            await true_permission(False)

    async def test_or_permission(self, true_permission, false_permission):
        or_permission = true_permission | false_permission
        assert await or_permission(True) is None

    async def test_or_permission_fail(self, true_permission, false_permission):
        or_permission = true_permission | false_permission
        try:
            assert await or_permission("FAIL")
        except RoutePermissionError as e:
            assert len(e.sub_errors) == 2
            assert (isinstance(error, RoutePermissionError) for error in e.args)
        else:
            pytest.fail()

    @pytest.mark.parametrize(
        "permission,length", [
            (true_permission | true_permission | false_permission, 3),
            (true_permission | (false_permission | false_permission), 3),
        ]
    )
    async def test_or_permission_chaining(self, permission, length):
        assert len(permission) == 3

    async def test_and_permission(self, true_permission, false_permission):
        and_permission = true_permission & false_permission
        try:
            assert await and_permission(True)
        except RoutePermissionError as e:
            assert len(e.sub_errors) == 1
            assert (isinstance(error, RoutePermissionError) for error in e.args)
        else:
            pytest.fail()

    @pytest.mark.parametrize(
        "permission,length", [
            ((true_permission | false_permission) & false_permission & (false_permission & true_permission), 4),
            ((true_permission & false_permission & false_permission), 3)
        ]
    )
    async def test_and_permission_chaining(self, permission, length):
        assert len(permission) == length

    async def test_not_permission(self, true_permission):
        not_true_permission = ~true_permission
        assert await not_true_permission(False) is None
        assert await not_true_permission("PASS") is None

    async def test_not_permission_fail(self, true_permission):
        not_true_permission = ~true_permission
        with pytest.raises(RoutePermissionError):
            assert await not_true_permission(True)
