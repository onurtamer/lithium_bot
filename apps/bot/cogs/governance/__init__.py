"""
Governance Module - Bot Autocracy Implementation
"""
from .pipeline import EventPipeline
from .policy_engine import PolicyEngine
from .action_dispatch import ActionDispatcher
from .safe_mode import SafeModeHandler

__all__ = [
    "EventPipeline",
    "PolicyEngine", 
    "ActionDispatcher",
    "SafeModeHandler"
]


async def setup(bot):
    """Load all governance cogs"""
    from .pipeline import EventPipeline
    from .safe_mode import SafeModeHandler
    
    await bot.add_cog(EventPipeline(bot))
    await bot.add_cog(SafeModeHandler(bot))
