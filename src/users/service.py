import random

from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt_tools
from src.database import get_async_session
from src.users import models
from src.users.schemas import CreateUser, UpdateUser, UpdatePassword, User
from tools.SimpleCache import CacheTool

cache_service = CacheTool("mailing_cache")


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

    async def create_verification_code(self, user_id: int) -> dict:
        user: models.User = await self.read(user_id)
        user_model: User = User(**user.__dict__)
        to_str: str = user_model.model_dump_json()
        code: int = random.randint(10**5, 10**6-1)
        await cache_service.set_data(to_str, code)
        result: dict = {
            "username": user.username,
            "email": user.email,
            "code": code
        }
        return result

    async def verify_email(self, user_id: int, code: int) -> HTTPException:
        user = await self.read(user_id)

        try:
            user_model = User(**user.__dict__)
            to_str = user_model.model_dump_json()

            code_from_db = await cache_service.get_data(to_str)

            if not code_from_db:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect data")
            elif code != code_from_db:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect code")

            await cache_service.del_data(to_str)

            user.email_verified = True
            await self.__session.commit()
            return
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)