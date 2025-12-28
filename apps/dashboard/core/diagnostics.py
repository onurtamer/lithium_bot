import os
import redis
import json
import uuid
import time

def run_guild_diagnostics(guild_id):
    """
    Sends a diagnostic request to the bot via Redis and waits for a response.
    Returns a dict of status checks.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = redis.from_url(redis_url)
    
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "guild_id": str(guild_id),
        "action": "DIAGNOSTIC"
    }
    
    # Broadcast request
    r.publish("guild_config_changed", json.dumps(payload))
    
    # Wait for response in Redis (using a unique key)
    # The bot should write to 'diag_res:{request_id}'
    res_key = f"diag_res:{request_id}"
    
    # Poll for 3 seconds
    for _ in range(30):
        res = r.get(res_key)
        if res:
            r.delete(res_key)
            return json.loads(res)
        time.sleep(0.1)
        
    # Default failure response if bot doesn't reply
    return {
        "permissions": False,
        "role_hierarchy": False,
        "intents": False,
        "log_access": False,
        "slash_sync": False,
        "error": "Bot timeout. Is the bot online?"
    }
