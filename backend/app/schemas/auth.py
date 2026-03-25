from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone_number: str = Field(..., min_length=7, max_length=20)
    business_name: str = Field(..., min_length=2, max_length=255)
    office_address: Optional[str] = Field(None, max_length=512)
    gst_number: str = Field(..., min_length=15, max_length=15, description="15-character GST number")
    password: str = Field(..., min_length=8, max_length=128)

    model_config = {"str_strip_whitespace": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_questionnaire: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
