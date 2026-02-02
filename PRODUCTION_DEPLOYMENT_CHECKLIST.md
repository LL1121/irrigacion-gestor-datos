# 🚀 Production Deployment Checklist - Malargüe DB

**Fecha de análisis:** 2 de Febrero 2026  
**Estado actual:** PostgreSQL configurado, seguridad básica implementada

---

## ✅ Completado (Ya tenés esto)

### Base de Datos
- [x] PostgreSQL configurado y migraciones ejecutadas
- [x] Environment variables con `python-decouple`
- [x] Backup command (`python manage.py backup_data`)

### Seguridad
- [x] `SECRET_KEY` en variable de entorno
- [x] `DEBUG=False` configurable
- [x] HTTPS settings (SSL_REDIRECT, SECURE_COOKIES, HSTS)
- [x] Rate limiting en login (5/min) y uploads (10/min)
- [x] `@login_required` en todas las vistas protegidas
- [x] CSRF protection habilitado

### Logging & Monitoring
- [x] RotatingFileHandler (10MB, 5 backups)
- [x] Sentry integration para error tracking
- [x] Logging en vistas críticas (cargar_medicion, exportar_csv)

### Caching
- [x] Redis configurado para cache
- [x] `@cache_page` en weekly_route

### Testing
- [x] Tests unitarios (models, views, utils)
- [x] pytest configurado
- [x] Coverage tool instalado

---

## ⚠️ CRÍTICO - Falta implementar

### 1. Archivos Estáticos (STATIC_ROOT)
**Problema:** En producción, Django NO sirve archivos estáticos automáticamente.

**Solución:**
```python
# config/settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Agregar esta línea
```

**Comando a ejecutar antes del deploy:**
```bash
python manage.py collectstatic --noinput
```

**Riesgo:** CSS/JS/imágenes no cargarán en producción ❌

---

### 2. Servidor WSGI (Gunicorn)
**Problema:** `runserver` es solo para desarrollo.

**Solución:**
```bash
pip install gunicorn
```

**Agregar a requirements.txt:**
```
gunicorn==21.2.0
```

**Comando de producción:**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 60
```

**Riesgo:** Performance pobre, crashes, no soporta concurrencia ❌

---

### 3. Servidor Web (Nginx)
**Problema:** Gunicorn solo maneja Python, no sirve archivos estáticos eficientemente.

**Crear:** `nginx.conf`
```nginx
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name tu-dominio.com;

    # Archivos estáticos
    location /static/ {
        alias /path/to/IrrigacionPetroleras/staticfiles/;
        expires 30d;
    }

    # Archivos media (uploads)
    location /media/ {
        alias /path/to/IrrigacionPetroleras/media/;
        expires 30d;
    }

    # Proxy a Django
    location / {
        proxy_pass http://django_app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
        client_max_body_size 20M;  # Para uploads de fotos
    }
}
```

**Riesgo:** Sin nginx, performance limitada y sin servir static/media correctamente ❌

---

### 4. Systemd Service (Auto-restart)
**Problema:** Si el servidor se reinicia, Django no arranca automáticamente.

**Crear:** `/etc/systemd/system/malargue.service`
```ini
[Unit]
Description=Malargue DB Django Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/IrrigacionPetroleras
Environment="PATH=/path/to/IrrigacionPetroleras/venv/bin"
ExecStart=/path/to/IrrigacionPetroleras/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/malargue/access.log \
    --error-logfile /var/log/malargue/error.log \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable malargue
sudo systemctl start malargue
```

**Riesgo:** App no se reinicia automáticamente después de crashes o reboots ❌

---

### 5. SSL/HTTPS con Let's Encrypt
**Problema:** Datos viajando sin encriptar (passwords, GPS, fotos).

**Solución:**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

**Actualizar nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    # ... resto de la config
}
```

**Riesgo:** Datos sensibles viajando en texto plano ❌

---

### 6. Health Check Endpoint
**Problema:** No hay forma de verificar si la app está funcionando (para load balancers, monitoring).

**Agregar en web/views.py:**
```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint para monitoring"""
    try:
        # Verificar DB
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

**Agregar en web/urls.py:**
```python
path('health/', views.health_check, name='health_check'),
```

**Riesgo:** No podés monitorear si la app está caída ⚠️

---

### 7. Email Backend Configuration
**Problema:** No hay forma de enviar notificaciones (reseteo de passwords, alertas).

**Agregar a settings.py:**
```python
# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@malargue.com')
```

**Riesgo:** No podés enviar emails automáticos ⚠️

---

### 8. Backups Automáticos (Cron Job)
**Problema:** Tenés el comando pero no se ejecuta automáticamente.

**Crear script:** `backup.sh`
```bash
#!/bin/bash
cd /path/to/IrrigacionPetroleras
source venv/bin/activate
python manage.py backup_data --output /backups/$(date +\%Y-\%m-\%d)
# Upload a S3/cloud storage
aws s3 cp /backups/ s3://malargue-backups/ --recursive
```

**Agregar a crontab:**
```bash
# Backup diario a las 2 AM
0 2 * * * /path/to/IrrigacionPetroleras/backup.sh
```

**Riesgo:** Sin backups automáticos, podés perder datos ❌

---

### 9. Environment Variables de Producción
**Problema:** Tu `.env` actual tiene valores de desarrollo.

**Crear `.env.production` template:**
```bash
# Production Environment Variables

# Django Core
DEBUG=False
SECRET_KEY=<generar-con-django-get-secret-key>
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Database
DATABASE_URL=postgresql://malargue_user:STRONG_PASSWORD@localhost:5432/malargue_db

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Sentry
SENTRY_DSN=https://tu-sentry-dsn-aqui

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=notificaciones@malargue.com
```

**Riesgo:** Configuraciones incorrectas en producción ❌

---

### 10. DEFAULT_AUTO_FIELD
**Advertencia Django:** Falta especificar el tipo de campo para PKs.

**Agregar a settings.py:**
```python
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

**Riesgo:** Warnings molestos en logs ⚠️

---

### 11. Middleware WhiteNoise (Alternativa a Nginx para static)
**Si no querés usar Nginx:**

```bash
pip install whitenoise
```

**Actualizar settings.py:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Agregar después de SecurityMiddleware
    # ... resto
]

# Static files con compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Riesgo:** Performance menor que nginx pero más fácil de configurar ⚠️

---

### 12. Max Upload Size & Timeout Settings
**Problema:** Fotos grandes podrían fallar.

**Agregar a settings.py:**
```python
# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
```

**En Nginx:**
```nginx
client_max_body_size 20M;
```

**Riesgo:** Uploads grandes fallan sin mensajes claros ⚠️

---

### 13. Logs Directory Permissions
**Problema:** La carpeta `logs/` debe tener permisos correctos.

**Comandos:**
```bash
mkdir -p /path/to/IrrigacionPetroleras/logs
chmod 755 /path/to/IrrigacionPetroleras/logs
chown www-data:www-data /path/to/IrrigacionPetroleras/logs
```

**Riesgo:** Logs no se escriben y debugging imposible ❌

---

### 14. Media Files Backup
**Problema:** Tu backup actual solo cubre DB, pero las fotos también son críticas.

**Actualizar backup_data.py** para incluir compresión de media:
```python
# Ya está implementado parcialmente, verificar que funcione
```

**Riesgo:** Pérdida de evidencias fotográficas ❌

---

### 15. Database Connection Pooling
**Problema:** Cada request abre/cierra conexión DB (ineficiente).

**Instalar:**
```bash
pip install psycopg2-pool
```

**Agregar a settings.py:**
```python
DATABASES = {
    'default': {
        **dj_database_url.config(
            default=config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
        ),
        'CONN_MAX_AGE': 600,  # 10 minutos de persistent connections
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

**Riesgo:** Performance degradada bajo carga ⚠️

---

### 16. Redis Password Protection
**Problema:** Redis sin password en producción.

**Configurar Redis:**
```bash
# /etc/redis/redis.conf
requirepass TU_PASSWORD_SEGURO
```

**Actualizar .env:**
```bash
REDIS_URL=redis://:TU_PASSWORD@127.0.0.1:6379/1
```

**Riesgo:** Redis expuesto a acceso no autorizado ⚠️

---

## 📋 Prioridad de Implementación

### AHORA (antes de deploy):
1. ✅ STATIC_ROOT + collectstatic
2. ✅ Gunicorn instalado
3. ✅ Health check endpoint
4. ✅ DEFAULT_AUTO_FIELD
5. ✅ Environment variables de producción

### SEMANA 1:
6. Nginx configuration
7. Systemd service
8. SSL/HTTPS con Let's Encrypt
9. Database connection pooling
10. Logs directory permissions

### SEMANA 2:
11. Backups automáticos (cron)
12. Redis password
13. Email backend
14. Max upload size settings
15. WhiteNoise (si no usás Nginx)

### OPCIONAL (mejoras):
16. Monitoring adicional (New Relic, Datadog)
17. CDN para archivos estáticos
18. Load balancer (si escalás)
19. Docker containers
20. CI/CD pipeline

---

## 🛠️ Comandos Rápidos de Deployment

### Pre-deploy Checklist:
```bash
# 1. Actualizar .env con valores de producción
cp .env.production .env

# 2. Instalar dependencias
pip install -r requirements.txt
pip install gunicorn

# 3. Collectstatic
python manage.py collectstatic --noinput

# 4. Migraciones
python manage.py migrate

# 5. Crear superusuario (si hace falta)
python manage.py createsuperuser

# 6. Tests
pytest

# 7. Check de seguridad
python manage.py check --deploy
```

### Start Production Server:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 60 --daemon
```

---

## 📊 Resumen de Riesgos

| Item | Riesgo | Impacto | Urgencia |
|------|--------|---------|----------|
| STATIC_ROOT | ❌ Alto | App no funciona | CRÍTICO |
| Gunicorn | ❌ Alto | Performance pobre | CRÍTICO |
| Health Check | ⚠️ Medio | No monitoring | ALTA |
| Nginx | ⚠️ Medio | Performance | ALTA |
| SSL/HTTPS | ❌ Alto | Seguridad | CRÍTICO |
| Backups Auto | ❌ Alto | Pérdida datos | ALTA |
| Systemd | ⚠️ Medio | Downtime | MEDIA |
| Email | ⚠️ Bajo | Sin notificaciones | BAJA |
| Redis Pass | ⚠️ Medio | Seguridad | MEDIA |
| Logs Perms | ⚠️ Medio | No debugging | MEDIA |

---

## ✅ Conclusión

**Estado actual:** 60% listo para producción  
**Faltan:** 10 items críticos/importantes  
**Tiempo estimado:** 2-3 días de trabajo

**Próximos pasos:**
1. Implementar items CRÍTICOS (1-5)
2. Configurar servidor (Nginx + Systemd)
3. SSL/HTTPS
4. Testing en ambiente staging
5. Deploy a producción

---

**Última actualización:** 2 de Febrero 2026
