import pytest
import redis
import os
from sqlalchemy import create_url
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.asyncio
async def test_database_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set")
    
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        assert conn is not None
    await engine.dispose()

def test_redis_connection():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        pytest.skip("REDIS_URL not set")
    
    r = redis.from_url(redis_url)
    assert r.ping() is True
