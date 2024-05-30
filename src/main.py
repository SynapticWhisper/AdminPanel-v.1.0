from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from src.auth.router import router as AuthRouter
from src.users.router import router as UserRouter
from src.pages.router import router as PagesRouter

app = FastAPI(
    title="ToDo-API",
    version="0.2.1"
)


class RedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 303:
            return RedirectResponse(url="/auth/v1/refresh-token")
        # if response.status_code == 401:
        #     return RedirectResponse(url="/auth/v1/login")
        return response


app.mount("/static", StaticFiles(directory="src/pages/static"), name="static")

app.include_router(AuthRouter)
app.include_router(UserRouter)
app.include_router(PagesRouter)
app.add_middleware(RedirectMiddleware)