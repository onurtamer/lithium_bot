from sqlalchemy import String, Integer, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discord_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)

class Guild(Base, TimestampMixin):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discord_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    owner_id: Mapped[str] = mapped_column(String)
    
    # Module configs will link here

class OAuthSession(Base, TimestampMixin):
    __tablename__ = "oauth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    access_token: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String) # Storing as ISO string or timestamp
    
    user: Mapped["User"] = relationship()


class AccessKey(Base, TimestampMixin):
    """Key-based authentication for quick dashboard access without Discord OAuth"""
    __tablename__ = "access_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    guild_discord_id: Mapped[str] = mapped_column(String, index=True)
    created_by_discord_id: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String, nullable=True)  # ISO datetime string
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
