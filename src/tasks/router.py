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


@router.post("/send-confirmation-code", status_code=status.HTTP_200_OK)
async def send_confirmation_code(
    user: AccessToken = Depends(get_current_user),
    service: UserCRUD = Depends()
):
    """
    Handler for sending the email confirmation code.

    Returns:
    - HTTPException: Confirmation code sent successfully with status code 200.
    """
    values = await service.create_confirmation_code(user.user_id)
    email_confirmation_message.delay(**values)
    return HTTPException(status_code=status.HTTP_200_OK)


@router.post("/send-2fa-code", status_code=status.HTTP_200_OK)
async def send_2fa_code():
    """
    Handler for sending the 2FA code.

    Returns:
    - HTTPException: 2FA-code sent successfully with status code 200.
    """
    return {"status": "OK"}