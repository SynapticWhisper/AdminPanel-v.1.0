from fastapi import APIRouter, Depends, Cookie, Response, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import Token
from src.auth.service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["AUTH"]
)

# @router.post("/jwt/token")
# async def login(
#     user_data: OAuth2PasswordRequestForm = Depends(),
#     service: AuthService = Depends(),
# ):
#     return Token(access_token=await service.authenticate(user_data.username, user_data.password))


@router.post("/jwt/cookie", status_code=status.HTTP_200_OK)
async def cookie_login(
    response: Response, 
    user_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends()
):
    token = await service.authenticate(user_data.username, user_data.password)
    response.set_cookie(AuthService.COOKIE_SESSION_TOKEN_KEY, token, httponly=True)
    return HTTPException(status_code=status.HTTP_200_OK, detail="Logged in successfully")
