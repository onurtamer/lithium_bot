"""
Access Key Cog - Generate keys for quick dashboard access
Admin-only /key command that creates a 30-character access key
"""

import discord
from discord.ext import commands
from discord import app_commands
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import database session and model
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import AccessKey


def generate_access_key(length: int = 30) -> str:
    """Generate a cryptographically secure random key"""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class AccessKeyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="key", description="Dashboard erişim anahtarı oluştur (Sadece Yöneticiler)")
    @app_commands.default_permissions(administrator=True)
    async def create_key(self, interaction: discord.Interaction):
        """Generate a 30-character access key for this guild"""
        
        # Check if user has administrator permission
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Yönetici** yetkisine sahip olmalısınız.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Generate unique key
            new_key = generate_access_key(30)
            
            # Store in database
            async with AsyncSessionLocal() as db:
                # Deactivate any existing keys for this guild
                existing_keys = await db.execute(
                    select(AccessKey).where(
                        AccessKey.guild_discord_id == str(interaction.guild.id),
                        AccessKey.is_active == True
                    )
                )
                for old_key in existing_keys.scalars():
                    old_key.is_active = False
                
                # Create new key with 24h expiration
                expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
                
                access_key = AccessKey(
                    key=new_key,
                    guild_discord_id=str(interaction.guild.id),
                    created_by_discord_id=str(interaction.user.id),
                    expires_at=expires_at,
                    is_active=True
                )
                db.add(access_key)
                await db.commit()

            # Create embed for response
            embed = discord.Embed(
                title="🔑 Dashboard Erişim Anahtarı",
                description="Bu anahtar ile Discord girişi olmadan dashboard'a erişebilirsiniz.",
                color=0x39FF14  # Lithium green
            )
            embed.add_field(
                name="Anahtar",
                value=f"```{new_key}```",
                inline=False
            )
            embed.add_field(
                name="Sunucu",
                value=interaction.guild.name,
                inline=True
            )
            embed.add_field(
                name="Geçerlilik",
                value="24 saat",
                inline=True
            )
            embed.add_field(
                name="Kullanım",
                value="[lithiumbot.xyz/login](https://lithiumbot.xyz/login) adresinde anahtarı girin.",
                inline=False
            )
            embed.set_footer(text="⚠️ Bu anahtarı kimseyle paylaşmayın!")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Anahtar oluşturulurken bir hata oluştu: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AccessKeyCog(bot))
