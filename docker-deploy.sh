#!/bin/bash

###############################################################################
# MALARGUE DOCKER DEPLOYMENT SCRIPT
# Script para desplegar Malargue desde el servidor en producción
# 
# Uso:
#   sudo bash deploy.sh deploy
#   sudo bash deploy.sh stop
#   sudo bash deploy.sh logs
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/your-username/IrrigacionPetroleras.git"  # CAMBIAR
BRANCH="main"
DEPLOY_DIR="/home/malargue/IrrigacionPetroleras"
DOMAIN="irrigacionmalargue.net"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Check root
check_root() {
    [[ $EUID -eq 0 ]] || log_error "Ejecuta con sudo"
}

# Check Docker
check_docker() {
    command -v docker &> /dev/null || log_error "Docker no instalado"
    command -v docker-compose &> /dev/null || log_error "Docker Compose no instalado"
    log_success "Docker instalado"
}

# Setup repo
setup_repo() {
    log_info "Configurando repositorio..."
    
    if [ -d "$DEPLOY_DIR" ]; then
        cd "$DEPLOY_DIR"
        git fetch origin
        git checkout $BRANCH
        git pull origin $BRANCH
    else
        git clone -b $BRANCH $REPO_URL $DEPLOY_DIR
    fi
    
    log_success "Repo configurado"
}

# Setup .env
setup_env() {
    log_info "Configurando .env..."
    
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env.production" "$DEPLOY_DIR/.env" || log_error ".env.production no existe"
        log_warning "Edita $DEPLOY_DIR/.env con tus valores:"
        nano "$DEPLOY_DIR/.env"
    fi
    
    log_success ".env configurado"
}

# Create directories
create_dirs() {
    mkdir -p "$DEPLOY_DIR"/{media,staticfiles,logs}
    chown -R 1000:1000 "$DEPLOY_DIR"/{media,staticfiles,logs}
    log_success "Directorios creados"
}

# Start containers
start_containers() {
    log_info "Compilando y iniciando contenedores..."
    cd "$DEPLOY_DIR"
    docker-compose build --no-cache
    docker-compose up -d
    sleep 10
    log_success "Contenedores iniciados"
}

# Run migrations
run_migrations() {
    log_info "Ejecutando migraciones..."
    cd "$DEPLOY_DIR"
    docker-compose exec -T web python manage.py migrate
    log_success "Migraciones completadas"
}

# Collect static
collect_static() {
    log_info "Recolectando archivos estáticos..."
    cd "$DEPLOY_DIR"
    docker-compose exec -T web python manage.py collectstatic --noinput
    log_success "Archivos estáticos recolectados"
}

# Health check
health_check() {
    log_info "Verificando salud de la app..."
    curl -f http://localhost:8000/health/ > /dev/null || log_error "Health check fallido"
    log_success "Health check OK"
}

# Show logs
show_logs() {
    log_info "Mostrando logs (Ctrl+C para salir)..."
    cd "$DEPLOY_DIR"
    docker-compose logs -f web
}

# Stop containers
stop_containers() {
    log_info "Deteniendo contenedores..."
    cd "$DEPLOY_DIR"
    docker-compose down
    log_success "Contenedores detenidos"
}

# Full deployment
full_deploy() {
    echo ""
    echo "================================"
    echo "  MALARGUE DOCKER DEPLOYMENT"
    echo "================================"
    echo ""
    
    check_root
    check_docker
    setup_repo
    setup_env
    create_dirs
    start_containers
    run_migrations
    collect_static
    health_check
    
    echo ""
    echo "================================"
    log_success "¡DEPLOY COMPLETADO!"
    echo "================================"
    echo ""
    echo "📍 App disponible en: http://localhost:8000"
    echo "📍 Admin en: http://localhost:8000/admin"
    echo ""
    echo "Comandos útiles:"
    echo "  Ver logs:     sudo bash deploy.sh logs"
    echo "  Parar:        sudo bash deploy.sh stop"
    echo "  Reiniciar:    sudo bash deploy.sh restart"
    echo "  Actualizar:   sudo bash deploy.sh update"
    echo ""
}

# Main handler
case "${1:-deploy}" in
    deploy) full_deploy ;;
    stop) stop_containers ;;
    logs) show_logs ;;
    restart) stop_containers && sleep 2 && start_containers ;;
    update) setup_repo && docker-compose -f $DEPLOY_DIR/docker-compose.yml up -d ;;
    health) health_check ;;
    *)
        echo "Uso: $0 {deploy|stop|logs|restart|update|health}"
        exit 1
        ;;
esac
