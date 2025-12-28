# Lithium Dashboard - Route List & RBAC

The Lithium Dashboard uses Discord OAuth2 for authentication and a custom RBAC system for authorization.

## Dashboard Routes

| Path | Description | Access Level |
| :--- | :--- | :--- |
| `/app` | Server selection screen. | Authenticated |
| `/app/guild/<id>` | Main dashboard for a server. | Viewer+ |
| `/app/guild/<id>/overview` | Statistics and module overview. | Viewer+ |
| `/app/guild/<id>/audit` | Configuration change logs. | Admin/Owner |
| `/app/guild/<id>/test-configuration` | Real-time diagnostic tool. | Admin/Owner |
| `/app/guild/<id>/<module>` | Module-specific settings (e.g., `/automod`). | Moderator+ |

## RBAC Implementation Details

The dashboard determines permissions on the fly using the user's Discord permissions in the target guild:

1. **Owner**: If `user_id == guild.owner_id`.
2. **Admin**: If user has `ADMINISTRATOR` or `MANAGE_GUILD` flag.
3. **Moderator**: If user has `KICK_MEMBERS`, `BAN_MEMBERS`, or `MANAGE_MESSAGES`.
4. **Viewer**: Any user who is a member of the guild.

> [!NOTE]
> All configuration updates (`POST` requests) are strictly restricted to **Admin** and **Owner** levels to ensure server security.
