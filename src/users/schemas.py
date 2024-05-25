from annotated_types import MinLen, MaxLen
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Annotated, Optional
from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm


class CreateUser(BaseModel, OAuth2PasswordRequestForm):
    username: Annotated[str, MinLen(3), MaxLen(20)] = Form(
        title="Username",
        description="Your unique username",
        example="example@email.ru",
        min_length=3,
        max_length=20,
    )
    email: EmailStr = Form(
        title="Email",
        description="New username or keep field empty if it is not changing",
        example="example@email.ru"
    )
    birth_date: date = Field(
        title="Birth date",
        description="Your birth date.",
        examples=["YYYY-MM-DD"],
        default=date(year=1990, month=1, day=1),
    )
    password: Annotated[str, MinLen(6), MaxLen(20)] = Form(
        title="Password",
        description="Choose security password",
        example="password",
        min_length=6,
        max_length=20,
    )

class UpdateUser(BaseModel):
    username: Optional[str] = Form(
        title="Username",
        description="New username or keep field empty if it is not changing",
        default=None,
        min_length=3,
        max_length=20
    )
    birth_date: Optional[date] = Field(
        title="Birth date",
        description="New birth date or keep field empty if it is not changing",
        examples=["YYYY-MM-DD"],
        default=None
    )

class UpdatePassword(BaseModel, OAuth2PasswordRequestForm):
    old_password: Annotated[str, MinLen(6), MaxLen(20)] = Form(
        title="Old password",
        description="Your old password",
        example="password",
        min_length=6,
        max_length=20,
    )
    new_password: Annotated[str, MinLen(6), MaxLen(20)] = Form(
        title="New password",
        description="Choose new security password",
        example="drowssap",
        min_length=6,
        max_length=20,
    )

class User(BaseModel):
    id: int
    username: str
    email: EmailStr

    birth_date: date
    registration_date: date
    last_loggin: Optional[datetime] = None

    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None

    email_verified: bool
    mailing_allowed: bool
    telegram_mailing_allowed: bool

    class Config:
        strict=True
        from_attributes = True