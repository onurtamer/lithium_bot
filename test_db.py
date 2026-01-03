import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connect(host):
    print(f"\n--- Testing host: {host} ---")
    try:
        # Construct URL manually
        # postgresql://user:pass@host:port/dbname
        user = "postgres"
        password = "postgres"
        dbname = "lithium"
        port = "5432"
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        
        print(f"Connecting to {dsn}...")
        conn = await asyncpg.connect(dsn)
        print(f"SUCCESS: Connected to {host}!")
        await conn.close()
        return True
    except Exception as e:
        print(f"FAILED {host}: {str(e)}")
        return False

async def main():
    hosts = ["127.0.0.1", "localhost"]
    results = []
    for h in hosts:
        res = await test_connect(h)
        results.append(res)
    
    if any(results):
        print("\nAt least one connection succeeded.")
    else:
        print("\nAll connection attempts failed.")

if __name__ == "__main__":
    asyncio.run(main())
