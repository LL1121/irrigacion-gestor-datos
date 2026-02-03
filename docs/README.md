# Documentación

## Índice
- [Descripción](#descripción)
- [Requisitos](#requisitos)
- [Setup de desarrollo](#setup-de-desarrollo)
- [Deployment (Producción)](#deployment-producción)
- [Operación y mantenimiento](#operación-y-mantenimiento)
- [PWA y modo offline](#pwa-y-modo-offline)
- [Mapa y mediciones GPS](#mapa-y-mediciones-gps)
- [Seguridad](#seguridad)
- [Troubleshooting](#troubleshooting)

---

## Descripción
Sistema web para gestión de mediciones de caudalímetros con PWA offline-first, validaciones, reportes y visualización en mapas.

---

## Requisitos
**Desarrollo**
- Python 3.9+
- PostgreSQL 12+
- Redis 6+ (opcional en dev)

**Producción**
- Ubuntu/Debian
- Nginx + Gunicorn
- Certbot/HTTPS

---

## Setup de desarrollo
1. Crear entorno virtual y dependencias:
```
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Configurar `.env` (ver ejemplo en README principal).
3. Migraciones y static:
```
python manage.py migrate
python manage.py collectstatic --noinput
```
4. Ejecutar servidor:
```
python manage.py runserver
```

---

## Deployment (Producción)
Checklist esencial:
- `DEBUG=False`
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`
- HTTPS y certificados
- `collectstatic` y servir `static/` + `media/`
- Backup de DB y medios
- Health check `/health/`

Recomendado:
- Nginx + Gunicorn + systemd
- Logs y rotación
- Redis para cache

---

## Operación y mantenimiento
- Backups periódicos de DB
- Revisión de logs y alertas
- Monitoreo de latencia y errores

---

## PWA y modo offline
- Service Worker para cache de assets
- IndexedDB para cola offline
- Sync automático cuando vuelve la conexión

---

## Mapa y mediciones GPS
- Leaflet + OpenStreetMap
- GeoJSON desde API semanal
- Pins basados en coordenadas EXIF

---

## Seguridad
- Rate limit en login y cargas
- Validaciones de medición
- Roles (staff/operadores)

---

## Troubleshooting
- Verificar `.env`
- Revisar migraciones pendientes
- Validar que `MEDIA_URL`/`MEDIA_ROOT` estén correctos
- Revisar logs de Nginx/Gunicorn
