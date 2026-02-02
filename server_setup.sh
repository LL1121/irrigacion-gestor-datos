#!/bin/bash
# ==============================================================
# Malargüe DB - Server Setup Script
# ==============================================================
# Este script configura el servidor de producción
# Ejecutar con: sudo bash server_setup.sh
# ==============================================================

set -e

echo "🚀 Configurando servidor para Malargüe DB..."

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Variables (AJUSTAR SEGÚN TU SERVIDOR)
APP_USER="malargue"
APP_DIR="/home/$APP_USER/IrrigacionPetroleras"
DOMAIN="tu-dominio.com"

# ----------------------------------------------------------
# 1. Actualizar sistema
# ----------------------------------------------------------
echo "📦 Actualizando sistema..."
apt-get update
apt-get upgrade -y

# ----------------------------------------------------------
# 2. Instalar dependencias
# ----------------------------------------------------------
echo "📦 Instalando dependencias..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    redis-server \
    nginx \
    git \
    supervisor \
    certbot \
    python3-certbot-nginx

# ----------------------------------------------------------
# 3. Crear usuario de aplicación
# ----------------------------------------------------------
echo "👤 Creando usuario $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    usermod -aG www-data "$APP_USER"
    echo "✅ Usuario $APP_USER creado"
else
    echo "ℹ️  Usuario $APP_USER ya existe"
fi

# ----------------------------------------------------------
# 4. Configurar PostgreSQL
# ----------------------------------------------------------
echo "🗄️  Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE malargue_db;" 2>/dev/null || echo "ℹ️  Base de datos ya existe"
sudo -u postgres psql -c "CREATE USER malargue_user WITH PASSWORD 'CAMBIAR_PASSWORD_AQUI';" 2>/dev/null || echo "ℹ️  Usuario ya existe"
sudo -u postgres psql -c "ALTER ROLE malargue_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE malargue_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE malargue_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE malargue_db TO malargue_user;"

# ----------------------------------------------------------
# 5. Configurar Redis
# ----------------------------------------------------------
echo "🔴 Configurando Redis..."
sed -i 's/^# requirepass .*/requirepass CAMBIAR_REDIS_PASSWORD/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# ----------------------------------------------------------
# 6. Crear directorios necesarios
# ----------------------------------------------------------
echo "📁 Creando directorios..."
mkdir -p /var/log/malargue
mkdir -p /var/run/gunicorn
mkdir -p /var/www/certbot

chown -R "$APP_USER:www-data" /var/log/malargue
chown -R "$APP_USER:www-data" /var/run/gunicorn
chmod 755 /var/log/malargue

# ----------------------------------------------------------
# 7. Configurar Nginx
# ----------------------------------------------------------
echo "🌐 Configurando Nginx..."
if [ -f "$APP_DIR/nginx.conf" ]; then
    cp "$APP_DIR/nginx.conf" "/etc/nginx/sites-available/malargue"
    
    # Reemplazar placeholders
    sed -i "s/tu-dominio.com/$DOMAIN/g" /etc/nginx/sites-available/malargue
    sed -i "s|/home/malargue/IrrigacionPetroleras|$APP_DIR|g" /etc/nginx/sites-available/malargue
    
    # Crear symlink
    ln -sf /etc/nginx/sites-available/malargue /etc/nginx/sites-enabled/
    
    # Eliminar default
    rm -f /etc/nginx/sites-enabled/default
    
    # Test y reload
    nginx -t && systemctl reload nginx
    echo "✅ Nginx configurado"
else
    echo "⚠️  nginx.conf no encontrado en $APP_DIR"
fi

# ----------------------------------------------------------
# 8. Configurar Systemd Service
# ----------------------------------------------------------
echo "⚙️  Configurando systemd service..."
if [ -f "$APP_DIR/malargue.service" ]; then
    cp "$APP_DIR/malargue.service" /etc/systemd/system/
    
    # Reemplazar placeholders
    sed -i "s|/home/malargue/IrrigacionPetroleras|$APP_DIR|g" /etc/systemd/system/malargue.service
    
    systemctl daemon-reload
    systemctl enable malargue
    echo "✅ Systemd service configurado (no iniciado aún)"
else
    echo "⚠️  malargue.service no encontrado en $APP_DIR"
fi

# ----------------------------------------------------------
# 9. Configurar SSL con Let's Encrypt
# ----------------------------------------------------------
echo "🔒 ¿Configurar SSL con Let's Encrypt?"
read -p "Configurar SSL ahora? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN"
fi

# ----------------------------------------------------------
# 10. Configurar firewall (UFW)
# ----------------------------------------------------------
echo "🔥 Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo "✅ Firewall configurado"
fi

# ----------------------------------------------------------
# 11. Configurar permisos
# ----------------------------------------------------------
echo "🔐 Configurando permisos..."
chown -R "$APP_USER:www-data" "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod -R 775 "$APP_DIR/media"
chmod -R 775 "$APP_DIR/logs"

# ----------------------------------------------------------
# Resumen
# ----------------------------------------------------------
echo ""
echo "=============================================="
echo "✅ Configuración del servidor completada"
echo "=============================================="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Como usuario $APP_USER:"
echo "   su - $APP_USER"
echo "   cd $APP_DIR"
echo ""
echo "2. Crear virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "3. Instalar dependencias:"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Crear archivo .env con configuración de producción"
echo ""
echo "5. Ejecutar migraciones:"
echo "   python manage.py migrate"
echo "   python manage.py collectstatic --noinput"
echo "   python manage.py createsuperuser"
echo ""
echo "6. Iniciar servicio:"
echo "   sudo systemctl start malargue"
echo "   sudo systemctl status malargue"
echo ""
echo "7. Verificar logs:"
echo "   sudo journalctl -u malargue -f"
echo "   tail -f /var/log/malargue/gunicorn_error.log"
echo ""
echo "8. Health check:"
echo "   curl http://localhost:8000/health/"
echo ""
echo "⚠️  IMPORTANTE:"
echo "  - Cambiar password de PostgreSQL en .env"
echo "  - Cambiar password de Redis en .env"
echo "  - Generar nuevo SECRET_KEY"
echo "  - Configurar ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS"
echo ""
echo "=============================================="
