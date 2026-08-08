from fastapi import HTTPException, status
from pydantic import ValidationError


class InvalidForm(HTTPException):
    def __init__(self, error: ValidationError) -> None:
        first = error.errors()[0]
        self.field = str(first["loc"][0]) if first["loc"] else "form"
        message = first["msg"].removeprefix("Value error, ")
        super().__init__(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


class EmailTaken(HTTPException):
    field = "email"

    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "That email already has an account")


class InvalidCredentials(HTTPException):
    field = "form"

    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "That email and password do not match")


class NotAuthenticated(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Sign in to continue")


class AdminOnly(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "That page is for administrators")


class AdminSignInRequired(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Sign in as an administrator to continue")
