from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.auth.schemas import AccessToken
from src.auth.service import get_current_user

router = APIRouter(
    prefix="/pages",
    tags=["Pages"]
)

templates = Jinja2Templates(directory="src/pages/templates")


@router.get("/", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """
    Handler for rendering the login page.

    Returns:
    - HTMLResponse: The login page template if the user is not authenticated,
    otherwise redirects to the home page.
    """
    try:
        await get_current_user()
        return RedirectResponse("/pages/home", status_code=303)
    except HTTPException:
        return templates.TemplateResponse("index.html", {"request": request})


@router.get("/home", response_class=HTMLResponse)
def get_home_page(
    request: Request,
    user: AccessToken = Depends(get_current_user)
):
    """
    Handler for rendering the home page.

    Returns:
    - HTMLResponse: The home page template if the user's email is verified,
    otherwise redirects to the email confirmation page.
    """
    if not user.email_confirmed:
        return RedirectResponse("/pages/email-confirmation", status_code=303)
    return templates.TemplateResponse("base.html", {"request": request})


@router.get("/email-confirmation", response_class=HTMLResponse)
def get_email_confirmation_page(
    request: Request,
    user: AccessToken = Depends(get_current_user)
):
    """
    Handler for rendering the email confirmation page.
    
    Returns:
    - HTMLResponse: The email confirmation page template if the user's email is not verified,
    otherwise redirects to the home page.
    """
    if user.email_confirmed:
        return RedirectResponse("/pages/home", status_code=303)
    return templates.TemplateResponse("email-confirmation.html", {"request": request})