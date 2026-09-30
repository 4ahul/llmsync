# Deploy LLMSync NOW - Complete Guide

**Status: Ready for Production Deployment** ✅

This guide gets your LLMSync instance running in production within 2 hours.

---

## 🚀 Quick Deploy (30 minutes)

### Option 1: VPS Deployment (Recommended)

**Requirements:**
- Ubuntu 22.04 VPS (4GB RAM, 2 CPU minimum)
- Domain name pointed to your VPS
- SSH access

```bash
# 1. SSH into your VPS
ssh root@your-server.com

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# 3. Install Docker Compose
apt install docker-compose -y

# 4. Clone repository
git clone https://github.com/yourusername/llmsync.git
cd llmsync

# 5. Configure environment
cp .env.example .env
nano .env

# Change these values:
# - SECRET_KEY=<generate-random-32-char-string>
# - POSTGRES_PASSWORD=<strong-password>
# - MINIO_SECRET_KEY=<strong-password>
# - ALLOWED_ORIGINS=https://yourdomain.com

# 6. Start services
docker-compose up -d

# 7. Wait for services to start
sleep 60

# 8. Test
curl http://localhost:8000/api/health

# ✓ You're running!
```

### Option 2: One-Click Deploy

**Coming Soon:**
- ✅ DigitalOcean 1-Click App
- ✅ AWS Marketplace
- ✅ Heroku Button
- ✅ Railway Template

---

## 🔒 Add HTTPS/TLS (Required for Production)

### With Let's Encrypt (Free)

```bash
# 1. Install Certbot
apt install certbot nginx -y

# 2. Get SSL certificate
certbot certonly --standalone -d yourdomain.com

# 3. Create nginx config
cat > /etc/nginx/sites-available/llmsync << 'EOF'
upstream llmsync_api {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API proxy
    location / {
        proxy_pass http://llmsync_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /api/sync/ws {
        proxy_pass http://llmsync_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
EOF

# 4. Enable site
ln -s /etc/nginx/sites-available/llmsync /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 5. Auto-renew SSL
echo "0 0 1 * * certbot renew --quiet" | crontab -

# ✓ HTTPS enabled!
```

---

## 💾 Setup Automated Backups

```bash
# 1. Make backup script executable
chmod +x backup.sh

# 2. Create backup directory
mkdir -p /backups/llmsync

# 3. Test backup
BACKUP_DIR=/backups/llmsync ./backup.sh

# 4. Schedule daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * cd /path/to/llmsync && BACKUP_DIR=/backups/llmsync ./backup.sh >> /var/log/llmsync-backup.log 2>&1

# ✓ Backups automated!
```

---

## 📊 Setup Monitoring (Optional but Recommended)

### Option 1: Simple Health Check Monitor

```bash
# Install monitoring script
cat > /usr/local/bin/llmsync-monitor.sh << 'EOF'
#!/bin/bash
API_URL="http://localhost:8000"

HEALTH=$(curl -s "$API_URL/api/health/full")
STATUS=$(echo "$HEALTH" | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "ALERT: LLMSync unhealthy at $(date)"
    echo "$HEALTH"
    # Send alert (email, Slack, etc.)
fi
EOF

chmod +x /usr/local/bin/llmsync-monitor.sh

# Run every 5 minutes
echo "*/5 * * * * /usr/local/bin/llmsync-monitor.sh" | crontab -
```

### Option 2: Uptime Robot (Free)

1. Go to https://uptimerobot.com
2. Add monitor: `https://yourdomain.com/api/health`
3. Get alerted if down

---

## 🎯 Production Checklist

Before going live:

### Security
- [ ] Changed SECRET_KEY in .env
- [ ] Changed all database passwords
- [ ] HTTPS/TLS enabled
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] CORS origins restricted to your domain
- [ ] Rate limiting enabled (already done ✓)

### Operational
- [ ] Automated backups configured
- [ ] Monitoring/alerts set up
- [ ] Logs being collected
- [ ] Disk space sufficient (20GB+ recommended)

### Testing
- [ ] Health check passes: `curl https://yourdomain.com/api/health/full`
- [ ] Can request magic link
- [ ] Can authenticate
- [ ] Can create thread
- [ ] Can send message
- [ ] WebSocket works
- [ ] File upload works

---

## 📱 Test Your Deployment

```bash
# Set your domain
DOMAIN="https://yourdomain.com"

# 1. Health check
curl "$DOMAIN/api/health/full" | jq

# Expected: All services "healthy"

# 2. Request magic link
curl -X POST "$DOMAIN/api/auth/login/magic-link" \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}' | jq

# 3. Check logs for magic link
docker-compose logs api | grep "Magic link"

# 4. Test WebSocket (requires wscat)
wscat -c "wss://yourdomain.com/api/sync/ws?token=YOUR_TOKEN"

# ✓ All working!
```

---

## 🔥 Troubleshooting

### Services won't start
```bash
# Check Docker logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

### Can't reach API
```bash
# Check nginx
systemctl status nginx
nginx -t

# Check firewall
ufw status
ufw allow 80/tcp
ufw allow 443/tcp
```

### Database errors
```bash
# Check Postgres
docker exec llmsync-postgres pg_isready

# View Postgres logs
docker-compose logs postgres

# Reset database (⚠️ data loss)
docker-compose down -v
docker-compose up -d
```

---

## 📦 Prepare for PyPI (Coming Soon)

### Package llmsync-server

```bash
# 1. Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="llmsync-server",
    version="0.1.0",
    description="LLMSync - E2E encrypted conversation sync server",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="LLMSync Contributors",
    url="https://github.com/yourusername/llmsync",
    packages=find_packages("backend"),
    package_dir={"": "backend"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy[asyncio]>=2.0.25",
        "asyncpg>=0.29.0",
        "alembic>=1.13.1",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "redis[hiredis]>=5.0.1",
        "PyNaCl>=1.5.0",
        "cryptography>=42.0.0",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
        "aiosmtplib>=3.0.1",
        "minio>=7.2.3",
        "slowapi>=0.1.9",
        "python-json-logger>=2.0.7",
    ],
    entry_points={
        "console_scripts": [
            "llmsync=llmsync.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
EOF

# 2. Build
python -m build

# 3. Test locally
pip install dist/*.whl
llmsync --version

# 4. Upload to PyPI
twine upload dist/*

# ✓ Now anyone can: pip install llmsync-server
```

---

## 🌟 What's Next

After deployment:

### Week 1
1. ✅ Monitor logs for errors
2. ✅ Get feedback from first users
3. ✅ Optimize based on usage patterns

### Week 2
4. Build Python SDK (12 hours)
5. Build MCP server (12 hours)
6. Load test your instance

### Week 3
7. Build TypeScript SDK (16 hours)
8. Write comprehensive tests
9. Document common patterns

### Month 2
10. Build admin dashboard
11. Add more OAuth providers
12. Scale based on demand

---

## 💰 Estimated Costs

### Small Deployment (1,000 users)
- **DigitalOcean Droplet** (4GB): $24/month
- **Managed Postgres**: $15/month
- **Managed Redis**: $10/month
- **Object Storage (100GB)**: $5/month
- **SSL Certificate**: Free (Let's Encrypt)
- **Total: ~$54/month**

### Medium Deployment (10,000 users)
- **Load Balancer**: $12/month
- **3x Droplets** (4GB each): $72/month
- **Managed Postgres (HA)**: $55/month
- **Redis Cluster**: $40/month
- **Object Storage (1TB)**: $20/month
- **Total: ~$199/month**

### Large Deployment (100,000 users)
- **Kubernetes Cluster**: $200/month
- **Database (High Availability)**: $300/month
- **Redis Cluster**: $150/month
- **CDN + Storage**: $200/month
- **Total: ~$850/month**

---

## ✅ Deployment Complete!

You now have:
- ✅ Production LLMSync instance running
- ✅ HTTPS/TLS secured
- ✅ Automated backups
- ✅ Monitoring in place
- ✅ Ready for real users

**Your API is at:** `https://yourdomain.com`

**Test it:**
```bash
curl https://yourdomain.com/api/health/full
```

---

## 📞 Support

- **Issues:** GitHub Issues
- **Documentation:** See all *.md files in project
- **Community:** Coming soon

---

## 🎉 Congratulations!

You've deployed a production-ready E2E encrypted conversation sync service!

**Share your deployment:**
- Tweet: "Just deployed @LLMSync for encrypted LLM conversation sync!"
- Blog: Write about your experience
- Contribute: Send PRs for improvements

**Next:** Build the SDKs and start syncing conversations! 🚀
