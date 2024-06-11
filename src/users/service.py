import random

from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt_tools
from src.auth.schemas import AccessToken 
from src.database import get_async_session
from src.users import models
from src.users.schemas import CreateUser, UpdateUser, UpdatePassword, User, CodeToUser
from tools.SimpleCache import CacheTool


class UserCRUD:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.__session = session

    async def create(self, user_data: CreateUser) -> HTTPException:
        user = models.User(
            username=user_data.username,
            email=user_data.email,
            birth_date=user_data.birth_date,
            hashed_password=jwt_tools.hash_password(user_data.password)
        )
        try:
            self.__session.add(user)
            await self.__session.commit()
            return HTTPException(status_code=status.HTTP_201_CREATED, detail="Successfully created!\nNow please login with your credentials!")
        except IntegrityError as e:
            if 'username' in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already in use. Please choose another username."
                )
            elif 'email' in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email address is already registered. If this is your email, you can recover access to your account."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unable to create user due to unavailable data."
                )
            
    async def read(self, user_id: int) -> models.User:
        stmt = (
            select(models.User)
            .where(models.User.id == user_id)
        )

        user = (await self.__session.execute(stmt)).scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        return user
    
    async def update_data(self, user_id: int, user_data: UpdateUser) -> HTTPException:
        user = await self.read(user_id)
        try:
            for key, value in user_data:
                if value is not None:
                    setattr(user, key, value)
            await self.__session.commit()
            return HTTPException(status_code=status.HTTP_200_OK)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to update user due to unavailable data."
            )
        
    async def update_password(self, user_id: int, user_data: UpdatePassword) -> HTTPException:
        user = await self.read(user_id)

        if not jwt_tools.validate_password(user_data.old_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")

        user.hashed_password = jwt_tools.hash_password(user_data.new_password)
        await self.__session.commit()

        return HTTPException(status_code=status.HTTP_200_OK)
    
    async def delete(self, user_id: int) -> HTTPException:
        user = await self.read(user_id)
        await self.__session.delete(user)
        await self.__session.commit()
        return HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        
    async def confirm_email(self, user_id: int, code: int) -> HTTPException:
        user: models.User = await self.read(user_id)
        try:
            await CodeService().validate_code(user, code)
            user.email_confirmed = True
            await self.__session.commit()
            return HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "error_code": "REFRESH_TOKENS",
                    "message": "Confirmation successful, refresh your tokens please"
                }
            )
        except HTTPException as exception:
            raise exception
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    async def enable_2fa(self, user_id: int, value: bool) -> HTTPException:
        user = await self.read(user_id)
        try:
            user.two_factor_auth = value
            detail = "2FA enabled" if value else "2FA disabled"
            await self.__session.commit()
            return HTTPException(status_code=status.HTTP_200_OK, detail=detail)
        except HTTPException as exception:
            raise exception
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CodeService:
    def __init__(self, user_service: UserCRUD = Depends()):
        self.cache = CacheTool("mailing_cache")
        self.service = user_service
        
    @classmethod
    async def user_to_str(cls, user: models.User) -> str:
        user_model: User = User(**user.__dict__)
        return user_model.model_dump_json()

    async def create_code(self, user: models.User) -> CodeToUser:
        key = await self.user_to_str(user)
        code: int = random.randint(10**5, 10**6-1)
        await self.cache.set_data(key, code)
        return CodeToUser(
            username=user.username,
            email=user.email,
            code=code
        )

    async def validate_code(self, user: models.User, code: int) -> bool:
        key = await self.user_to_str(user)
        code_from_db = await self.cache.get_data(key)
        if not code_from_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect data")
        elif code != code_from_db:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect code")
        await self.cache.del_data(key)
        return True
    
    async def validate_2fa_code(self, user_id: int, code: int) -> bool:
        user: models.User = await self.service.read(user_id)
        return await self.validate_code(user, code)

    async def create_confirmation_code(self, user_id: int) -> CodeToUser:
        user: models.User = await self.service.read(user_id)
        if user.email_confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already confirmed"
            )
        return await self.create_code(user)
    
    async def create_2fa_code(self, at_user: AccessToken) -> CodeToUser:
        if at_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has already been verified"
            )
        user: models.User = await self.service.read(at_user.user_id)
        if not user.two_factor_auth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA disabled, enable it if you want."
            )
        return await self.create_code(user)