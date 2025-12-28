-- Manually create missing tables for Economy and Ticket features

-- 1. Create economy_profiles table
CREATE TABLE IF NOT EXISTS economy_profiles (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    balance INTEGER DEFAULT 0,
    daily_streak INTEGER DEFAULT 0,
    last_daily TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
);

-- Indexes for economy
CREATE INDEX IF NOT EXISTS ix_economy_profiles_guild_id ON economy_profiles (guild_id);
CREATE INDEX IF NOT EXISTS ix_economy_profiles_user_id ON economy_profiles (user_id);

-- 2. Create ticket_configs table
CREATE TABLE IF NOT EXISTS ticket_configs (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    support_role_id VARCHAR,
    categories JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
);

-- Unique index for ticket config
CREATE UNIQUE INDEX IF NOT EXISTS ix_ticket_configs_guild_id ON ticket_configs (guild_id);

-- 3. Update alembic version to avoid future conflicts (Optional, but good practice)
-- We force it to the latest revision ID '3e87a2b9c1d5'
UPDATE alembic_version SET version_num = '3e87a2b9c1d5';
