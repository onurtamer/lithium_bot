# Release Checklist

- [ ] **Environment**
    - [ ] `DISCORD_TOKEN` set
    - [ ] `DISCORD_CLIENT_ID` / `SECRET` set
    - [ ] `JWT_SECRET` changed from default

- **Discord Developer Portal**
    - [ ] **Intents**: `Message Content`, `Server Members`, `Presence` enabled.
    - [ ] **Redirect URL**: Added `http://your-domain.com/auth/discord/callback`.
    - [ ] **Bot Public**: Disabled (if private bot).

- **Deployment**
    - [ ] `docker compose up -d --build` successful.
    - [ ] `docker compose logs` shows no errors.
    - [ ] Database tables created (Alembic).

- **Verification**
    - [ ] Login via Panel works.
    - [ ] Dashboard lists guilds.
    - [ ] Bot responds to `/ping`.
    - [ ] Modifying a setting (e.g. Leveling) updates DB.
