from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String, nullable=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    
    status: Mapped[str] = mapped_column(String, default="OPEN") # OPEN, CLAIMED, CLOSED
    claimed_by: Mapped[str] = mapped_column(String, nullable=True)
    
    category: Mapped[str] = mapped_column(String, default="support")
    
    messages: Mapped[list["TicketMessage"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base, TimestampMixin):
    __tablename__ = "ticket_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    author_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    attachments: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")

class TicketConfig(Base, TimestampMixin):
    __tablename__ = "ticket_configs"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    support_role_id: Mapped[str] = mapped_column(String, nullable=True)
    categories: Mapped[list[dict]] = mapped_column(JSON, default=list) # [{"label": "General", "value": "gen", "emoji": "❓"}]
