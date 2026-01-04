"""
Auth utilities for Lithium API
Re-exports from router.auth for backward compatibility
"""

import os

from fastapi import Depends, HTTPException, Request
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lithium_core.database.session import get_db
from lithium_core.models import User

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    This is the proper dependency version (not a route handler).
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

        # Check if this is a key-based auth
        if payload.get("key_auth"):

            class KeyUser:
                """Mock User-like object for key-based auth"""

                id = 0
                discord_id = "0"
                username = "Key Access"
                avatar_url = None
                key_auth = True
                guild_id = payload.get("guild_id")

            return KeyUser()

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# Alias for compatibility with guilds_v2.py
get_me = get_current_user

# Re-export User model
__all__ = ["get_me", "get_current_user", "User"]
