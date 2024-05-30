from fastapi import APIRouter, Depends, status, Body
from src.auth.schemas import AccessToken
from src.auth.service import get_current_user

from src.users.schemas import CreateUser, User
from src.users.service import UserCRUD

router = APIRouter(
    prefix="/user",
    tags=["USER"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    new_user: CreateUser = Depends(),
    service: UserCRUD = Depends(),
):
    print(1)
    return await service.create(new_user)


@router.get("/me", response_model=User)
async def get_me(
    user: AccessToken = Depends(get_current_user),
    service: UserCRUD = Depends(),
):
    return await service.read(user.user_id)
