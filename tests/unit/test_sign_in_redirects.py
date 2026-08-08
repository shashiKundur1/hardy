import pytest

from src.auth.constants import SHOP_HOME
from src.auth.router import safe_next

OFF_SITE = (
    "https://evil.example/steal",
    "//evil.example/steal",
    "/\\evil.example/steal",
    "http://evil.example",
    "javascript:alert(1)",
    "",
    None,
)

ON_SITE = ("/shop", "/category/cookware", "/product/12", "/footprint?page=2")


@pytest.mark.parametrize("target", OFF_SITE)
def test_a_target_that_leaves_hardy_is_refused(target):
    assert safe_next(target) == SHOP_HOME


@pytest.mark.parametrize("target", ON_SITE)
def test_a_target_inside_hardy_survives(target):
    assert safe_next(target) == target
