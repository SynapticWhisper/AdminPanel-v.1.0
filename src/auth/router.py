from fastapi import APIRouter, Depends, Response, status, HTTPException, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.service import AuthService, get_current_user
from src.auth.schemas import FingerPrint, AccessToken

router = APIRouter(
    prefix="/auth",
    tags=["AUTH"]
)

def get_finger_print(request: Request) -> FingerPrint:
    return FingerPrint(
        user_agent=request.headers.get("user-agent"),
        accept_language=request.headers.get("accept-language"),
        accept_encoding=request.headers.get("accept-encoding")
    )

@router.post("/v1/login", status_code=status.HTTP_200_OK)
async def cookie_login(
    request: Request,
    response: Response,
    user_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends()
):
    fingerprint = get_finger_print(request)
    token = await service.authenticate(user_data.username, user_data.password, fingerprint)
    response.set_cookie(service.COOKIE_SESSION_TOKEN_KEY, token["access-token"], httponly=True, samesite="Strict")
    response.set_cookie(service.COOKIE_SESSION_ID, token["session-id"], httponly=True, samesite="Strict")
    return HTTPException(status_code=status.HTTP_200_OK, detail="Logged in successfully")


@router.get("/v1/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request,
    response: Response,
    session_id: str = Cookie(alias=AuthService.COOKIE_SESSION_ID),
    user: AccessToken = Depends(get_current_user),
    service: AuthService = Depends()
):
    fingerprint = get_finger_print(request)
    token = await service.validate_refresh_token(user.user_id, session_id, fingerprint)
    response.set_cookie(service.COOKIE_SESSION_TOKEN_KEY, token["access-token"], httponly=True, samesite="Strict")
    response.set_cookie(service.COOKIE_SESSION_ID, token["session-id"], httponly=True, samesite="Strict")
    return HTTPException(status_code=status.HTTP_200_OK, detail="OK")