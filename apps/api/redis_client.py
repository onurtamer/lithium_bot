"""
Redis client utility for Lithium API
"""

import os

import redis.asyncio as redis_async

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def get_redis() -> redis_async.Redis:
    """Get an async Redis connection"""
    return redis_async.from_url(REDIS_URL, decode_responses=True)
