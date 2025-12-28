from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from datetime import datetime

class EconomyProfile(Base, TimestampMixin):
    __tablename__ = "economy_profiles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily: Mapped[datetime] = mapped_column(DateTime, nullable=True)
