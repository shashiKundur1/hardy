import json

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import EmailTaken, InvalidCredentials
from src.auth.models import User
from src.auth.schemas import Credentials, OnboardingChoices
from src.constants import CATEGORIES, Role
from src.database import utcnow


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def password_matches(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


async def find_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def create_user(
    session: AsyncSession, credentials: Credentials, role: Role = Role.USER
) -> User:
    if await find_by_email(session, credentials.email) is not None:
        raise EmailTaken()
    user = User(
        email=credentials.email,
        password_hash=hash_password(credentials.password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, credentials: Credentials) -> User:
    user = await find_by_email(session, credentials.email)
    if user is None or not password_matches(credentials.password, user.password_hash):
        raise InvalidCredentials()
    return user


def declared_interests(user: User) -> list[str]:
    try:
        chosen = json.loads(user.interests or "[]")
    except json.JSONDecodeError:
        return []
    return [slug for slug in chosen if slug in CATEGORIES]


async def save_interests(session: AsyncSession, user: User, interests: list[str]) -> None:
    user.interests = json.dumps(interests)
    await session.commit()


async def complete_onboarding(
    session: AsyncSession, user: User, choices: OnboardingChoices
) -> None:
    user.shopping_for = choices.shopping_for
    user.display_name = choices.display_name or None
    user.onboarded_at = utcnow()
    await session.commit()


async def skip_onboarding(session: AsyncSession, user: User) -> None:
    user.onboarded_at = utcnow()
    await session.commit()
