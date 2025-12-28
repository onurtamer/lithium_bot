from sqlalchemy import String, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class QuarantineConfig(Base, TimestampMixin):
    __tablename__ = "quarantine_configs"

    guild_id: Mapped[str] = mapped_column(ForeignKey("guilds.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Anti-raid settings
    max_joins_per_minute: Mapped[int] = mapped_column(Integer, default=10)
    min_account_age_days: Mapped[int] = mapped_column(Integer, default=0)
    require_avatar: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Actions
    action: Mapped[str] = mapped_column(String, default="KICK") # KICK, BAN, QUARANTINE_ROLE
    quarantine_role_id: Mapped[str] = mapped_column(String, nullable=True)
    
    guild = relationship("Guild")

class QuarantineLog(Base, TimestampMixin):
    __tablename__ = "quarantine_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    action_taken: Mapped[str] = mapped_column(String)
