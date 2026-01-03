import os
import sys
from dotenv import load_dotenv

# Load env vars before anything else
load_dotenv()

from fastapi import FastAPI, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from lithium_core.database.session import get_db
from fastapi.middleware.cors import CORSMiddleware
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.api.router import auth, guilds, modules

import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Structlog Config
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Lithium Bot API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173"), "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(guilds.router)
app.include_router(modules.router)

@app.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    health_status = {"api": "ok", "db": "unknown", "redis": "unknown"}
    
    # DB Check
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        health_status["db"] = "ok"
    except Exception as e:
        logger.error(f"Healthcheck: DB connection failed: {e}")
        health_status["db"] = "failed"
    
    # Redis Check
    try:
        import redis.asyncio as redis_async
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis_async.from_url(redis_url)
        if await r.ping():
            health_status["redis"] = "ok"
    except Exception as e:
        logger.error(f"Healthcheck: Redis connection failed: {e}")
        health_status["redis"] = "failed"

    if "failed" in health_status.values():
        from fastapi import Response
        return Response(content="Degraded", status_code=503)
        
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
