from fastapi import APIRouter, Depends, status, Form
from fastapi.responses import RedirectResponse
from src.auth.schemas import AccessToken
from src.auth.service import get_current_user, get_current_verified_user, get_current_confirmed_user

from src.users.schemas import CreateUser, User
from src.users.service import UserCRUD

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def create_user(
    new_user: CreateUser = Depends(),
    service: UserCRUD = Depends(),
):
    """
    Handler for user sign-up.

    Parameters:
    - new_user (CreateUser): The new user data.
    
    Returns:
    - HTTPException: Successful user creation with status code 201.
    """
    return await service.create(new_user)


@router.patch("/confirm-email", status_code=status.HTTP_202_ACCEPTED)
async def confirm_email(
    code: int = Form(...),
    user: AccessToken = Depends(get_current_user),
    service: UserCRUD = Depends(),
):
    """
    Handler for email confirmation.

    Parameters:
    - code (int): The confirmation code.
    
    Returns:
    - RedirectResponse if confirmation is successful and status code 307, 
    otherwise the confirmation result.
    """
    return await service.confirm_email(user.user_id, code)



@router.patch("/enable-2fa", status_code=200)
async def switch_2fa(
    value: bool,
    user: AccessToken = Depends(get_current_confirmed_user),
    service: UserCRUD = Depends()
):
    return await service.enable_2fa(user.user_id, value)


@router.get("/me", response_model=User)
async def get_me(
    user: AccessToken = Depends(get_current_verified_user),
    service: UserCRUD = Depends(),
):
    """
    Handler for retrieving the current user's information.

    Returns:
    - The user object.
    """
    return await service.read(user.user_id)
