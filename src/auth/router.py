from typing import Annotated
from fastapi import APIRouter, Depends, Response, status, HTTPException, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.service import AuthService, get_current_user
from src.auth.schemas import FingerPrint, AccessToken

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

def get_finger_print(request: Request) -> FingerPrint:
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
    fingerprint = get_finger_print(request)
    tokens = await service.authenticate(user_data.username, user_data.password, fingerprint)
    response.set_cookie(
        service.COOKIE_ACCESS_TOKEN,
        tokens.access_token,
        httponly=True,
        samesite="Strict"
    )
    response.set_cookie(
        service.COOKIE_SESSION_ID,
        tokens.session_id,
        httponly=True,
        samesite="Strict"
    )
    if tokens.exception is None:
        return HTTPException(status_code=status.HTTP_200_OK, detail="Logged in successfully")
    else:
        return tokens.exception

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
    fingerprint = get_finger_print(request)
    tokens = await service.refresh_tokens(access_token, session_id, fingerprint)
    response.set_cookie(
        service.COOKIE_ACCESS_TOKEN,
        tokens.access_token,
        httponly=True,
        samesite="Strict"
    )
    response.set_cookie(
        service.COOKIE_SESSION_ID,
        tokens.session_id,
        httponly=True,
        samesite="Strict"
    )
    if tokens.exception is None:
        return HTTPException(status_code=status.HTTP_200_OK)
    else:
        return tokens.exception