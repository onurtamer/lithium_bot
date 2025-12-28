import discord
from sqlalchemy import select
from lithium_core.database.session import AsyncSessionLocal
from lithium_core.models import CommandPermission

async def check_command_permission(interaction: discord.Interaction, command_name: str) -> bool:
    """
    Checks if the user has a role that is allowed to use the given command.
    If no permissions are set in DB, it falls back to standard Discord permissions.
    """
    if interaction.user.guild_permissions.administrator:
        return True

    async with AsyncSessionLocal() as db:
        stmt = select(CommandPermission).where(
            CommandPermission.guild_id == str(interaction.guild_id),
            CommandPermission.command_name == command_name
        )
        allowed_roles = (await db.execute(stmt)).scalars().all()
        
        if not allowed_roles:
            return True # No restriction, use default d.py checks

        user_role_ids = [str(role.id) for role in interaction.user.roles]
        for p in allowed_roles:
            if p.role_id in user_role_ids:
                return True
                
    return False
