from dataclasses import dataclass
from datetime import date, datetime
from fastapi import Form
from pydantic import BaseModel, EmailStr
from typing import Optional

class CodeToUser(BaseModel):
    username: str
    email: EmailStr
    code: int


@dataclass
class CreateUser:
    username: str = Form(
        ...,
        title="Username",
        description="Your unique username",
        example="username",
        min_length=3,
        max_length=20,
    )
    email: EmailStr = Form(
        ...,
        title="Email",
        description="Your email address.",
        example="example@email.ru"
    )
    birth_date: date = Form(
        ...,
        title="Birth date",
        description="Your birth date.",
        examples=["YYYY-MM-DD"],
    )
    password: str = Form(
        ...,
        title="Password",
        description="Choose security password",
        example="password",
        min_length=6,
        max_length=20,
    )


@dataclass
class UpdateUser:
    username: Optional[str] = Form(
        default=None,
        title="Username",
        description="New username or keep field empty if it is not changing",
        min_length=3,
        max_length=20,
    )
    birth_date: Optional[date] = Form(
        default=None,
        title="Birth date",
        description="New birth date or keep field empty if it is not changing",
        examples=["YYYY-MM-DD"],
    )

@dataclass
class UpdatePassword:
    old_password: str = Form(
        ...,
        title="Old password",
        description="Your old password",
        example="old password",
        min_length=6,
        max_length=20,
    )
    new_password: str = Form(
        ...,
        title="New password",
        description="Choose new security password",
        example="new password",
        min_length=6,
        max_length=20,
    )

class User(BaseModel):
    id: int
    username: str
    email: EmailStr

    birth_date: date
    registration_date: date
    last_login: Optional[datetime] = None

    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None

    email_confirmed: bool
    two_factor_auth: bool
    mailing_allowed: bool
    telegram_mailing_allowed: bool

    class Config:
        strict=True
        from_attributes = True