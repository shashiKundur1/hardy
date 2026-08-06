import schemathesis

from src.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

public = schema.exclude(path_regex=r"^/(admin|api)").exclude(path_regex=r"^/(signup|login|logout)$")


@public.parametrize()
def test_public_routes_match_their_contract(case):
    case.call_and_validate()
