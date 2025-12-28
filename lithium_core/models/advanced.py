from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional
from datetime import datetime

class CommandPermission(Base, TimestampMixin):
    __tablename__ = "command_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    command_name: Mapped[str] = mapped_column(String, index=True)
    role_id: Mapped[str] = mapped_column(String)

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    guild_id: Mapped[str] = mapped_column(String)
    channel_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    remind_at: Mapped[datetime] = mapped_column(DateTime)

class StickyMessage(Base, TimestampMixin):
    __tablename__ = "sticky_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String, unique=True)
    content: Mapped[str] = mapped_column(Text)
    last_message_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class AutoResponder(Base, TimestampMixin):
    __tablename__ = "auto_responders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    trigger: Mapped[str] = mapped_column(String)
    response: Mapped[str] = mapped_column(Text)
    cooldown: Mapped[int] = mapped_column(Integer, default=5)

class StarboardConfig(Base, TimestampMixin):
    __tablename__ = "starboard_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    channel_id: Mapped[str] = mapped_column(String)
    threshold: Mapped[int] = mapped_column(Integer, default=3)
    emoji: Mapped[str] = mapped_column(String, default="⭐")

class AFKState(Base, TimestampMixin):
    __tablename__ = "afk_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class VoiceConfig(Base, TimestampMixin):
    __tablename__ = "voice_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    category_id: Mapped[str] = mapped_column(String)
    channel_name_tpl: Mapped[str] = mapped_column(String, default="{user}'s room")

class VerificationConfig(Base, TimestampMixin):
    __tablename__ = "verification_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    channel_id: Mapped[str] = mapped_column(String)
    message_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role_id: Mapped[str] = mapped_column(String)

class LogRoute(Base, TimestampMixin):
    __tablename__ = "log_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    module: Mapped[str] = mapped_column(String) # MODERATION, AUTOMOD, TICKETS, UTILITY
    channel_id: Mapped[str] = mapped_column(String)

class CaseNote(Base, TimestampMixin):
    __tablename__ = "case_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("moderation_cases.id"), index=True)
    moderator_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
