from auth import check_news_access
from common.auth import AuthContext


def test_allows_caller_claiming_news_business_unit():
    ctx = AuthContext(user_id="u1", business_units=["news"], roles=[])
    assert check_news_access(ctx) is True


def test_allows_group_admin_role_regardless_of_business_unit():
    ctx = AuthContext(user_id="u1", business_units=[], roles=["group_admin"])
    assert check_news_access(ctx) is True


def test_denies_caller_with_unrelated_business_unit_and_no_allowed_role():
    ctx = AuthContext(user_id="u1", business_units=["tv"], roles=["mcn_tv_employee"])
    assert check_news_access(ctx) is False


def test_denies_caller_with_no_claims_at_all():
    ctx = AuthContext(user_id="anonymous", business_units=[], roles=[])
    assert check_news_access(ctx) is False
