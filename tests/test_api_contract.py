import asyncio
import os
import tempfile

_WORKSPACE = tempfile.mkdtemp(prefix="hardy-contract-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_WORKSPACE}/hardy.db"
os.environ["QDRANT_PATH"] = f"{_WORKSPACE}/qdrant"
os.environ["QDRANT_URL"] = ""
os.environ.setdefault("SESSION_SECRET", "contract-test-secret")

import schemathesis

from src.database import create_schema
from src.integrations import vectorstore
from src.main import app

asyncio.run(create_schema())
asyncio.run(vectorstore.ensure_collection())

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

public = schema.exclude(path_regex=r"^/(admin|api)").exclude(path_regex=r"^/(signup|login|logout)$")


@public.parametrize()
def test_public_routes_match_their_contract(case):
    case.call_and_validate()
