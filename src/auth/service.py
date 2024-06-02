import jwt
import uuid
import hashlib

from typing import Annotated
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError, EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt_tools
from src.auth.schemas import AccessToken, UserSecret, FingerPrint, RefreshToken, Tokens
from src.auth.sessions import SessionService
from src.database import get_async_session
from src.users import models
from src.settings import settings

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/jwt/token")

class AuthService:
    COOKIE_ACCESS_TOKEN: str = "web-app-session-token"
    COOKIE_SESSION_ID: str = "web-app-session-id"
    
    EXCEPTIONS: dict = {
        "UNAUTHORIZED": HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message":"Could not validate credentials.",
            },
            headers={
                "www-Authenticate": 'Bearer'
            }
        ),
        "INCORRECT_DATA": HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Incorrect username or password.",
            },
            headers={
                "www-Authenticate": 'Bearer'
            }
        ),
        "2FA_REQUIRED": HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "error_code": "2FA_REQUIRED",
                "message": "Please enter 2FA code from your email address."
            }
        ),
        "EMAIL_CONFIRMATION_REQUIRED": HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "error_code": "EMAIL_CONFIRMATION_REQUIRED",
                "message": "Please confirm your email address."
            }
        ),
    }

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.__session = session
    
    @classmethod
    def create_user_hash(cls, user: models.User, user_fingerprint: FingerPrint) -> str:
        return hashlib.sha256(
            UserSecret(
                user_id=user.id,
                registration_date=user.registration_date,
                user_role=user.user_role,
                user_fingerprint=user_fingerprint
            ).model_dump_json().encode()
        ).hexdigest()
    
    @classmethod
    async def del_user_session(cls, user_id: int, session_id: str) -> None:
        await SessionService().del_user_session(user_id, session_id)
    
    @classmethod
    async def create_access_token(cls, user: models.User, is_verified: bool) -> str:
        payload = {
            "sub": user.id,
            "user": {
                "user_id": user.id,
                "is_verified": is_verified,
                "email_confirmed": user.email_confirmed,
                "user_role": user.user_role
            }
        }
        encoded_jwt = jwt_tools.encode_jwt(payload)
        return encoded_jwt
    
    async def validate_access_token(self, token: str) -> AccessToken:
        try:
            payload = jwt_tools.decode_jwt(token)
            if payload.get("sub") is None:
                raise self.EXCEPTIONS["UNAUTHORIZED"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail={
                    "error_code": "ACCESS_TOKEN_EXPIRED",
                    "message": "Access token expired! Please refresh token"
                }
            )
        except InvalidTokenError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        try:
            user = AccessToken.model_validate(payload.get("user"))
        except ValidationError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        if not user.email_confirmed:
            raise self.EXCEPTIONS["EMAIL_CONFIRMATION_REQUIRED"]
        
        if not user.is_verified:
            raise self.EXCEPTIONS["2FA_REQUIRED"]
        
        return user
    
    async def create_refresh_token(self, user: models.User, user_fingerprint: FingerPrint) -> str:
        session_id = str(uuid.uuid4())
        user_secret = self.create_user_hash(user, user_fingerprint)
        payload = {
            "sub": user.id,
            "user": {
                "session_id": session_id,
                "user_secret": user_secret 
            }
        }
        exp_timedelta = timedelta(days=settings.auth_jwt.refresh_token_expire_days)
        encoded_jwt = jwt_tools.encode_jwt(payload, expire_timedelta=exp_timedelta)
        await SessionService().add_refresh_token(user.id, session_id, encoded_jwt)
        return session_id
    
    async def validate_refresh_token(
        self,
        user_id: int,
        session_id: str,
        user_fingerprint: FingerPrint
    ) -> Tokens:
        token = await SessionService().get_refresh_token(user_id, session_id)
        if not token:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        try:
            payload = jwt_tools.decode_jwt(token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail={
                    "error_code": "REFRESH_TOKEN_EXPIRED",
                    "message": "Refresh token expired! Please re-login."
                }
            )
        
        try:
            _user = RefreshToken.model_validate(payload.get("user"))
        except ValidationError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        user: models.User = await self.__get(username=None, user_id=user_id)
        
        if not user:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        user_secret = self.create_user_hash(user, user_fingerprint)
        if not user_secret == _user.user_secret:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        await self.del_user_session(user.id, session_id)
        
        return await self.create_tokens(user, user_fingerprint)
    
    async def create_tokens(self, user: models.User, user_fingerprint: FingerPrint) -> Tokens:
        exception = None
        is_verified = True
        if not user.email_confirmed:
            exception = self.EXCEPTIONS["EMAIL_CONFIRMATION_REQUIRED"]
        elif user.two_factor_auth:
            is_verified = False
            exception = self.EXCEPTIONS["2FA_REQUIRED"]
        result = Tokens(
            exception=exception,
            access_token=await self.create_access_token(user, is_verified),
            session_id=await self.create_refresh_token(user, user_fingerprint)
        )
        return result
    
    async def refresh_tokens(
        self,
        access_token: str | None,
        session_id: str | None,
        user_fingerprint: FingerPrint
    ) -> Tokens:
        if access_token is None and session_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "UNAUTHORIZED",
                    "message": "No cookie provided."
                }
            )
        try:
            payload = jwt_tools.decode_jwt(access_token)
            if payload.get("sub") is None:
                raise self.EXCEPTIONS["UNAUTHORIZED"]
        except jwt.ExpiredSignatureError:
            payload = jwt_tools.decode_jwt(access_token, options={"verify_exp": False})
        except InvalidTokenError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        user = AccessToken.model_validate(payload.get("user"))
        return await self.validate_refresh_token(user.user_id, session_id, user_fingerprint)
    
    async def __get(
            self,
            username: str | None,
            email: EmailStr | None = None,
            user_id: int | None = None
        ) -> models.User:
        if username is None and email is None and user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Neither email address nor username were shared"
            )
        
        statements = {
            "email": (select(models.User).where(models.User.email == email)),
            "username": (select(models.User).where(models.User.username == username)),
            "user_id": (select(models.User).where(models.User.id == user_id))
        }

        if email:
            stmt = statements["email"]
        elif username:
            stmt = statements["username"]
        else:
            stmt = statements["user_id"]

        user = (await self.__session.execute(stmt)).scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user
    
    async def authenticate(self, username: str, password: str, fingerprint: FingerPrint) -> Tokens:
        try:
            user = await self.__get(username=username)
        except HTTPException:
            raise self.EXCEPTIONS["INCORRECT_DATA"]
        
        if not (jwt_tools.validate_password(password, user.hashed_password)):
            raise self.EXCEPTIONS["INCORRECT_DATA"]
        
        return await self.create_tokens(user, fingerprint)


async def get_current_user(
        token: Annotated[str | None, Cookie(alias=AuthService.COOKIE_ACCESS_TOKEN)] = None,
        service: AuthService = Depends()
) -> AccessToken:
    if token is None:
        raise AuthService.EXCEPTIONS["UNAUTHORIZED"]
    return await service.validate_access_token(token)