# Production Configuration Summary - Irrigación Malargüe

## ✅ Files Configured

### Core Configuration
- [x] `config/settings.py` - Updated for Cloudflare Tunnel + shared PostgreSQL
- [x] `docker-compose.yml` - Configured for shared_network + db_central
- [x] `Dockerfile` - Multi-stage build with Python 3.10-slim
- [x] `gunicorn.conf.py` - Production-ready Gunicorn config
- [x] `.dockerignore` - Optimized build context

### Environment & Deployment
- [x] `env.production.example` - Template with all required variables
- [x] `deploy-production.sh` - Automated deployment script
- [x] `DEPLOYMENT.md` - Complete deployment guide

## 🎯 Key Configuration Points

### 1. Networking
```yaml
# Docker Compose
networks:
  shared_network:
    external: true
    name: shared_network

ports:
  - "8002:8000"  # Cloudflare Tunnel → localhost:8002
```

### 2. Database
```python
# settings.py
DATABASE_URL=postgresql://user:pass@db_central:5432/irrigacion_malargue_db
```

### 3. Security
```python
# settings.py
SECURE_SSL_REDIRECT = False  # SSL handled by Cloudflare
CSRF_TRUSTED_ORIGINS = ['https://irrigacionmalargue.net']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 4. Static Files
```python
# settings.py (WhiteNoise - No Nginx needed)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## 📦 Required Environment Variables

```env
# Critical
DEBUG=False
SECRET_KEY=<50+ character random string>
ALLOWED_HOSTS=irrigacionmalargue.net,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://irrigacionmalargue.net

# Database (db_central)
DB_NAME=irrigacion_malargue_db
DB_USER=irrigacion_user
DB_PASSWORD=<strong-password>
DATABASE_URL=postgresql://irrigacion_user:<password>@db_central:5432/irrigacion_malargue_db

# Optional
REDIS_URL=redis://redis_central:6379/1
SENTRY_DSN=<optional-sentry-dsn>
```

## 🚀 Quick Start

1. **Prepare Environment**
   ```bash
   cp env.production.example .env
   nano .env  # Fill in values
   ```

2. **Create Database in db_central**
   ```sql
   CREATE DATABASE irrigacion_malargue_db;
   CREATE USER irrigacion_user WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE irrigacion_malargue_db TO irrigacion_user;
   ```

3. **Deploy**
   ```bash
   chmod +x deploy-production.sh
   ./deploy-production.sh
   ```

4. **Create Superuser**
   ```bash
   docker exec -it irrigacion_malargue_app python manage.py createsuperuser
   ```

## 🔍 Verification

```bash
# Check container
docker ps | grep irrigacion_malargue_app

# Check health
curl http://localhost:8002/health/

# View logs
docker logs -f irrigacion_malargue_app

# Test database connection
docker exec -it irrigacion_malargue_app python manage.py check --database default
```

## 📊 Architecture Flow

```
User Request
    ↓
https://irrigacionmalargue.net (Cloudflare SSL)
    ↓
Cloudflare Tunnel (Zero Trust)
    ↓
Linux Server - localhost:8002
    ↓
Docker: irrigacion_malargue_app (port 8000)
    ├→ WhiteNoise (serves static files)
    ├→ Gunicorn (WSGI server)
    └→ Django Application
        ├→ PostgreSQL (db_central:5432)
        └→ Redis (redis_central:6379) [optional]
```

## ⚠️ Important Notes

1. **No Nginx**: WhiteNoise handles static files
2. **No open ports**: Cloudflare Tunnel handles external access
3. **Shared database**: Uses existing `db_central` container
4. **SSL at Cloudflare**: App receives HTTP traffic
5. **Port 8002**: Mapped for Cloudflare Tunnel access

## 📝 Post-Deployment

- [ ] Configure Cloudflare Tunnel to localhost:8002
- [ ] Create Django superuser
- [ ] Test admin panel: https://irrigacionmalargue.net/admin/
- [ ] Verify file uploads work (media folder)
- [ ] Check logs are being written
- [ ] Monitor container health

## 🐛 Troubleshooting

See `DEPLOYMENT.md` for detailed troubleshooting guide.

Common issues:
- Container won't start → Check `docker logs`
- Database errors → Verify db_central is running
- Static files 404 → Run `collectstatic`
- CSRF errors → Check CSRF_TRUSTED_ORIGINS

## 📞 Next Steps

1. Deploy to server using `deploy-production.sh`
2. Configure Cloudflare Tunnel
3. Create superuser and test admin
4. Set up monitoring (optional: Sentry)
5. Configure backups for database and media files
