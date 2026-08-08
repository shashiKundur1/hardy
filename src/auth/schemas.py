from pydantic import BaseModel, field_validator

from src.auth.constants import (
    MAX_DISPLAY_NAME,
    MAX_EMAIL_LENGTH,
    MAX_PASSWORD_BYTES,
    MAX_SHOPPING_FOR,
    MIN_PASSWORD_LENGTH,
)
from src.constants import CATEGORIES


class Credentials(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def deliverable_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, separator, domain = email.partition("@")
        if not separator or not local or not domain:
            raise ValueError("Enter an email address in the form you@example.com")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Enter an email address in the form you@example.com")
        if any(character.isspace() for character in email):
            raise ValueError("An email address cannot contain spaces")
        if len(email) > MAX_EMAIL_LENGTH:
            raise ValueError("That email address is too long")
        return email

    @field_validator("password")
    @classmethod
    def usable_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Use at least {MIN_PASSWORD_LENGTH} characters")
        if len(value.encode()) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Keep the password under {MAX_PASSWORD_BYTES} bytes")
        return value


class OnboardingChoices(BaseModel):
    interests: list[str] = []
    shopping_for: str = ""
    display_name: str = ""

    @field_validator("interests")
    @classmethod
    def known_categories(cls, value: list[str]) -> list[str]:
        if any(slug not in CATEGORIES for slug in value):
            raise ValueError("Choose categories from the list shown")
        return list(dict.fromkeys(value))

    @field_validator("shopping_for")
    @classmethod
    def brief_enough(cls, value: str) -> str:
        text = " ".join(value.split())
        if len(text) > MAX_SHOPPING_FOR:
            raise ValueError(f"Keep this under {MAX_SHOPPING_FOR} characters")
        return text

    @field_validator("display_name")
    @classmethod
    def short_enough(cls, value: str) -> str:
        name = " ".join(value.split())
        if len(name) > MAX_DISPLAY_NAME:
            raise ValueError(f"Keep the name under {MAX_DISPLAY_NAME} characters")
        return name
