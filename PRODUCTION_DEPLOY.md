# Lithium Bot - Production Deployment Guide

This guide provides a step-by-step walkthrough for deploying Lithium Bot on a Linux VPS (Ubuntu 22.04/24.04 recommended).

## 1. VPS Preparation

### Install Docker
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
```

### Configure Firewall (UFW)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 2. Discord Developer Portal

1.  **Intents**: Enable `Message Content`, `Server Members`, and `Presence` in the Bot tab.
2.  **Redirect URI**: Add `https://your-domain.com/auth/callback`.
3.  **Permissions**: Use the invite link with `Administrator` or the scoped permissions defined in `PERMISSIONS.md`.

## 3. Environment Configuration

Copy `.env.example` to `.env` and fill in the production values:
```bash
cp .env.example .env
nano .env
```
Key production variables:
- `APP_ENV=production`
- `ALLOWED_HOSTS=your-domain.com`
- `CSRF_TRUSTED_ORIGINS=https://your-domain.com`
- `SESSION_COOKIE_SECURE=True`

## 4. Deployment

### Start Services
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Initialize Database
```bash
docker compose exec api alembic upgrade head
docker compose exec api python lithium_core/scripts/seed.py
```

### Static Files (Django)
```bash
docker compose exec panel python manage.py collectstatic --noinput
```

## 5. Reverse Proxy & SSL (Nginx)

1.  **Install Nginx**: `sudo apt install nginx`
2.  **Configure Site**: Copy `nginx/lithium.conf` to `/etc/nginx/sites-available/lithium` and link it.
3.  **SSL (Certbot)**:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d lithiumbot.xyz
    ```

## 6. Maintenance & Backups

### Logs
View logs in JSON format for better observability:
```bash
docker compose logs -f api
docker compose logs -f bot
```

### Automated Backups
Schedule the backup script using cron:
```bash
chmod +x scripts/backup_db.sh
crontab -e
# Add: 0 3 * * * /path/to/lithium_bot/scripts/backup_db.sh
```

## 7. Update Flow
To update the bot to a new version:
```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose exec api alembic upgrade head
```

---
*For troubleshooting, check health endpoints at `https://lithiumbot.xyz/health` (API) and `https://lithiumbot.xyz:8080/health` (Bot internal).*
