from typing import Annotated

from fastapi import Depends, Request

from src.auth.constants import SESSION_USER_KEY
from src.auth.exceptions import AdminOnly, AdminSignInRequired, NotAuthenticated
from src.auth.models import User
from src.constants import Role
from src.database import SessionDep


async def signed_in_user(request: Request, session: SessionDep) -> User | None:
    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        return None
    return await session.get(User, user_id)


OptionalUser = Annotated[User | None, Depends(signed_in_user)]


async def required_user(user: OptionalUser) -> User:
    if user is None:
        raise NotAuthenticated()
    return user


CurrentUser = Annotated[User, Depends(required_user)]


async def required_admin(user: OptionalUser) -> User:
    if user is None:
        raise AdminSignInRequired()
    if user.role != Role.ADMIN:
        raise AdminOnly()
    return user


AdminUser = Annotated[User, Depends(required_admin)]
