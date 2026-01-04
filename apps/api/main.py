"""
Lithium Bot API - Main Application
"""

# ruff: noqa: E402
import os
import sys

from dotenv import load_dotenv

# Load env vars before anything else - must be before other imports
load_dotenv()

# Add project root to path - must be before local imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import redis.asyncio as redis_async
import structlog
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.router import auth, guilds, guilds_v2, modules
from apps.api.websocket import router as ws_router
from apps.api.event_bus import event_bus
from lithium_core.database.session import get_db

# Structlog Config
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


# Lifespan for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - with error handling to prevent 502
    try:
        await event_bus.connect()
        await event_bus.start_listening()
        logger.info("EventBus started")
    except Exception as e:
        logger.error(f"EventBus startup failed: {e}")
    yield
    # Shutdown
    try:
        await event_bus.disconnect()
        logger.info("EventBus stopped")
    except Exception as e:
        logger.error(f"EventBus shutdown error: {e}")


app = FastAPI(title="Lithium Bot API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Dynamic origin list
cors_origins: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]

# Add production frontend URL
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cors_origins.append(frontend_url)

# Add production domain
production_domain = os.getenv("PRODUCTION_DOMAIN", "https://lithiumbot.xyz")
if production_domain not in cors_origins:
    cors_origins.append(production_domain)
    cors_origins.append(production_domain.replace("https://", "http://"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(guilds.router)
app.include_router(modules.router)
app.include_router(guilds_v2.router)
app.include_router(ws_router)  # WebSocket gateway


@app.get("/health", response_model=None)
@limiter.limit("5/minute")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    health_status: dict[str, str] = {"api": "ok", "db": "unknown", "redis": "unknown"}

    # DB Check
    try:
        await db.execute(text("SELECT 1"))
        health_status["db"] = "ok"
    except Exception as e:
        logger.error(f"Healthcheck: DB connection failed: {e}")
        health_status["db"] = "failed"

    # Redis Check
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis_async.from_url(redis_url)
        if await r.ping():
            health_status["redis"] = "ok"
        await r.aclose()
    except Exception as e:
        logger.error(f"Healthcheck: Redis connection failed: {e}")
        health_status["redis"] = "failed"

    if "failed" in health_status.values():
        return Response(content="Degraded", status_code=503)

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
