from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional
from datetime import datetime

class ScheduledMessage(Base, TimestampMixin):
    __tablename__ = "scheduled_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String)
    
    content: Mapped[str] = mapped_column(Text)
    cron: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class CustomCommand(Base, TimestampMixin):
    __tablename__ = "custom_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    response: Mapped[str] = mapped_column(Text)
    
    cooldown: Mapped[int] = mapped_column(Integer, default=5)
    permission_role: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class LogEvent(Base, TimestampMixin):
    __tablename__ = "log_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String)
    event_data: Mapped[dict] = mapped_column(JSON)

class ReactionRoleMenu(Base, TimestampMixin):
    __tablename__ = "reaction_role_menus"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    channel_id: Mapped[str] = mapped_column(String)
    message_id: Mapped[str] = mapped_column(String, nullable=True)
    options: Mapped[dict] = mapped_column(JSON, default=dict) # {emoji: role_id}
