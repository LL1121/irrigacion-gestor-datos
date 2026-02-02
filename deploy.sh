#!/bin/bash
# ==============================================================
# Malargüe DB - Production Deployment Script
# ==============================================================
# Este script prepara la aplicación para producción
# Ejecutar ANTES de desplegar al servidor
# ==============================================================

set -e  # Salir si cualquier comando falla

echo "🚀 Iniciando deployment checklist..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ----------------------------------------------------------
# 1. Verificar que estamos en el directorio correcto
# ----------------------------------------------------------
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No se encontró manage.py${NC}"
    echo "Ejecutá este script desde el directorio raíz del proyecto"
    exit 1
fi

echo -e "${GREEN}✅ Directorio correcto${NC}"

# ----------------------------------------------------------
# 2. Verificar archivo .env
# ----------------------------------------------------------
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: No se encontró archivo .env${NC}"
    echo "Copiá .env.example a .env y configuralo:"
    echo "  cp .env.example .env"
    exit 1
fi

echo -e "${GREEN}✅ Archivo .env encontrado${NC}"

# ----------------------------------------------------------
# 3. Verificar configuración de producción
# ----------------------------------------------------------
if grep -q "DEBUG=True" .env; then
    echo -e "${YELLOW}⚠️  WARNING: DEBUG=True en .env${NC}"
    echo "En producción, cambiá DEBUG=False"
    read -p "¿Continuar de todas formas? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ----------------------------------------------------------
# 4. Activar virtual environment
# ----------------------------------------------------------
if [ -d "venv" ]; then
    echo "🔧 Activando virtual environment..."
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activado${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró venv, asumiendo ambiente global${NC}"
fi

# ----------------------------------------------------------
# 5. Instalar/actualizar dependencias
# ----------------------------------------------------------
echo "📦 Instalando dependencias..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# ----------------------------------------------------------
# 6. Ejecutar migraciones
# ----------------------------------------------------------
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput
echo -e "${GREEN}✅ Migraciones aplicadas${NC}"

# ----------------------------------------------------------
# 7. Collect static files
# ----------------------------------------------------------
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✅ Static files recolectados${NC}"

# ----------------------------------------------------------
# 8. Verificar configuración de Django
# ----------------------------------------------------------
echo "🔍 Verificando configuración de deployment..."
python manage.py check --deploy --fail-level WARNING 2>&1 | tee deploy_check.log

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Hay advertencias de deployment (ver deploy_check.log)${NC}"
    read -p "¿Continuar de todas formas? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ Verificación completada${NC}"

# ----------------------------------------------------------
# 9. Ejecutar tests
# ----------------------------------------------------------
echo "🧪 Ejecutando tests..."
if command -v pytest &> /dev/null; then
    pytest --tb=short --quiet
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests pasaron${NC}"
    else
        echo -e "${RED}❌ Tests fallaron${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  pytest no instalado, skipeando tests${NC}"
fi

# ----------------------------------------------------------
# 10. Crear directorio de logs
# ----------------------------------------------------------
echo "📝 Creando directorio de logs..."
mkdir -p logs
chmod 755 logs
echo -e "${GREEN}✅ Directorio logs creado${NC}"

# ----------------------------------------------------------
# 11. Backup de base de datos (opcional)
# ----------------------------------------------------------
echo "💾 ¿Crear backup antes del deploy?"
read -p "Crear backup? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
    mkdir -p "$BACKUP_DIR"
    python manage.py backup_data --output "$BACKUP_DIR"
    echo -e "${GREEN}✅ Backup creado en $BACKUP_DIR${NC}"
fi

# ----------------------------------------------------------
# 12. Resumen
# ----------------------------------------------------------
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Deployment checklist completado${NC}"
echo "=============================================="
echo ""
echo "Próximos pasos:"
echo "  1. Subir archivos al servidor"
echo "  2. Configurar Nginx (ver nginx.conf.example)"
echo "  3. Configurar systemd service (ver malargue.service.example)"
echo "  4. Configurar SSL con Let's Encrypt"
echo "  5. Iniciar servicios:"
echo "       sudo systemctl start malargue"
echo "       sudo systemctl enable malargue"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs: journalctl -u malargue -f"
echo "  - Restart: sudo systemctl restart malargue"
echo "  - Status: sudo systemctl status malargue"
echo "  - Health check: curl http://localhost:8000/health/"
echo ""
echo "=============================================="
