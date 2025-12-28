from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Discord ID
    username: Mapped[str] = mapped_column(String)
    discriminator: Mapped[str] = mapped_column(String)
    avatar: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    access_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class UserSession(Base, TimestampMixin):
    __tablename__ = "user_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    session_data: Mapped[dict] = mapped_column(JSON, default=dict)
