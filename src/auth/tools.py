import jwt
import bcrypt
from datetime import timedelta, datetime
from src.settings import settings

def encode_jwt(
    payload: dict,
    private_key: str = settings.auth_jwt.private_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
    expire_minutes: int = settings.auth_jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    
    to_encode: dict = payload.copy()
    now: datetime = datetime.utcnow()

    expire: datetime = (now + expire_timedelta) if expire_timedelta else (now + timedelta(minutes=expire_minutes))

    to_encode.update(exp=expire, iat=now)

    encoded: str = jwt.encode(
        payload=to_encode,
        key=private_key,
        algorithm=algorithm
    )
    
    return encoded

def decode_jwt(
        token: str,
        public_key: str = settings.auth_jwt.public_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm
) -> dict:
    decoded = jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=[algorithm]
    )
    return decoded

def hash_password(password: str) -> str:
    salt: bytes = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt).decode()

def validate_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

