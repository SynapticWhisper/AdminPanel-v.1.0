import jwt
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

from typing import Annotated
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status, Cookie, Request, Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt_tools
from src.auth.schemas import AccessToken, UserSecret, FingerPrint, RefreshToken, Tokens
from src.auth.sessions import SessionService
from src.database import get_async_session
from src.users import models
from src.settings import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/v1/login")

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
    def get_finger_print(cls, request: Request) -> FingerPrint:
        """
        Function to get the browser fingerprint of the user.
        
        Parameters:
        request (Request): The HTTP request.

        Returns:
        FingerPrint: Object containing information about User-Agent, Accept-Language, and Accept-Encoding.
        """
        return FingerPrint(
            user_agent=request.headers.get("user-agent"),
            accept_language=request.headers.get("accept-language"),
            accept_encoding=request.headers.get("accept-encoding")
        )

    @classmethod
    def set_cookie(cls, response: Response, tokens: Tokens) -> HTTPException:
        now = datetime.now(timezone.utc)
        expire=now + timedelta(settings.auth_jwt.refresh_token_expire_days)
        response.set_cookie(
            AuthService.COOKIE_ACCESS_TOKEN,
            tokens.access_token,
            httponly=True,
            samesite="Strict",
            expires=expire
        )
        response.set_cookie(
            AuthService.COOKIE_SESSION_ID,
            tokens.session_id,
            httponly=True,
            samesite="Strict",
            expires=expire
        )
        return HTTPException(status_code=status.HTTP_200_OK)

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
        
        return user
    
    async def create_refresh_token(
            self,
            user: models.User,
            user_fingerprint: FingerPrint,
            is_verified: bool
        ) -> str:
        session_id = str(uuid.uuid4())
        user_secret = self.create_user_hash(user, user_fingerprint)
        payload = {
            "sub": user.id,
            "user": {
                "session_id": session_id,
                "is_verified": is_verified,
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
        user_fingerprint: FingerPrint,
    ) -> tuple[RefreshToken, models.User]:
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
        
        except InvalidTokenError:
            # Такой вариант возможен только если Public и Secret RSA-keys изменились, а токен пользователя
            # в Redis был подписан старыми ключами. Если вдруг, такое произошло, логично попросить
            # пользователя залогиниться еще раз.
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        try:
            rt_user = RefreshToken.model_validate(payload.get("user"))
        except ValidationError:
            # Такой вариант возможен только если модель RefreshToken изменилась, а у пользователя в Redis
            # лежит старая модель. Если вдруг, такое произошло, логично попросить пользователя 
            # залогиниться еще раз. 
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        user: models.User = await self.__get(username=None, user_id=user_id)
        
        if not user:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        user_secret = self.create_user_hash(user, user_fingerprint)
        
        if not user_secret == rt_user.user_secret:
            # Если к моменту обновления подписи у пользователя изменились критически важные поля
            # или FingerPrint пользователя не соответствует FingerPrint'у на основании которого был создан
            # хеш, просим пользователя перезайти.
            raise self.EXCEPTIONS["UNAUTHORIZED"]
                
        return rt_user, user
    
    async def create_tokens(
        self, 
        user: models.User,
        user_fingerprint: FingerPrint,
        is_verified: bool | None = None
    ) -> Tokens:

        if is_verified is None:
            is_verified: bool = False if user.two_factor_auth else True

        result = Tokens(
            access_token=await self.create_access_token(user, is_verified),
            session_id=await self.create_refresh_token(user, user_fingerprint, is_verified)
        )
        return result
    
    async def refresh_tokens(
        self,
        access_token: str | None,
        session_id: str | None,
        request: Request,
        is_verified: bool | None = None
    ) -> Tokens:
        fingerprint: FingerPrint = self.get_finger_print(request)

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
        except jwt.ExpiredSignatureError:
            payload = jwt_tools.decode_jwt(access_token, options={"verify_exp": False})
        except InvalidTokenError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        if payload.get("sub") is None:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        try:
            at_user = AccessToken.model_validate(payload.get("user"))
        except ValidationError:
            raise self.EXCEPTIONS["UNAUTHORIZED"]
        
        rt_user, user = await self.validate_refresh_token(at_user.user_id, session_id, fingerprint)
        await self.del_user_session(at_user.user_id, session_id)

        if is_verified is None:
            if not rt_user.is_verified:
                # Может произойти если пользователь авторизовался, но не прошел 2FA проверку, к моменту,
                # когда необходимо перевыпускать токены. Проверка не очень критична, и можно было бы
                # обойтись без нее, но! Прошло уже 15 минут (Время жизни AccessToken), а ты до сих пор не
                # ввел код, который тебе отправили на почту? ПОДОЗРИТЕЛЬНО!!!
                #
                # P.S. ИМХО, вполне логичный выброс ошибки, правда возможно лучше выбрасывать ошибку
                # типа TimeOut
                #
                # P.S.S Отработает только в том случае, если мы явно не передаем is_verified, то есть
                # если мы не обновляем токен, как раз таки потому что пользователь ввел код и подтвердил
                # вход.
                raise self.EXCEPTIONS["2FA_REQUIRED"]
            is_verified = rt_user.is_verified

        return await self.create_tokens(user, fingerprint, is_verified=is_verified)
    
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
    
    async def authenticate(
        self,
        username: str,
        password: str,
        request: Request,
    ) -> Tokens:
        fingerprint: FingerPrint = self.get_finger_print(request)
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

async def get_current_confirmed_user(
    user: AccessToken = Depends(get_current_user)
) -> AccessToken:
    if not user.email_confirmed:
        raise AuthService.EXCEPTIONS["EMAIL_CONFIRMATION_REQUIRED"]
    return user
        
async def get_current_verified_user(
    user: AccessToken = Depends(get_current_confirmed_user)
) -> AccessToken:
    if not user.is_verified:
        raise AuthService.EXCEPTIONS["2FA_REQUIRED"]
    return user
