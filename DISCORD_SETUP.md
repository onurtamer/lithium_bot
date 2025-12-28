# Discord Developer Portal Setup Guide

Follow these steps to correctly configure your application in the [Discord Developer Portal](https://discord.com/developers/applications).

## 1. General Information
- **Name**: Lithium Bot
- **App Icon**: (Upload your preferred icon)
- **Description**: An all-in-one Discord management bot with an advanced HTMX dashboard.

## 2. OAuth2 Configuration
- **Redirects**: Add the following URL:
  `http://localhost:5173/auth/callback` (for Development)
  `https://lithiumbot.xyz/auth/callback` (for Production)
- **Scopes**:
  - `identify`
  - `guilds`
  - `bot`
  - `applications.commands` (for Slash Commands)

## 3. Bot Settings
- **Privileged Gateway Intents**: Enable the following (Required for functionality):
  - [x] Presence Intent
  - [x] Server Members Intent
  - [x] Message Content Intent
- **Public Bot**: (Optional) Uncheck if you want to keep the bot private.

## 4. Invite URL Generator
Generate an invite URL using the following settings:
- **Scopes**: `bot`, `applications.commands`
- **Permissions**: `Administrator` (or use the Permission Matrix in `PERMISSIONS.md`)

## 5. Credentials
Copy the following to your `.env` file:
- **CLIENT ID** -> `DISCORD_CLIENT_ID`
- **CLIENT SECRET** -> `DISCORD_CLIENT_SECRET`
- **TOKEN** -> `DISCORD_TOKEN`
