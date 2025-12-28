from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class UserLevel(Base, TimestampMixin):
    __tablename__ = "user_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=0)
    
class LevelingConfig(Base, TimestampMixin):
    __tablename__ = "leveling_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    xp_rate: Mapped[float] = mapped_column(Integer, default=1.0) # Multiplier
    no_xp_channels: Mapped[list[str]] = mapped_column(String, default="[]") # JSON string or separate table if needed

class LevelReward(Base, TimestampMixin):
    __tablename__ = "level_rewards"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    
    level_requirement: Mapped[int] = mapped_column(Integer)
    role_id: Mapped[str] = mapped_column(String)
