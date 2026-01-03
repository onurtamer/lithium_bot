import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import sys
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lithium-bot")

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

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        error_msg = str(error)
        logger.error(f"App command error: {error_msg}")
        traceback.print_exc()
        
        if interaction.response.is_done():
            await interaction.followup.send(f"⚠️ An error occurred: `{error_msg}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ An error occurred: `{error_msg}`", ephemeral=True)

    async def setup_hook(self):
        # Global Error handler setup
        self.tree.on_error = self.on_app_command_error
        logger.info("Setting up Lithium Bot...")

        # --- AUTO DB MIGRATION ---
        try:
            from apps.bot.utils.db_setup import run_migrations_async
            logger.info("Checking database schema (Self-Healing)...")
            await run_migrations_async()
            logger.info("Database schema verification completed.")
        except Exception as e:
            logger.error(f"Startup DB Migration failed: {e}")
            traceback.print_exc()
        # -------------------------

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

        # Load Persistent Views
        try:
            from apps.bot.cogs.tickets import TicketView, TicketControlView
            self.add_view(TicketView(self, []))
            self.add_view(TicketControlView(self))
            logger.info("Persistent views registered.")
        except Exception as e:
            logger.error(f"Failed to register persistent views: {e}")

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
            'apps.bot.cogs.economy',
            'apps.bot.cogs.report',
            'apps.bot.cogs.welcome',
            # Yeni eklenen cog'lar
            'apps.bot.cogs.audit_logging',      # Gelişmiş loglama
            'apps.bot.cogs.advanced_automod',   # Küfür, caps, link, spam koruması
            'apps.bot.cogs.jail',               # Jail ve mute sistemi
            'apps.bot.cogs.fun',                # Çekiliş, doğum günü, düello, aşk ölçer
            'apps.bot.cogs.suggestions',        # Öneri sistemi
            'apps.bot.cogs.extended_utility',   # Userinfo, avatar, hava durumu, döviz
            'apps.bot.cogs.reaction_roles',     # Tepki rolleri
            # Bot-Otokrasi Governance modülü
            'apps.bot.cogs.governance.pipeline',    # Event pipeline
            'apps.bot.cogs.governance.safe_mode',   # Safe mode & lockdown
            'apps.bot.cogs.governance.tickets_v2',  # Report, complaint, request, appeal
            'apps.bot.cogs.access_key',             # Key-based authentication
            'apps.bot.cogs.admin',                  # Admin tools (!sync)
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                traceback.print_exc()

        try:
            await self.tree.sync()
            logger.info("Slash commands synced.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Verifying intents and permissions...")
        
        # Self-Check: Intents
        if not self.intents.message_content or not self.intents.members:
            logger.error("CRITICAL: Missing required intents (Message Content or Members)!")
        
        logger.info("------")
        self.bg_task = self.loop.create_task(self.redis_listener())
        self.stats_task = self.loop.create_task(self.guild_stats_updater())

    async def guild_stats_updater(self):
        """Background task to cache guild stats to Redis for the dashboard"""
        import redis.asyncio as redis_async
        import json
        
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        await self.wait_until_ready()
        logger.info("Guild stats updater started.")
        
        while not self.is_closed():
            try:
                r = redis_async.from_url(redis_url)
                
                for guild in self.guilds:
                    try:
                        # Count online members
                        online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
                        
                        stats = {
                            "total": guild.member_count,
                            "online": online_count,
                            "new_24h": 0  # Would need to track join events for this
                        }
                        
                        # Cache to Redis with 5 minute expiry
                        await r.set(
                            f"guild:stats:{guild.id}:members",
                            json.dumps(stats),
                            ex=300
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update stats for guild {guild.id}: {e}")
                
                await r.aclose()
                
            except Exception as e:
                logger.error(f"Guild stats updater error: {e}")
            
            # Update every 60 seconds
            await asyncio.sleep(60)

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

    @bot.command()
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    async def sync(ctx):
        """Sync commands to the current guild immediately."""
        try:
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"✅ Synced {len(synced)} commands to this guild!")
        except Exception as e:
            await ctx.send(f"❌ Sync failed: {e}")
    
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
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
