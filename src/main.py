from fastapi import FastAPI
from src.auth.router import router as AuthRouter
from src.users.router import router as UserRouter
app = FastAPI(
    title="ToDo-API",
    version="0.2.1"
)

app.include_router(AuthRouter)
app.include_router(UserRouter)