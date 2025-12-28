from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
from typing import Optional

class ReactionRoleMenu(Base, TimestampMixin):
    __tablename__ = "reaction_role_menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    message_id: Mapped[str] = mapped_column(String, unique=True)
    channel_id: Mapped[str] = mapped_column(String)
    
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class ReactionRoleItem(Base):
    __tablename__ = "reaction_role_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("reaction_role_menus.id"))
    emoji: Mapped[str] = mapped_column(String)
    role_id: Mapped[str] = mapped_column(String)
