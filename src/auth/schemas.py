from datetime import date
from pydantic import BaseModel, EmailStr
from enum import Enum

class Roles(str, Enum):
    ADMIN: str = "admin"
    USER: str = "user"


class FingerPrint(BaseModel):
    # Here you can add as much fields in user "Fingerprint" as you want.
    # More fields - more paranoid user verification.
    # But remember, that any dynamic IP-address or any other dynamic field
    # forces the user to relogin whent change them

    # host: str
    user_agent: str
    accept_language: str
    accept_encoding: str


class UserSecret(BaseModel):
    user_id: int
    email_verified: bool
    registration_date: date
    user_role: Roles

    user_fingerprint: FingerPrint

class AccessToken(BaseModel):
    user_id: int
    email_verified: bool
    user_role: Roles


class RefreshToken(BaseModel):
    session_id: str
    user_secret: str


class PwdResetToken(BaseModel):
    user_id: int
    email: EmailStr
