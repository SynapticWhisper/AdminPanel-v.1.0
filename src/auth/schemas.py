from pydantic import BaseModel


class UserSecret(BaseModel):
    id: int
    random: str
    email_verified: bool

class ValidateToken(UserSecret):
    ...

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"