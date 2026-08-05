from fastapi import HTTPException, status
from pydantic import ValidationError


class InvalidForm(HTTPException):
    def __init__(self, error: ValidationError) -> None:
        message = error.errors()[0]["msg"].removeprefix("Value error, ")
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


class EmailTaken(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "That email already has an account")


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "That email and password do not match")


class NotAuthenticated(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Sign in to continue")


class AdminOnly(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "That page is for administrators")
