#!/bin/bash
# ==============================================================================
# Management Script - Irrigación Malargüe
# ==============================================================================
# Quick commands for common operations
# ==============================================================================

CONTAINER_NAME="irrigacion_malargue_app"

case "$1" in
    start)
        echo "🚀 Starting containers..."
        docker-compose up -d
        ;;
    stop)
        echo "🛑 Stopping containers..."
        docker-compose down
        ;;
    restart)
        echo "♻️  Restarting containers..."
        docker-compose restart
        ;;
    logs)
        echo "📋 Showing logs (Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
        ;;
    shell)
        echo "🐚 Opening shell in container..."
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    django-shell)
        echo "🐍 Opening Django shell..."
        docker exec -it $CONTAINER_NAME python manage.py shell
        ;;
    migrate)
        echo "🔄 Running migrations..."
        docker exec $CONTAINER_NAME python manage.py migrate
        ;;
    makemigrations)
        echo "📝 Creating migrations..."
        docker exec $CONTAINER_NAME python manage.py makemigrations
        ;;
    collectstatic)
        echo "📦 Collecting static files..."
        docker exec $CONTAINER_NAME python manage.py collectstatic --noinput
        ;;
    createsuperuser)
        echo "👤 Creating superuser..."
        docker exec -it $CONTAINER_NAME python manage.py createsuperuser
        ;;
    health)
        echo "🏥 Checking health..."
        curl -f http://localhost:8002/health/ && echo "✅ Healthy" || echo "❌ Unhealthy"
        ;;
    status)
        echo "📊 Container status:"
        docker ps | grep $CONTAINER_NAME
        echo ""
        echo "🏥 Health status:"
        docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "No health check"
        ;;
    rebuild)
        echo "🔨 Rebuilding container..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Rebuild complete"
        ;;
    clean)
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup complete"
        ;;
    backup-db)
        echo "💾 Creating database backup..."
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        docker exec $CONTAINER_NAME pg_dump -h db_central -U irrigacion_user irrigacion_malargue_db > $BACKUP_FILE
        echo "✅ Backup saved to $BACKUP_FILE"
        ;;
    *)
        echo "Irrigación Malargüe - Management Script"
        echo ""
        echo "Usage: ./manage.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start            Start containers"
        echo "  stop             Stop containers"
        echo "  restart          Restart containers"
        echo "  logs             View logs (tail)"
        echo "  shell            Open bash shell in container"
        echo "  django-shell     Open Django shell"
        echo "  migrate          Run database migrations"
        echo "  makemigrations   Create new migrations"
        echo "  collectstatic    Collect static files"
        echo "  createsuperuser  Create Django superuser"
        echo "  health           Check health endpoint"
        echo "  status           Show container status"
        echo "  rebuild          Rebuild container from scratch"
        echo "  clean            Clean up containers and volumes"
        echo "  backup-db        Create database backup"
        echo ""
        exit 1
        ;;
esac
