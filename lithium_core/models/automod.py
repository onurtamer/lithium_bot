from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class AutoModRule(Base, TimestampMixin):
    __tablename__ = "automod_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    
    rule_type: Mapped[str] = mapped_column(String) # SPAM, BAD_WORDS, INVITES, LINKS, MENTION_SPAM
    config: Mapped[dict] = mapped_column(JSON) # Thresholds, regex patterns, allowlists
    actions: Mapped[dict] = mapped_column(JSON) # {type: DELETE/WARN/TIMEOUT, duration: 60}
    
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    exempt_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    exempt_channels: Mapped[list[str]] = mapped_column(JSON, default=list)
