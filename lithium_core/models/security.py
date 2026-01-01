"""
Security & Moderation Advanced Models
- Jail System, Bad Words, Mute System, Voice Protection
"""
from sqlalchemy import String, Integer, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional, List
from datetime import datetime


class JailConfig(Base, TimestampMixin):
    """Jail/Hapis sistemi ayarları"""
    __tablename__ = "jail_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    jail_role_id: Mapped[str] = mapped_column(String)
    jail_channel_id: Mapped[str] = mapped_column(String)
    log_channel_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class JailedUser(Base, TimestampMixin):
    """Hapiste olan kullanıcılar"""
    __tablename__ = "jailed_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    jailed_by: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    previous_roles: Mapped[List[str]] = mapped_column(JSON, default=list)  # Eski rolleri sakla
    jailed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    release_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Süreli hapis


class BadWordFilter(Base, TimestampMixin):
    """Küfür/Argo kelime listesi"""
    __tablename__ = "bad_word_filters"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    word: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String, default="WARN")  # WARN, DELETE, MUTE, KICK


class AutoModConfig(Base, TimestampMixin):
    """Gelişmiş AutoMod ayarları"""
    __tablename__ = "automod_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    # Caps Lock Protection
    caps_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    caps_threshold: Mapped[int] = mapped_column(Integer, default=70)  # %70
    caps_min_length: Mapped[int] = mapped_column(Integer, default=10)  # Minimum mesaj uzunluğu
    
    # Spam Protection
    spam_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    spam_threshold: Mapped[int] = mapped_column(Integer, default=5)  # 5 mesaj
    spam_interval: Mapped[int] = mapped_column(Integer, default=5)  # 5 saniye
    spam_action: Mapped[str] = mapped_column(String, default="MUTE")  # WARN, MUTE, KICK
    spam_mute_duration: Mapped[int] = mapped_column(Integer, default=300)  # 5 dakika
    
    # Link Protection
    link_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    link_whitelist: Mapped[List[str]] = mapped_column(JSON, default=list)  # İzin verilen domainler
    link_allowed_roles: Mapped[List[str]] = mapped_column(JSON, default=list)  # Link atabilen roller
    link_allowed_channels: Mapped[List[str]] = mapped_column(JSON, default=list)  # Link atılabilen kanallar
    
    # Bad Words
    bad_words_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Voice Protection (Mic Spam)
    voice_spam_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    voice_spam_threshold: Mapped[int] = mapped_column(Integer, default=5)  # 5 gir-çık
    voice_spam_interval: Mapped[int] = mapped_column(Integer, default=30)  # 30 saniye


class TempMute(Base, TimestampMixin):
    """Süreli mute kayıtları"""
    __tablename__ = "temp_mutes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    moderator_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    muted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    unmute_at: Mapped[datetime] = mapped_column(DateTime)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class VoiceSpamLog(Base, TimestampMixin):
    """Sesli kanal spam logu"""
    __tablename__ = "voice_spam_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    action_taken: Mapped[str] = mapped_column(String)  # DISCONNECT, MUTE
    join_count: Mapped[int] = mapped_column(Integer)


class ModerationWarning(Base, TimestampMixin):
    """Uyarı sistemi"""
    __tablename__ = "moderation_warnings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    moderator_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
