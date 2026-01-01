"""
Fun & Entertainment Models
- Giveaways, Birthdays, Mini Games, Suggestions
"""
from sqlalchemy import String, Integer, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional, List
from datetime import datetime


class Giveaway(Base, TimestampMixin):
    """Çekiliş sistemi için model"""
    __tablename__ = "giveaways"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String)
    message_id: Mapped[str] = mapped_column(String, unique=True)
    host_id: Mapped[str] = mapped_column(String)
    prize: Mapped[str] = mapped_column(String)
    winner_count: Mapped[int] = mapped_column(Integer, default=1)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    ended: Mapped[bool] = mapped_column(Boolean, default=False)
    winners: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    required_role_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Birthday(Base, TimestampMixin):
    """Doğum günü kayıtları"""
    __tablename__ = "birthdays"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    day: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)


class BirthdayConfig(Base, TimestampMixin):
    """Doğum günü kanal ayarları"""
    __tablename__ = "birthday_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    channel_id: Mapped[str] = mapped_column(String)
    message_template: Mapped[str] = mapped_column(Text, default="🎂 Bugün {user}'in doğum günü! İyi ki doğdun! 🎉")
    role_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Birthday role


class Suggestion(Base, TimestampMixin):
    """Öneri sistemi"""
    __tablename__ = "suggestions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String)
    message_id: Mapped[str] = mapped_column(String, unique=True)
    author_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING, APPROVED, DENIED, IMPLEMENTED
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    downvotes: Mapped[int] = mapped_column(Integer, default=0)
    staff_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SuggestionConfig(Base, TimestampMixin):
    """Öneri kanalı ayarları"""
    __tablename__ = "suggestion_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    channel_id: Mapped[str] = mapped_column(String)
    upvote_emoji: Mapped[str] = mapped_column(String, default="👍")
    downvote_emoji: Mapped[str] = mapped_column(String, default="👎")


class DuelStats(Base, TimestampMixin):
    """Düello istatistikleri"""
    __tablename__ = "duel_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
