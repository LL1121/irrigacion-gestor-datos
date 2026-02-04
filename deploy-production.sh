#!/bin/bash
# ==============================================================================
# Production Deployment Script - Irrigación Malargüe
# ==============================================================================
# Cloudflare Tunnel setup with shared PostgreSQL (db_central)
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "Starting deployment for Irrigación Malargüe..."

# Check .env
if [ ! -f .env ]; then
    log_error ".env file not found!"
    log_info "Copy env.production.example to .env first:"
    log_info "  cp env.production.example .env && nano .env"
    exit 1
fi
log_success ".env file found"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running!"
    exit 1
fi
log_success "Docker is running"

# Check/create shared network
if ! docker network inspect shared_network > /dev/null 2>&1; then
    log_warning "Creating shared_network..."
    docker network create shared_network
fi
log_success "shared_network exists"

# Check db_central
if ! docker ps --format '{{.Names}}' | grep -q "db_central"; then
    log_error "db_central container not running!"
    exit 1
fi
log_success "db_central is running"

# Build
log_info "Building Docker image..."
docker-compose build --no-cache
log_success "Build complete"

# Stop old containers
log_info "Stopping old containers..."
docker-compose down
log_success "Old containers stopped"

# Start new containers
log_info "Starting new containers..."
docker-compose up -d
log_success "Containers started"

# Wait for health
log_info "Waiting for container..."
sleep 10

# Check running
if ! docker ps --format '{{.Names}}' | grep -q "irrigacion_malargue_app"; then
    log_error "Container failed to start!"
    log_info "Check logs: docker logs irrigacion_malargue_app"
    exit 1
fi
log_success "Container is running"

# Migrations
log_info "Running migrations..."
docker exec irrigacion_malargue_app python manage.py migrate --noinput
log_success "Migrations done"

# Static files
log_info "Collecting static files..."
docker exec irrigacion_malargue_app python manage.py collectstatic --noinput
log_success "Static files collected"

# Summary
echo ""
log_success "======================================"
log_success "  Deployment Complete!"
log_success "======================================"
echo ""
log_info "Container: irrigacion_malargue_app"
log_info "Ports: 8000 (internal) → 8002 (Cloudflare Tunnel)"
log_info "Domain: https://irrigacionmalargue.net"
log_info "Database: db_central"
echo ""
log_info "Commands:"
log_info "  Logs:    docker logs -f irrigacion_malargue_app"
log_info "  Restart: docker-compose restart"
log_info "  Shell:   docker exec -it irrigacion_malargue_app /bin/bash"
echo ""
