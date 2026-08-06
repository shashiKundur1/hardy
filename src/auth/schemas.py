from pydantic import BaseModel, field_validator

from src.auth.constants import MAX_EMAIL_LENGTH, MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH


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
