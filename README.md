# Lithium Bot - The Ultimate Discord Management Solution

Lithium is a powerful, production-ready Discord bot suite featuring a modern FastAPI backend, a Discord.py bot client, and a stunning HTMX-powered Django dashboard.

## 🚀 Quick Start (Development)

1. **Clone and Setup Environment**:
   ```bash
   cp .env.example .env
   # Fill in your Discord Bot Token and OAuth2 credentials
   ```

2. **Start Services**:
   ```bash
   make up
   ```

3. **Initialize Database**:
   ```bash
   make init
   ```

4. **Access**:
   - Dashboard: [http://localhost:5173](http://localhost:5173)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🏗️ Production Deployment

### Nginx & SSL Configuration
We recommend using Nginx as a reverse proxy with Let's Encrypt SSL.

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5173; # Panel
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000; # API
        proxy_set_header Host $host;
    }
}
```

### Deployment Command
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Commands & Automation (Makefile)
- `make up`: Start containers.
- `make down`: Stop containers.
- `make init`: Run migrations and seeds.
- `make test`: Run unit, integration, and smoke tests.
- `make lint`: Check code quality.
- `make logs`: View real-time logs.

## 📁 Repository Structure
```text
.
├── apps/
│   ├── api/           # FastAPI Backend
│   ├── bot/           # Discord.py Bot
│   └── dashboard/     # Django Dashboard (Panel)
├── lithium_core/      # Shared Models, Database, and Utils
├── tests/             # Unit, Integration, and Smoke tests
├── docker-compose.yml # Dev environment
├── Makefile           # Automation scripts
└── .env.example       # Environment template
```

## 🛡️ Security & RBAC
Lithium uses a robust Role-Based Access Control system. Details can be found in `RBAC.md` and `PERMISSIONS.md`.

## ❓ Troubleshooting
- **Bot offline?**: Ensure `DISCORD_TOKEN` is correct and Intents are enabled in the Discord Developer Portal.
- **Database error?**: Run `make init` to ensure migrations are applied.
- **Dashboard login failed?**: Check `DISCORD_REDIRECT_URI` matches exactly what's in the Dev Portal.
