# 🌊 Malargüe DB - Sistema de Mediciones de Caudalímetros

Sistema web para la gestión y monitoreo de mediciones de caudalímetros en zonas petroleras de Malargüe, con soporte **offline-first** mediante PWA para operarios en campo sin conectividad.

---

## 🚀 Features

### ✅ Core Features
- **Autenticación Django** con roles (Operarios/Staff)
- **Carga de mediciones** con foto, GPS y timestamp
- **Offline-First PWA** con IndexedDB para sincronización automática
- **Dashboard administrativo** con panel de gestión de usuarios
- **Exportación CSV/PNG** de datos y gráficos
- **Mapa de rutas semanales** con Leaflet
- **Validación de datos** en backend y frontend

### 🔒 Security & Production
- ✅ PostgreSQL con migraciones completas
- ✅ Rate limiting (login: 5/min, uploads: 10/min)
- ✅ HTTPS/SSL configurado
- ✅ Environment variables con `python-decouple`
- ✅ Sentry integration para error tracking
- ✅ Redis caching
- ✅ Logging con RotatingFileHandler
- ✅ Health check endpoint (`/health/`)
- ✅ Backup command (`python manage.py backup_data`)

### 📱 PWA Features
- Service Worker para cache de assets
- IndexedDB para queue de uploads offline
- Sincronización automática al reconectar
- Badge indicator de uploads pendientes
- Instalable como app nativa

---

## 📋 Requisitos

### Desarrollo
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Node.js (opcional, para dev tools)

### Producción
- Ubuntu 20.04+ / Debian 11+
- Nginx
- Gunicorn
- Certbot (Let's Encrypt)
- Dominio configurado

---

## 🛠️ Instalación (Desarrollo)

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-usuario/IrrigacionPetroleras.git
cd IrrigacionPetroleras
```

### 2. Crear virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\Activate.ps1  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL
```bash
# Crear base de datos
psql -U postgres
CREATE DATABASE malargue_db;
CREATE USER postgres WITH PASSWORD '112129';
GRANT ALL PRIVILEGES ON DATABASE malargue_db TO postgres;
\q
```

### 5. Configurar .env
```bash
cp .env.example .env
# Editar .env con tus valores
```

Ejemplo `.env` para desarrollo:
```env
DEBUG=True
SECRET_KEY=django-insecure-dev-key
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

DATABASE_URL=postgresql://postgres:112129@localhost:5432/malargue_db
REDIS_URL=redis://127.0.0.1:6379/1

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### 6. Ejecutar migraciones
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 7. Iniciar servidor
```bash
python manage.py runserver
```

Acceder a: http://127.0.0.1:8000

---

## 🚀 Deployment (Producción)

Ver guía completa en [docs/README.md](docs/README.md)

### Quick Start
```bash
# 1. Subir código al servidor
rsync -avz --exclude 'venv' IrrigacionPetroleras/ user@servidor:/home/malargue/IrrigacionPetroleras/

# 2. Ejecutar setup automático
cd /home/malargue/IrrigacionPetroleras
sudo bash server_setup.sh

# 3. Configurar como usuario malargue
su - malargue
cd IrrigacionPetroleras
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar .env de producción
cp .env.example .env
nano .env  # Editar valores

# 5. Migrations y collectstatic
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 6. Iniciar servicio
sudo systemctl start malargue
sudo systemctl enable malargue
```

---

## 📁 Estructura del Proyecto

```
IrrigacionPetroleras/
├── config/
│   ├── settings.py          # Configuración Django
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # WSGI application
├── web/
│   ├── models.py            # Modelos (Medicion, EmpresaPerfil)
│   ├── views.py             # Views y lógica de negocio
│   ├── urls.py              # URLs de la app
│   ├── admin.py             # Admin panel customizado
│   ├── utils.py             # Utilidades (EXIF, compress)
│   ├── management/
│   │   └── commands/
│   │       └── backup_data.py  # Comando de backup
│   ├── migrations/          # Migraciones DB
│   └── tests/               # Tests unitarios
├── templates/
│   └── web/                 # Templates HTML
├── static/
│   ├── css/
│   ├── js/
│   │   ├── offline-upload.js  # PWA offline logic
│   │   └── sw.js              # Service Worker
│   └── images/
├── media/
│   └── evidencias/          # Fotos subidas
├── logs/                    # Application logs
├── staticfiles/             # Collectstatic output
├── .env                     # Environment variables (no commitear)
├── .env.example             # Template de variables
├── requirements.txt         # Python dependencies
├── manage.py                # Django CLI
├── deploy.sh                # Script de deployment
├── server_setup.sh          # Setup automático del servidor
├── nginx.conf               # Configuración Nginx
├── gunicorn.conf.py         # Configuración Gunicorn
├── malargue.service         # Systemd service
├── pytest.ini               # Testing config
└── DEPLOYMENT.md            # Guía de deployment
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
coverage run -m pytest
coverage report
coverage html  # Ver en htmlcov/index.html

# Tests específicos
pytest web/tests/test_models.py
pytest web/tests/test_views.py
```

---

## 📊 API Endpoints

### Autenticación
- `POST /login/` - Login
- `GET /logout/` - Logout

### Dashboard
- `GET /` - Dashboard del usuario

### Mediciones
- `GET /cargar/` - Formulario de carga
- `POST /cargar/` - Guardar medición
- `GET /api/weekly-route/` - Datos de ruta semanal (JSON)
- `GET /mapa/` - Mapa de rutas

### Exportación
- `GET /exportar/` - Exportar CSV con todas las mediciones

### Admin Panel
- `GET /gestion/usuarios/` - Lista de usuarios
- `POST /gestion/usuarios/crear/` - Crear usuario
- `GET /gestion/empresas/` - Lista de empresas

### Health Check
- `GET /health/` - Health check (DB + Redis status)

---

## 🔧 Comandos útiles

```bash
# Development server
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Collectstatic
python manage.py collectstatic --noinput

# Crear superusuario
python manage.py createsuperuser

# Backup de datos
python manage.py backup_data --output backups/

# Django shell
python manage.py shell

# Check de deployment
python manage.py check --deploy

# Production server (Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 🔐 Seguridad

### Implementado
- ✅ SECRET_KEY en variable de entorno
- ✅ DEBUG=False en producción
- ✅ ALLOWED_HOSTS configurado
- ✅ CSRF protection
- ✅ Rate limiting en login y uploads
- ✅ HTTPS/SSL redirect
- ✅ Secure cookies (HTTPS only)
- ✅ HSTS headers
- ✅ Password validators
- ✅ `@login_required` en views protegidas

### Recomendaciones adicionales
- Configurar Fail2ban en el servidor
- Backups automáticos con cron
- Monitoring con Sentry
- Firewall (UFW) configurado

---

## 📝 Variables de Entorno

Ver `.env.example` para la lista completa. Principales:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DEBUG` | Modo debug | `False` |
| `SECRET_KEY` | Django secret key | `<random-string>` |
| `ALLOWED_HOSTS` | Hosts permitidos | `dominio.com,www.dominio.com` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@localhost/db` |
| `REDIS_URL` | Redis URL | `redis://:password@localhost:6379/1` |
| `SENTRY_DSN` | Sentry DSN (opcional) | `https://...@sentry.io/...` |

---

## 🐛 Troubleshooting

### Static files no cargan
```bash
python manage.py collectstatic --noinput
# Verificar STATIC_ROOT en settings.py
```

### Error de base de datos
```bash
# Verificar conexión
psql -U postgres -d malargue_db

# Ver logs
tail -f logs/django.log
```

### Gunicorn no inicia
```bash
# Ver logs
sudo journalctl -u malargue -f

# Test manual
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

### 502 Bad Gateway (Nginx)
```bash
# Verificar que Gunicorn esté corriendo
curl http://127.0.0.1:8000/health/

# Ver logs de Nginx
tail -f /var/log/nginx/malargue_error.log
```

---

## 📄 Licencia

Propietario - Uso interno

---

## 👥 Contacto

Para soporte o consultas: [tu-email@dominio.com]

---

## 🗺️ Roadmap

- [ ] Dashboard con gráficos en tiempo real
- [ ] Notificaciones push para alertas
- [ ] App móvil nativa (React Native)
- [ ] API REST completa con DRF
- [ ] Integración con sistemas SCADA
- [ ] Machine Learning para detección de anomalías

---

**Última actualización:** Febrero 2026
