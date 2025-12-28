from sqlalchemy import String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class ModerationCase(Base, TimestampMixin):
    __tablename__ = "moderation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    case_id: Mapped[int] = mapped_column(Integer) # Local ID per guild
    
    action_type: Mapped[str] = mapped_column(String) # KARA, MUTE, KICK, BAN, WARN
    user_id: Mapped[str] = mapped_column(String, index=True)
    moderator_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    
    active: Mapped[bool] = mapped_column(Boolean, default=True) # For mutes/bans
    duration: Mapped[int] = mapped_column(Integer, nullable=True) # Seconds

class Warning(Base, TimestampMixin):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    moderator_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
