import asyncio
import sys

from src.auth import service as accounts
from src.auth.schemas import Credentials
from src.constants import Role
from src.database import create_schema, session_factory


async def promote(email: str, password: str) -> str:
    await create_schema()
    async with session_factory() as session:
        existing = await accounts.find_by_email(session, email)
        if existing is None:
            await accounts.create_user(
                session, Credentials(email=email, password=password), Role.ADMIN
            )
            return f"created {email} as an administrator"
        existing.role = Role.ADMIN
        await session.commit()
        return f"{email} is now an administrator"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python -m scripts.make_admin <email> <password>", file=sys.stderr)
        return 2
    print(asyncio.run(promote(sys.argv[1], sys.argv[2])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
