import sqlalchemy as sa
from datetime import date, datetime
from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: int = sa.Column(sa.Integer, primary_key=True)
    
    # Basic fields
    username: str = sa.Column(sa.String, unique=True, nullable=False)
    email: str = sa.Column(sa.String, unique=True, nullable=False)
    hashed_password: str = sa.Column(sa.String, nullable=False)
    user_role: str = sa.Column(sa.String, nullable=False, default="user")

    # Date fields
    birth_date: date = sa.Column(sa.Date, nullable=False)
    registration_date: date = sa.Column(sa.Date, nullable=False, default=date.today)
    last_login: datetime = sa.Column(sa.DateTime, nullable=True)

    # Telegram
    telegram_id: int = sa.Column(sa.Integer, nullable=True, unique=True)
    telegram_username: str = sa.Column(sa.String, nullable=True, unique=True)

    # Settings
    two_factor_auth: bool = sa.Column(sa.Boolean, nullable=False, default=False)
    email_confirmed: bool = sa.Column(sa.Boolean, nullable=False, default=False)
    mailing_allowed: bool = sa.Column(sa.Boolean, nullable=False, default=True)
    telegram_mailing_allowed: bool = sa.Column(sa.Boolean, nullable=False, default=True)