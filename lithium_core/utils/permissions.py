def define_role(guild_data, user_id):
    """
    Determines the RBAC role for a user in a guild.
    Roles: OWNER, ADMIN, MODERATOR, VIEWER
    """
    # Check ownership
    if str(guild_data.get('owner_id')) == str(user_id) or guild_data.get('owner'):
        return "OWNER"
        
    permissions = int(guild_data.get('permissions', 0))
    
    # Check permissions logic
    # 0x8 = Administrator
    if (permissions & 0x8) == 0x8: 
        return "ADMIN"
        
    # 0x20 = Manage Guild
    if (permissions & 0x20) == 0x20: 
        return "MODERATOR"
        
    return "VIEWER"
