# Irrigación Malargüe - Production Deployment Guide

## 🏗️ Architecture Overview

```
Internet
    ↓
Cloudflare (SSL/TLS Termination)
    ↓
Cloudflare Tunnel (Zero Trust)
    ↓
Linux Home Server (localhost:8002)
    ↓
Docker: irrigacion_malargue_app (port 8000)
    ↓
Shared Network: db_central (PostgreSQL)
```

## 📋 Prerequisites

1. **Docker & Docker Compose** installed on Linux server
2. **Cloudflare Tunnel** configured to forward to `localhost:8002`
3. **Shared PostgreSQL** container `db_central` running
4. **Shared Docker Network** `shared_network` created
5. **Domain**: `irrigacionmalargue.net` configured in Cloudflare

## 🚀 Deployment Steps

### 1. Prepare Environment

```bash
# Clone or upload project to server
cd /path/to/project

# Copy and configure environment variables
cp env.production.example .env
nano .env
```

### 2. Configure .env

```env
# Critical settings for production
DEBUG=False
SECRET_KEY=your-super-secret-key-min-50-chars
ALLOWED_HOSTS=irrigacionmalargue.net,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://irrigacionmalargue.net

# Database (Shared PostgreSQL: db_central)
DB_NAME=irrigacion_malargue_db
DB_USER=irrigacion_user
DB_PASSWORD=your-db-password
DATABASE_URL=postgresql://irrigacion_user:your-db-password@db_central:5432/irrigacion_malargue_db

# Redis (Optional)
REDIS_URL=redis://redis_central:6379/1
```

### 3. Create Database in db_central

```bash
# Connect to shared PostgreSQL container
docker exec -it db_central psql -U postgres

# Create database and user
CREATE DATABASE irrigacion_malargue_db;
CREATE USER irrigacion_user WITH PASSWORD 'your-db-password';
GRANT ALL PRIVILEGES ON DATABASE irrigacion_malargue_db TO irrigacion_user;
\q
```

### 4. Deploy Application

```bash
# Make deploy script executable
chmod +x deploy-production.sh

# Run deployment
./deploy-production.sh
```

## 🔧 Manual Deployment (Alternative)

```bash
# 1. Create shared network (if not exists)
docker network create shared_network

# 2. Build image
docker-compose build --no-cache

# 3. Start containers
docker-compose up -d

# 4. Run migrations
docker exec irrigacion_malargue_app python manage.py migrate --noinput

# 5. Collect static files
docker exec irrigacion_malargue_app python manage.py collectstatic --noinput

# 6. Create superuser (first time only)
docker exec -it irrigacion_malargue_app python manage.py createsuperuser
```

## 🛠️ Common Commands

```bash
# View logs
docker logs -f irrigacion_malargue_app

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Shell access
docker exec -it irrigacion_malargue_app /bin/bash

# Django shell
docker exec -it irrigacion_malargue_app python manage.py shell

# Create superuser
docker exec -it irrigacion_malargue_app python manage.py createsuperuser
```

## 🔐 Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` (min 50 chars)
- [ ] Database password is strong
- [ ] `.env` file is NOT in version control
- [ ] `ALLOWED_HOSTS` includes only your domain
- [ ] `CSRF_TRUSTED_ORIGINS` matches your domain
- [ ] SSL handled by Cloudflare
- [ ] Container runs as non-root user

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8002/health/
# Should return: {"status": "healthy", ...}
```

### Container Health

```bash
docker inspect --format='{{.State.Health.Status}}' irrigacion_malargue_app
# Should return: healthy
```

### Logs Location

- Gunicorn Access: `/var/log/malargue/gunicorn_access.log`
- Gunicorn Error: `/var/log/malargue/gunicorn_error.log`
- Django: `/var/log/malargue/django.log`

## 🔄 Updates

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and restart
./deploy-production.sh

# 3. Check logs
docker logs -f irrigacion_malargue_app
```

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker logs irrigacion_malargue_app

# Check if db_central is running
docker ps | grep db_central

# Verify shared network
docker network inspect shared_network
```

### Database connection error

```bash
# Test connection to db_central
docker exec -it irrigacion_malargue_app psql -h db_central -U irrigacion_user -d irrigacion_malargue_db

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Static files not loading

```bash
# Recollect static files
docker exec irrigacion_malargue_app python manage.py collectstatic --noinput

# Check WhiteNoise is in MIDDLEWARE (config/settings.py)
```

### Cloudflare Tunnel not working

```bash
# Verify app is listening on 8002
netstat -tlnp | grep 8002

# Check Cloudflare Tunnel config
# Tunnel should point to: localhost:8002
```

## 📝 Notes

- **No Nginx**: Static files served by WhiteNoise
- **SSL**: Handled by Cloudflare (app receives HTTP)
- **Port Mapping**: Container 8000 → Host 8002
- **Database**: Shared `db_central` on `shared_network`
- **Logs**: Mounted to `./logs/` directory

## 📞 Support

For issues, check:
1. Container logs: `docker logs irrigacion_malargue_app`
2. Database connectivity
3. Cloudflare Tunnel status
4. Firewall rules (if any)
