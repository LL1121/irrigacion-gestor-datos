# ==============================================================
# DEPLOYMENT SIMPLE - Sin Nginx (WhiteNoise + Cloudflare)
# ==============================================================
# Guía para deployment usando solo Gunicorn + WhiteNoise
# Ideal cuando usás Cloudflare como CDN/Proxy
# ==============================================================

## 🎯 Stack de Producción

```
Usuario → Cloudflare (CDN) → Gunicorn (puerto 80/443) → Django + WhiteNoise
                                    ↓
                              PostgreSQL + Redis
```

---

## 📋 Pre-requisitos

- Servidor Ubuntu 20.04+ / Debian 11+
- Dominio en Cloudflare
- Acceso SSH root o sudo
- PostgreSQL 12+
- Redis 6+
- Python 3.9+

---

## 🚀 Deployment Paso a Paso

### 1. Preparar el servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    redis-server \
    git \
    supervisor
```

### 2. Crear usuario de aplicación

```bash
sudo useradd -m -s /bin/bash malargue
sudo usermod -aG sudo malargue
sudo su - malargue
```

### 3. Subir código al servidor

```bash
# Opción A: Git
git clone https://github.com/tu-usuario/IrrigacionPetroleras.git
cd IrrigacionPetroleras

# Opción B: rsync desde local
# rsync -avz --exclude 'venv' IrrigacionPetroleras/ malargue@servidor:~/IrrigacionPetroleras/
```

### 4. Configurar virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE malargue_db;
CREATE USER malargue_user WITH PASSWORD 'TuPasswordSeguro123!';
ALTER ROLE malargue_user SET client_encoding TO 'utf8';
ALTER ROLE malargue_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE malargue_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE malargue_db TO malargue_user;
\q
```

### 6. Configurar Redis

```bash
sudo nano /etc/redis/redis.conf
```

Descomentar y configurar:
```
requirepass TuRedisPasswordAqui
```

Reiniciar:
```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 7. Crear .env de producción

```bash
cd ~/IrrigacionPetroleras
nano .env
```

Configurar con estos valores:
```env
DEBUG=False
SECRET_KEY=<generar-con-python-manage.py-shell>
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

DATABASE_URL=postgresql://malargue_user:TuPasswordSeguro123!@localhost:5432/malargue_db
REDIS_URL=redis://:TuRedisPasswordAqui@127.0.0.1:6379/1

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Sentry (opcional)
# SENTRY_DSN=https://tu-sentry-dsn
```

**Nota:** `SECURE_SSL_REDIRECT=False` porque Cloudflare maneja SSL

### 8. Ejecutar migraciones y collectstatic

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 9. Crear directorios de logs

```bash
sudo mkdir -p /var/log/malargue
sudo chown -R malargue:malargue /var/log/malargue
mkdir -p ~/IrrigacionPetroleras/logs
```

### 10. Configurar systemd service (SIN Nginx)

```bash
sudo nano /etc/systemd/system/malargue.service
```

Contenido:
```ini
[Unit]
Description=Malargüe DB Django Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=malargue
Group=malargue
WorkingDirectory=/home/malargue/IrrigacionPetroleras
Environment="PATH=/home/malargue/IrrigacionPetroleras/venv/bin"

# Gunicorn escuchando en puerto 80 (requiere permisos)
ExecStart=/home/malargue/IrrigacionPetroleras/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 60 \
    --max-requests 1000 \
    --access-logfile /var/log/malargue/access.log \
    --error-logfile /var/log/malargue/error.log \
    --log-level info \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable malargue
sudo systemctl start malargue
sudo systemctl status malargue
```

### 11. Configurar Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # Gunicorn
sudo ufw enable
```

### 12. Configurar Cloudflare

En el panel de Cloudflare:

**DNS:**
- Tipo: `A`
- Name: `@` (tu dominio)
- Content: `IP-de-tu-servidor`
- Proxy: ✅ Activado (nube naranja)

- Tipo: `A`
- Name: `www`
- Content: `IP-de-tu-servidor`
- Proxy: ✅ Activado (nube naranja)

**SSL/TLS:**
- Modo: **"Full"** (no strict, porque no tenés certificado local)
- Always Use HTTPS: ✅ Activado

**Speed:**
- Auto Minify: CSS, JS, HTML ✅
- Brotli: ✅
- Rocket Loader: ✅ (opcional)

**Caching:**
- Caching Level: Standard
- Browser Cache TTL: 4 hours

**Page Rules** (opcional):
```
*tu-dominio.com/static/*
Cache Level: Cache Everything
Edge Cache TTL: 1 month
```

```
*tu-dominio.com/media/*
Cache Level: Cache Everything
Edge Cache TTL: 1 week
```

### 13. Configurar Gunicorn para puerto 80 (opcional)

Si querés que Gunicorn escuche en puerto 80 directamente:

```bash
# Permitir a Python bindear puertos < 1024
sudo setcap 'cap_net_bind_service=+ep' /home/malargue/IrrigacionPetroleras/venv/bin/python3
```

Actualizar service:
```ini
ExecStart=... --bind 0.0.0.0:80 ...
```

O usar puerto 8000 y configurar port forwarding:
```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8000
```

---

## ✅ Verificación

### Health Check
```bash
curl http://localhost:8000/health/
# Debe retornar: {"status": "healthy", ...}
```

### Desde Cloudflare
```bash
curl https://tu-dominio.com/health/
```

### Ver logs
```bash
# Systemd
sudo journalctl -u malargue -f

# Gunicorn
tail -f /var/log/malargue/error.log

# Django
tail -f ~/IrrigacionPetroleras/logs/django.log
```

---

## 🔄 Actualizar código

```bash
ssh malargue@servidor
cd ~/IrrigacionPetroleras
git pull  # o rsync desde local

source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart malargue
```

---

## 🐛 Troubleshooting

### Gunicorn no inicia
```bash
# Ver logs
sudo journalctl -u malargue -n 50

# Test manual
cd ~/IrrigacionPetroleras
source venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Static files no cargan
```bash
# Verificar collectstatic
python manage.py collectstatic --noinput

# Verificar WhiteNoise en logs
tail -f /var/log/malargue/error.log | grep -i whitenoise
```

### Cloudflare muestra error 522
- Verificar que Gunicorn esté corriendo: `sudo systemctl status malargue`
- Verificar firewall: `sudo ufw status`
- Verificar que el puerto esté abierto: `netstat -tulpn | grep 8000`

### Media files no cargan
WhiteNoise solo sirve static files. Para media files necesitás configurar en `config/urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... tus URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En producción, Gunicorn no debería servir media
    # Usar S3, Cloudinary, o configurar nginx solo para /media/
    pass
```

**Mejor opción:** Usar Cloudflare R2 o AWS S3 para media files en producción.

---

## 📊 Ventajas de este setup

✅ **Simplicidad**: Sin configurar Nginx  
✅ **Cloudflare cache**: Static files ultra rápidos  
✅ **WhiteNoise**: Compresión automática (Gzip + Brotli)  
✅ **Menos servidor**: Solo Gunicorn + WhiteNoise  
✅ **Auto-restart**: Systemd maneja crashes  
✅ **SSL gratis**: Cloudflare maneja certificados  

---

## ⚠️ Limitaciones

- Media files: Deberías usar CDN externo (R2, S3) para uploads grandes
- Sin rate limiting avanzado: Cloudflare lo maneja
- Sin proxy cache local: Cloudflare lo hace a nivel global

Para proyectos grandes con mucho tráfico de media files, considerá agregar Nginx.

---

## 🚀 Comandos útiles

```bash
# Ver status
sudo systemctl status malargue

# Restart
sudo systemctl restart malargue

# Ver logs en tiempo real
sudo journalctl -u malargue -f

# Health check
curl http://localhost:8000/health/

# Backup
python manage.py backup_data --output backups/$(date +%Y-%m-%d)

# Django shell
python manage.py shell
```

---

**¡Tu app está lista para producción con WhiteNoise + Cloudflare!** 🎉
