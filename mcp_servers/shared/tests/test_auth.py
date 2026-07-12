from auth import check_shared_access
from common.auth import AuthContext


def test_allows_caller_claiming_any_business_unit():
    ctx = AuthContext(user_id="u1", business_units=["tv"], roles=[])
    assert check_shared_access(ctx) is True


def test_allows_group_admin_role_with_no_business_unit_claim():
    ctx = AuthContext(user_id="u1", business_units=[], roles=["group_admin"])
    assert check_shared_access(ctx) is True


def test_denies_caller_with_no_claims_at_all():
    ctx = AuthContext(user_id="anonymous", business_units=[], roles=[])
    assert check_shared_access(ctx) is False
