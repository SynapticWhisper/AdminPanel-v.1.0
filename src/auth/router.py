from typing import Annotated
from fastapi import APIRouter, Depends, Response, status, HTTPException, Request, Cookie, Form
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.service import AuthService, get_current_user, get_current_confirmed_user
from src.auth.schemas import AccessToken
from src.users.service import CodeService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/v1/login", status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    response: Response,
    user_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends()
):
    """
    Handler for user login.

    Parameters:
    - user_data (OAuth2PasswordRequestForm): The user data for login.
    
    Returns:
    - HTTPException: Successful login with status code 200.
    """
    tokens = await service.authenticate(user_data.username, user_data.password, request)
    return service.set_cookie(response, tokens)
    

@router.post("/v1/logout", status_code=status.HTTP_401_UNAUTHORIZED)
async def logout(
    response: Response,
    user: AccessToken = Depends(get_current_user),
    session_id: Annotated[str | None, Cookie(alias=AuthService.COOKIE_SESSION_ID)] = None,
    service: AuthService = Depends()
):
    """
    Handler for user logout.

    Returns:
    - HTTPException: Successful logout with status code 401.
    """
    response.delete_cookie(service.COOKIE_ACCESS_TOKEN)
    response.delete_cookie(service.COOKIE_SESSION_ID)
    await service.del_user_session(user.user_id, session_id)
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Logged out.")


@router.post("/v1/refresh-token")
async def refresh_token(
    request: Request,
    response: Response,
    access_token: Annotated[str | None, Cookie(alias=AuthService.COOKIE_ACCESS_TOKEN)] = None,
    session_id: Annotated[str | None, Cookie(alias=AuthService.COOKIE_SESSION_ID)] = None,
    service: AuthService = Depends()
):
    """
    Handler for refreshing the access and refresh tokens.

    Returns:
    - HTTPException: Successful tokens refresh with status code 200.
    """
    tokens = await service.refresh_tokens(access_token, session_id, request)
    return service.set_cookie(response, tokens)
    

@router.post("/v1/verify-2fa-code", status_code=status.HTTP_200_OK)
async def send_2fa_code(
    request: Request,
    response: Response,
    code_2fa: int = Form(
        ...,
        title="2FA code",
        description="2FA code from your email",
        example="123456"
    ),
    at_user: AccessToken = Depends(get_current_confirmed_user),
    access_token: Annotated[str | None, Cookie(alias=AuthService.COOKIE_ACCESS_TOKEN)] = None,
    session_id: Annotated[str | None, Cookie(alias=AuthService.COOKIE_SESSION_ID)] = None,
    service: AuthService = Depends(),
    code_service: CodeService = Depends()
):
    is_verified = await code_service.validate_2fa_code(at_user.user_id, code_2fa)
    tokens = await service.refresh_tokens(access_token, session_id, request, is_verified=is_verified)
    return service.set_cookie(response, tokens)
