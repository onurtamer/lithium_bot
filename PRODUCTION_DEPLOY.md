# Lithium Bot - Production Deployment Guide

🌐 **Domain:** lithiumbot.xyz  
🖥️ **VPS:** 93.127.213.114  
🐧 **OS:** Ubuntu 22.04

---

## 📋 Quick Start

```bash
# 1. SSH into VPS
ssh root@93.127.213.114

# 2. Clone repository
git clone https://github.com/onurtamer/lithium_bot.git /opt/lithium
cd /opt/lithium

# 3. Run deployment script
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh

# 4. Edit environment file with your credentials
nano .env

# 5. Start services
./scripts/start_services.sh
```

---

## 🔑 Required Credentials

Before deployment, you need these from [Discord Developer Portal](https://discord.com/developers/applications):

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Bot token from Bot tab |
| `DISCORD_CLIENT_ID` | Application ID |
| `DISCORD_CLIENT_SECRET` | OAuth2 Client Secret |

And generate these secrets:
```bash
# Generate JWT_SECRET (64 characters)
openssl rand -hex 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 24
```

---

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │   Cloudflare    │ (Optional CDN)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Nginx       │ :443 (SSL)
                    │  Rate Limiting  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  Next.js │        │  FastAPI │        │  Bot     │
  │  :3000   │        │  :8000   │        │  :8080   │
  │(Frontend)│        │  (API)   │        │(Discord) │
  └────┬─────┘        └────┬─────┘        └────┬─────┘
       │                   │                   │
       └─────────┬─────────┴─────────┬─────────┘
                 │                   │
          ┌──────▼─────┐      ┌──────▼─────┐
          │ PostgreSQL │      │   Redis    │
          │   :5432    │      │   :6379    │
          └────────────┘      └────────────┘
```

---

## 📁 Directory Structure

```
/opt/lithium/
├── .env                    # Production environment variables
├── docker-compose.prod.yml # Production Docker configuration
├── nginx/
│   └── lithium.conf       # Nginx reverse proxy config
├── scripts/
│   ├── deploy_production.sh   # Initial deployment
│   ├── start_services.sh      # Start/restart services
│   └── backup_db.sh           # Database backup
├── apps/
│   ├── api/               # FastAPI backend
│   ├── web/               # Next.js Control Center
│   └── bot/               # Discord.py bot
└── backups/               # Database backups
```

---

## 🚀 Deployment Steps

### Step 1: Initial Server Setup

```bash
# SSH into VPS
ssh root@93.127.213.114

# Clone repository
git clone https://github.com/onurtamer/lithium_bot.git /opt/lithium
cd /opt/lithium

# Run automated setup
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh
```

This script will:
- ✅ Update system packages
- ✅ Install Docker & Docker Compose
- ✅ Install & configure Nginx
- ✅ Setup UFW firewall (22, 80, 443)
- ✅ Obtain SSL certificate via Certbot
- ✅ Create `.env` from template

### Step 2: Configure Environment

```bash
nano /opt/lithium/.env
```

Fill in the required values:

```env
# Discord credentials
DISCORD_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here

# Database password (generate with: openssl rand -base64 24)
POSTGRES_PASSWORD=your_secure_password_here

# JWT secret (generate with: openssl rand -hex 32)
JWT_SECRET=your_64_char_secret_here
```

### Step 3: Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. **Bot** tab:
   - Copy the Bot Token
   - Enable `MESSAGE CONTENT INTENT`
   - Enable `SERVER MEMBERS INTENT`
   - Enable `PRESENCE INTENT`
4. **OAuth2** tab:
   - Add Redirect URI: `https://lithiumbot.xyz/auth/callback`
   - Copy Client ID and Client Secret

### Step 4: Start Services

```bash
cd /opt/lithium
./scripts/start_services.sh
```

Or manually:
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose exec api alembic upgrade head
```

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker compose ps

# Check API health
curl https://lithiumbot.xyz/health

# Check logs
docker compose logs -f api
docker compose logs -f bot
docker compose logs -f web
```

---

## 🔧 Maintenance

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f bot
docker compose logs -f api
docker compose logs -f web
```

### Restart Services
```bash
docker compose -f docker-compose.prod.yml restart
```

### Update Application
```bash
cd /opt/lithium
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose exec api alembic upgrade head
```

### Database Backup
```bash
# Manual backup
./scripts/backup_db.sh

# Setup automatic daily backup (3 AM)
crontab -e
# Add: 0 3 * * * /opt/lithium/scripts/backup_db.sh
```

### Database Restore
```bash
# Stop services
docker compose stop

# Restore from backup
gunzip -c backups/lithium_db_YYYYMMDD.sql.gz | \
    docker compose exec -T postgres psql -U lithium_admin lithium

# Start services
docker compose start
```

### SSL Certificate Renewal
```bash
# Test renewal
certbot renew --dry-run

# Force renewal
certbot renew --force-renewal
systemctl reload nginx
```

---

## 🔒 Security Checklist

- [x] UFW firewall enabled (only 22, 80, 443 open)
- [x] SSL/TLS with Let's Encrypt
- [x] HTTP to HTTPS redirect
- [x] HSTS enabled
- [x] Rate limiting on API endpoints
- [x] Secure headers (X-Frame-Options, etc.)
- [x] Database not exposed to public
- [x] Redis not exposed to public
- [ ] Change SSH port (optional)
- [ ] Setup fail2ban (optional)
- [ ] Enable Cloudflare proxy (optional)

---

## 📊 Monitoring

### Health Endpoints
- **API:** https://lithiumbot.xyz/health
- **Bot:** Internal only (check logs)

### Resource Usage
```bash
docker stats
```

### Disk Space
```bash
df -h
docker system df
```

### Clean Docker (if disk full)
```bash
docker system prune -a
```

---

## 🆘 Troubleshooting

### Bot not connecting
```bash
# Check bot logs
docker compose logs bot

# Verify token in .env
grep DISCORD_TOKEN .env
```

### OAuth not working
1. Check `DISCORD_REDIRECT_URI` matches Discord Developer Portal
2. Verify `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET`
3. Check API logs: `docker compose logs api`

### Database connection failed
```bash
# Check postgres is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Verify DATABASE_URL in .env
```

### Nginx returning 502
```bash
# Check if backend services are running
docker compose ps

# Check nginx config
nginx -t

# Restart nginx
systemctl restart nginx
```

---

## 📞 Support

For issues or questions:
- Check logs first: `docker compose logs -f`
- Database: Check postgres container health
- Bot: Verify Discord token and intents
- Web: Check Next.js build logs
