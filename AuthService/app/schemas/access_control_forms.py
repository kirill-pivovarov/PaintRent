from pydantic import BaseModel, EmailStr, SecretStr, field_validator

from app.db import UserRole

class LogInForm(BaseModel):
    email: EmailStr
    password: SecretStr


class SignUpForm(BaseModel):
    email: EmailStr
    password: SecretStr
    role: str

    @field_validator("role", mode="before")
    def role_checker(cls, v: str):
        if v.upper() in [item.value for item in UserRole]:
            return v.upper()
        raise ValueError("There is no such role.")


AdminSignUpForm = LogInForm