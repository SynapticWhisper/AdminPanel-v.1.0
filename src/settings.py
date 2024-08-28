from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent

class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    
    refresh_token_expire_days: int = 30

class Settings(BaseSettings):
    db_url: str
    redis_url: str

    auth_jwt: AuthJWT = AuthJWT()

    smtp_user: str
    smtp_password: str

settings = Settings(
    _env_file=".env",
    _env_file_encoding="utf-8"
)