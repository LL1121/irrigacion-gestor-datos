# ==============================================================
# DEPLOYMENT GUIDE - Malargüe DB
# ==============================================================
# Guía paso a paso para desplegar en producción
# ==============================================================

## 📋 Pre-requisitos

- Servidor Ubuntu 20.04+ / Debian 11+
- Dominio apuntando al servidor (o Cloudflare configurado)
- Acceso SSH root o sudo
- PostgreSQL 12+
- Redis 6+
- Python 3.9+

---

## 🎯 Dos opciones de deployment:

### Opción 1: WhiteNoise + Cloudflare (RECOMENDADO - MÁS SIMPLE)
✅ Sin Nginx  
✅ Ideal con Cloudflare como CDN  
✅ Setup en 20 minutos  
✅ Menos servidores que mantener  

👉 **[Ver guía: DEPLOYMENT_SIMPLE.md](DEPLOYMENT_SIMPLE.md)**

---

### Opción 2: Nginx + Gunicorn (TRADICIONAL)
✅ Máximo performance para static/media files  
✅ Control granular de proxy/cache  
✅ Ideal sin CDN externo  

👉 **Continuar leyendo esta guía**

---

## 🚀 Deployment Rápido (Automated)

### 1. Subir archivos al servidor
```bash
# Desde tu máquina local
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  /path/to/IrrigacionPetroleras/ user@tu-servidor:/home/malargue/IrrigacionPetroleras/
```

### 2. Ejecutar setup automático
```bash
# En el servidor
cd /home/malargue/IrrigacionPetroleras
sudo bash server_setup.sh
```

### 3. Configurar como usuario malargue
```bash
su - malargue
cd IrrigacionPetroleras
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configurar .env
```bash
cp .env.example .env
nano .env  # Editar con valores de producción
```

### 5. Migrations y static
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Iniciar servicio
```bash
sudo systemctl start malargue
sudo systemctl enable malargue
```

---

## 🔧 Deployment Manual (Paso a Paso)

### 1. Preparar el servidor

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql \
  postgresql-contrib libpq-dev redis-server nginx git
```

### 2. Crear usuario de aplicación

```bash
sudo useradd -m -s /bin/bash malargue
sudo usermod -aG www-data malargue
sudo su - malargue
```

### 3. Clonar o subir código

```bash
# Opción A: Git
cd ~
git clone https://github.com/tu-usuario/IrrigacionPetroleras.git

# Opción B: rsync (desde tu máquina)
rsync -avz --exclude 'venv' IrrigacionPetroleras/ user@servidor:/home/malargue/IrrigacionPetroleras/
```

### 4. Configurar virtual environment

```bash
cd ~/IrrigacionPetroleras
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
CREATE USER malargue_user WITH PASSWORD 'SuperSecurePassword123!';
ALTER ROLE malargue_user SET client_encoding TO 'utf8';
ALTER ROLE malargue_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE malargue_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE malargue_db TO malargue_user;
\q
```

### 6. Configurar Redis con password

```bash
sudo nano /etc/redis/redis.conf
```

Buscar y descomentar:
```
requirepass YourRedisPasswordHere
```

Reiniciar:
```bash
sudo systemctl restart redis-server
```

### 7. Crear .env de producción

```bash
cd ~/IrrigacionPetroleras
cp .env.example .env
nano .env
```

Configurar:
```bash
DEBUG=False
SECRET_KEY=<generar-con-django>
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

DATABASE_URL=postgresql://malargue_user:SuperSecurePassword123!@localhost:5432/malargue_db
REDIS_URL=redis://:YourRedisPasswordHere@127.0.0.1:6379/1

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

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
sudo mkdir -p /var/run/gunicorn
sudo chown -R malargue:www-data /var/log/malargue
sudo chown -R malargue:www-data /var/run/gunicorn
```

### 10. Configurar Gunicorn con systemd

```bash
sudo cp ~/IrrigacionPetroleras/malargue.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable malargue
sudo systemctl start malargue
```

Verificar:
```bash
sudo systemctl status malargue
sudo journalctl -u malargue -f
```

### 11. Configurar Nginx

```bash
sudo cp ~/IrrigacionPetroleras/nginx.conf /etc/nginx/sites-available/malargue
sudo nano /etc/nginx/sites-available/malargue  # Ajustar rutas y dominio
sudo ln -s /etc/nginx/sites-available/malargue /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 12. Configurar SSL con Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

Renovación automática:
```bash
sudo certbot renew --dry-run
```

### 13. Configurar Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## ✅ Verificación

### Health Check
```bash
curl http://localhost:8000/health/
# Debe retornar: {"status": "healthy", "database": "connected", ...}
```

### Verificar Gunicorn
```bash
ps aux | grep gunicorn
sudo systemctl status malargue
```

### Verificar Nginx
```bash
sudo nginx -t
curl -I http://tu-dominio.com
```

### Logs
```bash
# Gunicorn
tail -f /var/log/malargue/gunicorn_error.log

# Systemd
sudo journalctl -u malargue -f

# Nginx
tail -f /var/log/nginx/malargue_error.log
```

---

## 🔄 Actualización de código

```bash
# 1. Conectar al servidor
ssh user@servidor
sudo su - malargue

# 2. Actualizar código
cd ~/IrrigacionPetroleras
git pull  # o rsync desde local

# 3. Activar venv y actualizar deps
source venv/bin/activate
pip install -r requirements.txt

# 4. Migraciones y collectstatic
python manage.py migrate
python manage.py collectstatic --noinput

# 5. Reiniciar servicio
sudo systemctl restart malargue

# 6. Verificar
curl http://localhost:8000/health/
```

---

## 🛑 Troubleshooting

### Gunicorn no inicia
```bash
# Ver logs detallados
sudo journalctl -u malargue -n 50 --no-pager

# Verificar permisos
ls -la /home/malargue/IrrigacionPetroleras

# Test manual
cd /home/malargue/IrrigacionPetroleras
source venv/bin/activate
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

### Nginx 502 Bad Gateway
```bash
# Verificar que Gunicorn esté corriendo
curl http://127.0.0.1:8000/health/

# Ver logs
tail -f /var/log/nginx/malargue_error.log
```

### Static files no cargan
```bash
# Verificar collectstatic
python manage.py collectstatic --noinput

# Verificar permisos
ls -la /home/malargue/IrrigacionPetroleras/staticfiles/

# Verificar nginx config
grep -A5 "location /static/" /etc/nginx/sites-available/malargue
```

### Database connection errors
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Test conexión
psql -U malargue_user -d malargue_db -h localhost

# Ver logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## 📊 Monitoring

### Configurar monitoreo básico
```bash
# Disk usage alert
echo "0 */6 * * * df -h | mail -s 'Disk Usage' admin@tu-dominio.com" | crontab -

# Health check cron
echo "*/5 * * * * curl -fsS http://localhost:8000/health/ > /dev/null || echo 'App down!' | mail -s 'Alert' admin@tu-dominio.com" | crontab -
```

### Instalar herramientas de monitoring (opcional)
- Grafana + Prometheus
- New Relic
- Datadog
- Sentry (ya configurado)

---

## 🔒 Hardening adicional

```bash
# Fail2ban para proteger SSH
sudo apt install fail2ban

# Limitar rate en Nginx (ya configurado en nginx.conf)

# Actualizar regularmente
sudo apt update && sudo apt upgrade

# Backups automáticos
crontab -e
# Agregar: 0 2 * * * /home/malargue/IrrigacionPetroleras/backup.sh
```

---

## 📞 Comandos útiles

```bash
# Restart app
sudo systemctl restart malargue

# Ver logs en tiempo real
sudo journalctl -u malargue -f

# Reload nginx (sin downtime)
sudo systemctl reload nginx

# Backup manual
python manage.py backup_data --output /backups/$(date +%Y-%m-%d)

# Django shell
python manage.py shell

# Ver usuarios
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.all())"
```

---

**¡Listo! Tu aplicación debería estar corriendo en producción.** 🚀
