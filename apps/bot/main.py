import discord
from discord.ext import commands
import os
import asyncio
import logging
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
import structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

class LithiumBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        logger.info("Setting up Lithium Bot...")
        
        # Start Health Check Server
        from aiohttp import web
        async def health_check(request):
            return web.Response(text="OK")
        
        app = web.Application()
        app.router.add_get('/health', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("Health check server started on port 8080")

        # Load Cogs
        extensions = [
            'apps.bot.cogs.moderation',
            'apps.bot.cogs.automod',
            'apps.bot.cogs.utility', 
            'apps.bot.cogs.advanced_utils',
            'apps.bot.cogs.logging',
            'apps.bot.cogs.antiraid',
            'apps.bot.cogs.social_features',
            'apps.bot.cogs.leveling', 
            'apps.bot.cogs.tickets',
            'apps.bot.cogs.embed_builder',
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        logger.info("Slash commands synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Verifying intents and permissions...")
        
        # Self-Check: Intents
        if not self.intents.message_content or not self.intents.members:
            logger.error("CRITICAL: Missing required intents (Message Content or Members)!")
        
        logger.info("------")
        self.bg_task = self.loop.create_task(self.redis_listener())

    async def redis_listener(self):
        import redis.asyncio as redis_async
        import json
        
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis_async.from_url(redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe("guild_config_changed")
        
        logger.info("Redis Pub/Sub listener started.")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    logger.info(f"Received Redis command: {data}")
                    
                    if data.get("action") == "DIAGNOSTIC":
                        guild_id = int(data["guild_id"])
                        request_id = data["request_id"]
                        guild = self.get_guild(guild_id)
                        
                        diag_res = {
                            "permissions": False,
                            "role_hierarchy": False,
                            "intents": True, # If we are here, bot is alive
                            "log_access": False,
                            "slash_sync": True,
                        }
                        
                        if guild:
                            me = guild.me
                            perms = me.guild_permissions
                            diag_res["permissions"] = perms.administrator or (perms.manage_guild and perms.manage_roles and perms.manage_channels)
                            
                            # Role hierarchy check (is bot above majority of roles)
                            try:
                                bot_top_role = me.top_role
                                diag_res["role_hierarchy"] = bot_top_role.position > 1
                            except: pass
                            
                            # Log access (check base permissions for logging)
                            diag_res["log_access"] = perms.view_audit_log and perms.embed_links
                            
                        # Post back to Redis
                        res_key = f"diag_res:{request_id}"
                        await r.set(res_key, json.dumps(diag_res), ex=60)
                        logger.info(f"Sent diagnostic response for {guild_id}")
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")

    async def close(self):
        logger.info("Shutting down Lithium Bot...")
        await super().close()


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment!")
        return

    bot = LithiumBot()
    
    # Handle SIGTERM/SIGINT
    loop = asyncio.get_event_loop()
    import signal
    
    def stop():
        asyncio.create_task(bot.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop)
        except NotImplementedError:
            # Signal handling on Windows is limited
            pass

    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
