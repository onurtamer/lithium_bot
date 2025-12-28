from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lithium_core.database.session import get_db
from lithium_core.models import User, OAuthSession
import httpx
import os
from datetime import datetime, timedelta
from jose import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

@router.get("/discord")
async def login_discord():
    return RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    )

@router.get("/discord/callback")
async def discord_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://discord.com/api/oauth2/token", data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        
        token_data = token_res.json()
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="Invalid code")
        
        user_res = await client.get("https://discord.com/api/users/@me", headers={
            "Authorization": f"Bearer {token_data['access_token']}"
        })
        user_data = user_res.json()
        
        # Save User
        discord_id = user_data["id"]
        result = await db.execute(select(User).where(User.discord_id == discord_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(discord_id=discord_id, username=user_data["username"], avatar_url=user_data["avatar"])
            db.add(user)
        else:
            user.username = user_data["username"]
            user.avatar_url = user_data["avatar"]
            
        await db.commit()
        await db.refresh(user)

        # Update/Create OAuth Session
        session_result = await db.execute(select(OAuthSession).where(OAuthSession.user_id == user.id))
        oauth_session = session_result.scalar_one_or_none()
        
        expire_at_iso = (datetime.utcnow() + timedelta(seconds=token_data["expires_in"])).isoformat()
        
        if not oauth_session:
            oauth_session = OAuthSession(
                user_id=user.id, 
                access_token=token_data["access_token"], 
                refresh_token=token_data["refresh_token"],
                expires_at=expire_at_iso
            )
            db.add(oauth_session)
        else:
            oauth_session.access_token = token_data["access_token"]
            oauth_session.refresh_token = token_data["refresh_token"]
            oauth_session.expires_at = expire_at_iso
        
        await db.commit()

        # Create JWT
        access_token_expires = timedelta(minutes=60 * 24 * 7) # 7 days
        expire = datetime.utcnow() + access_token_expires
        encoded_jwt = jwt.encode({"sub": str(user.id), "discord_id": discord_id, "exp": expire}, JWT_SECRET, algorithm=ALGORITHM)
        
        response = RedirectResponse(url=f"{os.getenv('FRONTEND_URL')}/app")
        response.set_cookie(key="access_token", value=encoded_jwt, httponly=True, samesite='lax', secure=False) # Secure=True in prod
        return response

@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
             raise HTTPException(status_code=401)
        return user
    except:
        raise HTTPException(status_code=401)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
