from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lithium_core.database.session import get_db
from lithium_core.models import User, OAuthSession, Guild
from .auth import ALGORITHM, JWT_SECRET, get_me
import httpx
from jose import jwt

router = APIRouter(prefix="/guilds", tags=["guilds"])

@router.get("")
async def list_guilds(user: User = Depends(get_me), db: AsyncSession = Depends(get_db)):
    # Get OAuth Session
    result = await db.execute(select(OAuthSession).where(OAuthSession.user_id == user.id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=401, detail="No Discord session found")

    async with httpx.AsyncClient() as client:
        res = await client.get("https://discord.com/api/users/@me/guilds", headers={
            "Authorization": f"Bearer {session.access_token}"
        })
        
        if res.status_code == 401:
            # Refresh logic should be implemented via a background worker or middleware
            # to ensure high availability of tokens.
            raise HTTPException(status_code=401, detail="Discord token expired")
            
        guilds = res.json()
        
    manage_guilds = []
    MANAGE_GUILD_PERM = 0x20
    
    for g in guilds:
        permissions = int(g.get("permissions", 0))
        if (permissions & MANAGE_GUILD_PERM) == MANAGE_GUILD_PERM or g.get("owner"):
            manage_guilds.append({
                "id": g["id"],
                "name": g["name"],
                "icon": g["icon"],
                "owner": g["owner"],
                "permissions": permissions
            })
            
            # Sync to DB if needed (optional)
            
    return manage_guilds
