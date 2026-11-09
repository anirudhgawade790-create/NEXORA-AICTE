from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    region: str | None = None
    institution_id: int | None = None
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    institution_id: int | None = None
    region: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_bcrypt_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
