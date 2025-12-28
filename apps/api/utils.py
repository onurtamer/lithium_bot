import httpx
import os
from typing import Any, Optional

DISCORD_API_URL = "https://discord.com/api/v10"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/auth/callback")

async def exchange_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await client.post(f"{DISCORD_API_URL}/oauth2/token", data=data, headers=headers)
        response.raise_for_status()
        return response.json()

async def get_user_profile(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{DISCORD_API_URL}/users/@me", headers=headers)
        response.raise_for_status()
        return response.json()

async def get_user_guilds(access_token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{DISCORD_API_URL}/users/@me/guilds", headers=headers)
        response.raise_for_status()
        return response.json()
