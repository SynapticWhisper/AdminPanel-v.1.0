from fastapi import APIRouter, Form, HTTPException, status, Depends
from fastapi.responses import RedirectResponse

from src.auth.schemas import AccessToken
from src.auth.service import get_current_user
from src.users.service import UserCRUD
from src.tasks.mailing import email_confirmation_message

# * celery -A tasks.mailing:celery worker --loglevel=INFO
# * worker - принял задачу - выполнил задачу
# * bit - ежедневные задачи/задачи с некой периодичностью
# * flower - менеджер с удобным интерфейсом

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


@router.get("/send-confirmation-code", status_code=status.HTTP_200_OK)
async def get_confirmation_code(
    user: AccessToken = Depends(get_current_user),
    service: UserCRUD = Depends()
):
    values = await service.create_verification_code(user.user_id)
    email_confirmation_message.delay(**values)
    return HTTPException(status_code=status.HTTP_200_OK)


@router.post("/verify-email")
async def verify_email(
    code: int = Form(...),
    user: AccessToken = Depends(get_current_user),
    user_service: UserCRUD = Depends(),
):
    await user_service.verify_email(user.user_id, code)
    return RedirectResponse("/auth/v1/refresh-token", status_code=status.HTTP_302_FOUND)