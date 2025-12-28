from sqlalchemy import String, Boolean, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from typing import List, Optional

class Guild(Base, TimestampMixin):
    __tablename__ = "guilds"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Discord ID
    name: Mapped[str] = mapped_column(String)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner_id: Mapped[str] = mapped_column(String)
    
    # Module Toggles
    moderation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    automod_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    leveling_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    logs_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tickets_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reaction_roles_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scheduled_messages_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_commands_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sticky_messages_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_responder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    starboard_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    afk_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    temp_voice_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    quarantine_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Configs
    moderation_config = relationship("ModerationConfig", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    welcome_config = relationship("WelcomeConfig", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    leveling_config = relationship("LevelingConfig", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    ticket_config = relationship("TicketConfig", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    quarantine_config = relationship("QuarantineConfig", back_populates="guild", uselist=False, cascade="all, delete-orphan")
    embed_configs = relationship("EmbedConfig", back_populates="guild", cascade="all, delete-orphan")

class ModerationConfig(Base):
    __tablename__ = "moderation_configs"

    guild_id: Mapped[str] = mapped_column(ForeignKey("guilds.id"), primary_key=True)
    log_channel_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mute_role_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    admin_roles: Mapped[List[str]] = mapped_column(JSON, default=list)
    mod_roles: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    guild = relationship("Guild", back_populates="moderation_config")

class WelcomeConfig(Base):
    __tablename__ = "welcome_configs"

    guild_id: Mapped[str] = mapped_column(ForeignKey("guilds.id"), primary_key=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    welcome_message: Mapped[str] = mapped_column(String, default="Welcome {user} to {server}!")
    goodbye_message: Mapped[str] = mapped_column(String, default="{user} has left the server.")
    auto_role_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    use_embed: Mapped[bool] = mapped_column(Boolean, default=True)
    
    guild = relationship("Guild", back_populates="welcome_config")
