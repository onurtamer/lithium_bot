"""
Guilds Router - List user's Discord guilds
"""

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.auth import get_me
from lithium_core.database.session import get_db
from lithium_core.models import OAuthSession, User

router = APIRouter(prefix="/guilds", tags=["guilds"])

# Bot token for checking bot membership
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


async def check_bot_in_guild(client: httpx.AsyncClient, guild_id: str) -> bool:
    """Check if the bot is a member of the guild"""
    if not BOT_TOKEN:
        return True  # Assume installed if no bot token configured

    try:
        res = await client.get(
            f"https://discord.com/api/v10/guilds/{guild_id}",
            headers={"Authorization": f"Bot {BOT_TOKEN}"},
        )
        return res.status_code == 200
    except Exception:
        return False


@router.get("")
async def list_guilds(
    user: User = Depends(get_me), db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    """List all guilds user can manage"""
    # Get OAuth Session
    result = await db.execute(
        select(OAuthSession).where(OAuthSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="No Discord session found")

    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )

        if res.status_code == 401:
            raise HTTPException(status_code=401, detail="Discord token expired")

        guilds = res.json()

    manage_guilds: list[dict[str, Any]] = []
    manage_guild_perm = 0x20

    async with httpx.AsyncClient() as client:
        for g in guilds:
            permissions = int(g.get("permissions", 0))
            if (permissions & manage_guild_perm) == manage_guild_perm or g.get("owner"):
                # Check if bot is installed in this guild
                bot_installed = await check_bot_in_guild(client, g["id"])

                manage_guilds.append(
                    {
                        "id": g["id"],
                        "name": g["name"],
                        "icon": g["icon"],
                        "owner": g["owner"],
                        "permissions": permissions,
                        "bot_installed": bot_installed,
                    }
                )

    return manage_guilds
