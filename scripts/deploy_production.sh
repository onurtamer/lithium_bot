#!/bin/bash
# ============================================
# Lithium Bot - Production Deployment Script
# Domain: lithiumbot.xyz
# VPS: 93.127.213.114
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Lithium Bot - Production Deploy     ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# ============================================
# Step 1: System Update
# ============================================
echo -e "\n${YELLOW}[1/8] Updating system packages...${NC}"
apt update && apt upgrade -y

# ============================================
# Step 2: Install Docker
# ============================================
echo -e "\n${YELLOW}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    apt install -y docker-compose-plugin
fi

# ============================================
# Step 3: Install Nginx
# ============================================
echo -e "\n${YELLOW}[3/8] Installing Nginx...${NC}"
apt install -y nginx
systemctl enable nginx

# ============================================
# Step 4: Configure Firewall
# ============================================
echo -e "\n${YELLOW}[4/8] Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo -e "${GREEN}Firewall configured${NC}"

# ============================================
# Step 5: Setup Project Directory
# ============================================
echo -e "\n${YELLOW}[5/8] Setting up project directory...${NC}"
PROJECT_DIR="/opt/lithium"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone or pull repository
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git pull
else
    echo "Cloning repository..."
    # You'll need to update this URL
    git clone https://github.com/onurtamer/lithium_bot.git .
fi

# ============================================
# Step 6: Configure Environment
# ============================================
echo -e "\n${YELLOW}[6/8] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your credentials:${NC}"
        echo "   nano /opt/lithium/.env"
        echo ""
        echo "   Required values:"
        echo "   - DISCORD_TOKEN"
        echo "   - DISCORD_CLIENT_ID"
        echo "   - DISCORD_CLIENT_SECRET"
        echo "   - POSTGRES_PASSWORD"
        echo "   - JWT_SECRET"
    else
        echo -e "${RED}ERROR: .env.production not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

# ============================================
# Step 7: Setup Nginx
# ============================================
echo -e "\n${YELLOW}[7/8] Configuring Nginx...${NC}"

# Copy nginx config
cp nginx/lithium.conf /etc/nginx/sites-available/lithium

# Create certbot webroot
mkdir -p /var/www/certbot

# Enable site (temporarily comment out SSL for initial certbot run)
cat > /etc/nginx/sites-available/lithium-temp << 'EOF'
server {
    listen 80;
    server_name lithiumbot.xyz www.lithiumbot.xyz;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

# Enable temp config first
ln -sf /etc/nginx/sites-available/lithium-temp /etc/nginx/sites-enabled/lithium
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ============================================
# Step 8: SSL Certificate
# ============================================
echo -e "\n${YELLOW}[8/8] Setting up SSL certificate...${NC}"

# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
if [ ! -d "/etc/letsencrypt/live/lithiumbot.xyz" ]; then
    certbot certonly --webroot -w /var/www/certbot \
        -d lithiumbot.xyz -d www.lithiumbot.xyz \
        --non-interactive --agree-tos \
        --email admin@lithiumbot.xyz
    
    echo -e "${GREEN}SSL certificate obtained${NC}"
else
    echo -e "${GREEN}SSL certificate already exists${NC}"
fi

# Now enable full nginx config with SSL
ln -sf /etc/nginx/sites-available/lithium /etc/nginx/sites-enabled/lithium
nginx -t && systemctl reload nginx

# Setup auto-renewal
systemctl enable certbot.timer

# ============================================
# Deployment Complete - Show Next Steps
# ============================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Initial Setup Complete!             ${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Edit the .env file with your Discord credentials:"
echo "   ${BLUE}nano /opt/lithium/.env${NC}"
echo ""
echo "2. Start the services:"
echo "   ${BLUE}cd /opt/lithium${NC}"
echo "   ${BLUE}docker compose -f docker-compose.prod.yml up -d --build${NC}"
echo ""
echo "3. Run database migrations:"
echo "   ${BLUE}docker compose exec api alembic upgrade head${NC}"
echo ""
echo "4. Verify everything is working:"
echo "   ${BLUE}docker compose ps${NC}"
echo "   ${BLUE}curl https://lithiumbot.xyz/health${NC}"
echo ""
echo -e "${GREEN}Your site will be available at: https://lithiumbot.xyz${NC}"
