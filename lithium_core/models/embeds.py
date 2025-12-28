from sqlalchemy import String, Integer, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class EmbedConfig(Base, TimestampMixin):
    __tablename__ = "embed_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(ForeignKey("guilds.id"), index=True)
    name: Mapped[str] = mapped_column(String) # e.g. "welcome", "announcement"
    
    # Embed data
    title: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    color: Mapped[int] = mapped_column(Integer, default=0x3498db)
    thumbnail_url: Mapped[str] = mapped_column(String, nullable=True)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    footer_text: Mapped[str] = mapped_column(String, nullable=True)
    
    guild = relationship("Guild")
