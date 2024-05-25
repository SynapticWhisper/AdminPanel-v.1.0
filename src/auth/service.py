import secrets
import jwt
from jwt.exceptions import InvalidTokenError

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import tools
from src.auth.schemas import Token, ValidateToken, UserSecret
from src.database import get_async_session
from src.users import models
from src.settings import settings

from tools.SecretHash import Secret

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/jwt/token")

class AuthService:
    COOKIE_SESSION_TOKEN_KEY = "web-app-session-token"
    
    EXCEPTIONS: dict = {
        "UNAUTHORIZED": HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={
                "www-Authenticate": 'Bearer'
            }
        ),
        "INCORRECT_DATA": HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={
                "www-Authenticate": 'Bearer'
            }
        ),
        "INVALID_PASSWORD_TOKEN": HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        ),
    }

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.__session = session

    @classmethod
    async def create_token(cls, user: models.User) -> Token:
        random_hex=secrets.token_hex(16)
        data = UserSecret(
            id=user.id,
            random=random_hex,
            email_verified=user.email_verified
        )
        
        payload = {
            "sub": await Secret.create(data),
            "user": {
                "id": user.id,
                "random": random_hex,
                "email_verified": user.email_verified
            }
        }

        encoded_jwt = tools.encode_jwt(payload)
        return encoded_jwt
    
    @classmethod
    async def validate_token(cls, token: str) -> ValidateToken:
        try:
            payload = tools.decode_jwt(token)
            if payload.get("sub") is None:
                raise cls.EXCEPTIONS["UNAUTHORIZED"]
        except jwt.ExpiredSignatureError:
            # TODO Update token on expire
            ...
        except InvalidTokenError:
            raise cls.EXCEPTIONS["UNAUTHORIZED"]

        try:
            user = ValidateToken.model_validate(payload.get("user"))
        except ValidationError:
            raise cls.EXCEPTIONS["UNAUTHORIZED"]

        if not await Secret.verify(payload.get("sub"), user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication error! Provided user data missmatch." \
                    "For security reasons, please consider logging in again.",
                headers={
                    "www-Authenticate": 'Bearer'
                }
            )

        return user
    
    async def __get(self, username: str | None, email: EmailStr | None = None) -> models.User:
        if username is None and email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Neither email address nor username were shared"
            )
        
        statements = {
            "email": (select(models.User).where(models.User.email == email)),
            "username": (select(models.User).where(models.User.username == username))
        }

        stmt = statements["email"] if email else statements["username"]

        user = (await self.__session.execute(stmt)).scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user
    
    async def authenticate(self, username: str, password: str) -> Token:
        try:
            user = await self.__get(username=username)
        except HTTPException:
            raise self.EXCEPTIONS["INCORRECT_DATA"]
        
        if not (tools.validate_password(password, user.hashed_password)):
            raise self.EXCEPTIONS["INCORRECT_DATA"]
        
        return await self.create_token(user)
    

# async def get_current_user_bearer(token: str = Depends(oauth2_scheme)) -> ValidateToken:
#     return await AuthService.validate_token(token)


async def get_current_user(
        token: str = Cookie(alias=AuthService.COOKIE_SESSION_TOKEN_KEY)
) -> ValidateToken:
    return await AuthService.validate_token(token)