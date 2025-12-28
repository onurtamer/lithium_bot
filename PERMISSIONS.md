# Lithium Bot - Permission Matrix & Commands

This document outlines the required Discord permissions and the command structure of Lithium Bot.

## Required Permissions (Bot User)
The bot requires an invite URL with the following permissions (Integer: `8` or `1544412230` for scoped permissions):
- **Administrator** (Recommended for full functionality)
OR
- Manage Channels
- Manage Roles
- Manage Webhooks
- View Audit Log
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use External Emojis
- Add Reactions
- Connect / Speak (for Temporary Voice)

## Automated Command List (Slash Commands)

| Category | Command | Description | Permission Level |
| :--- | :--- | :--- | :--- |
| **Moderation** | `/kick` | Kicks a member from the server. | Moderate Members |
| **Moderation** | `/ban` | Bans a member from the server. | Ban Members |
| **Moderation** | `/mute` | Timeouts a member. | Moderate Members |
| **Utility** | `/remind` | Sets a personal reminder. | Everyone |
| **Utility** | `/afk` | Sets an AFK status. | Everyone |
| **Social** | `/cc-add` | Adds a custom command. | Manage Server |
| **System** | `/sync` | Syncs application commands. | Bot Owner |

## Permission Levels (Custom RBAC)
- **OWNER**: Server Owner. Full access to all dashboard settings.
- **ADMIN**: Users with `Administrator` or `Manage Server` permissions.
- **MODERATOR**: Users with `Manage Messages` or `Kick/Ban` permissions.
- **VIEWER**: Regular users with access to the dashboard (Read-only for most modules).
