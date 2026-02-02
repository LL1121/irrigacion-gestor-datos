# 🖥️ LOCAL DEVELOPMENT SETUP GUIDE

**Status:** ✅ READY TO USE  
**Date:** February 2, 2026  
**Environment:** Local SQLite (no PostgreSQL needed)  

---

## ✅ Todo está configurado

```
✅ Python 3.13.7 + venv activado
✅ Django 6.0.1 instalado
✅ Todas las dependencias (dev, testing, etc)
✅ .env.local configurado para SQLite
✅ Migraciones ejecutadas
✅ Superusuario creado (admin:admin123)
✅ Static files recolectados (135 archivos)
✅ Servidor Django corriendo en http://127.0.0.1:8000
```

---

## 🚀 Acceso a la app

| URL | Descripción |
|-----|-------------|
| `http://127.0.0.1:8000/` | Home page |
| `http://127.0.0.1:8000/admin/` | Django Admin |
| `http://127.0.0.1:8000/health/` | Health check API |
| `http://127.0.0.1:8000/mapa/` | Mapa de riego |

### Credenciales de prueba:
```
Username: admin
Password: admin123
```

---

## 📝 Comandos útiles en desarrollo

### Ver logs en tiempo real
```bash
# Ya está corriendo en background en el terminal actual
# Los logs aparecen automáticamente
```

### Parar el servidor
```powershell
# Ctrl+C en el terminal donde corre runserver
```

### Reiniciar servidor
```powershell
# Parar con Ctrl+C
.\venv\Scripts\python.exe manage.py runserver
```

### Ejecutar tests
```powershell
.\venv\Scripts\python.exe manage.py pytest
# O con coverage:
.\venv\Scripts\python.exe -m pytest web/tests/ -v --cov=web --cov-report=html
```

### Ejecutar comando Django
```powershell
.\venv\Scripts\python.exe manage.py shell
# Dentro del shell:
>>> from web.models import Medicion
>>> Medicion.objects.all().count()
```

### Crear nuevas migraciones
```powershell
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate
```

### Crear superusuario adicional
```powershell
.\venv\Scripts\python.exe manage.py createsuperuser
```

---

## 🗄️ Base de Datos

### En desarrollo usamos:
- **SQLite** (db.sqlite3)
- No requiere instalación de PostgreSQL
- Perfecto para análisis local de la interfaz

### Si necesitás datos:
```powershell
# Cargar datos de fixture (si existen)
.\venv\Scripts\python.exe manage.py loaddata web/fixtures/data.json

# Exportar datos a JSON
.\venv\Scripts\python.exe manage.py dumpdata web > backup.json

# Limpiar base de datos
.\venv\Scripts\python.exe manage.py flush
```

---

## 🧪 Testing

### Ejecutar tests
```powershell
.\venv\Scripts\python.exe -m pytest web/tests/ -v
```

### Con coverage
```powershell
.\venv\Scripts\python.exe -m pytest web/tests/ -v --cov=web --cov-report=html
# Ver reporte en: htmlcov/index.html
```

### Tests específicos
```powershell
# Solo tests de views
.\venv\Scripts\python.exe -m pytest web/tests/test_views.py -v

# Solo un test
.\venv\Scripts\python.exe -m pytest web/tests/test_views.py::test_login_required -v
```

---

## 📁 Estructura de archivos importante

```
IrrigacionPetroleras/
├── config/
│   └── settings.py           ← Configuración principal
├── web/
│   ├── views.py              ← Vistas/handlers
│   ├── models.py             ← Modelos DB
│   ├── tests/                ← Tests unitarios
│   └── templates/            ← HTML templates
├── templates/
│   └── web/                  ← Templates
├── staticfiles/              ← CSS, JS compilados
├── media/                    ← Fotos/archivos subidos
├── db.sqlite3                ← Base de datos local
├── .env.local                ← Variables de entorno (dev)
├── manage.py                 ← Django CLI
└── requirements/
    ├── base.txt              ← Deps principales
    ├── dev.txt               ← + testing/debug
    └── prod.txt              ← Solo base.txt
```

---

## 🔍 Analizando la Interfaz

### Vistas principales que puedes explorar:

1. **Admin Django:** `http://127.0.0.1:8000/admin/`
   - Ver/editar usuarios
   - Gestionar modelos
   - Datos de la aplicación

2. **Home:** `http://127.0.0.1:8000/`
   - Landing page
   - Interfaz principal

3. **Dashboard:** `http://127.0.0.1:8000/dashboard/`
   - Dashboard de mediciones (requiere login)

4. **Mapa:** `http://127.0.0.1:8000/mapa/`
   - Mapa interactivo de riego (requiere login)

5. **Health Check:** `http://127.0.0.1:8000/health/`
   - JSON con estado de la app

---

## 💡 Tips para desarrollo

### Auto-reload activado
- Cambios en Python → reload automático
- Cambios en templates → reload automático
- Cambios en static files → necesita Ctrl+Shift+R en navegador (hard refresh)

### Debug mode
```python
# En settings.py, DEBUG=True (desarrollo)
# Ves errores detallados en páginas

# En producción, DEBUG=False
# Errors se loguean, no se muestran
```

### Shell interactivo
```powershell
.\venv\Scripts\python.exe manage.py shell
```

Dentro del shell:
```python
from web.models import Medicion
from django.contrib.auth.models import User

# Ver usuarios
User.objects.all()

# Ver mediciones
Medicion.objects.all().count()

# Crear dato de prueba
Medicion.objects.create(
    user=User.objects.first(),
    latitud=-35.395,
    longitud=-69.551,
    valor=45.5
)
```

---

## 🔧 Troubleshooting

### Error: "Address already in use"
```powershell
# Puerto 8000 en uso, usar otro puerto:
.\venv\Scripts\python.exe manage.py runserver 8001
```

### Error: "No module named 'django'"
```powershell
# Venv no está activado
.\venv\Scripts\activate.ps1

# O instalar requirements nuevamente
pip install -r requirements/dev.txt
```

### Error: "db.sqlite3 is locked"
```powershell
# Base de datos bloqueada, usar otra terminal
# O parar el servidor y reiniciar
```

### Error: "TemplateNotFound"
```powershell
# Falta template HTML
# Verificar que existe en templates/web/
# Parar servidor y reiniciar
```

---

## 📊 Estadísticas del Proyecto

```
- Modelos: 5+ (User, Medicion, etc)
- Vistas: 15+ (login, dashboard, mapa, API, etc)
- Tests: 11 (100% pasando)
- Coverage: 48%
- Templates: 8+ archivos HTML
- Static files: 135 archivos (CSS, JS, etc)
- Líneas de código: ~2000+ Python
```

---

## ✅ Checklist para analizar interfaz

- [ ] Acceder a http://127.0.0.1:8000/admin/ (login con admin:admin123)
- [ ] Explorar usuarios y permisos
- [ ] Ver modelos de datos
- [ ] Acceder a http://127.0.0.1:8000/ (home page)
- [ ] Revisar CSS y diseño
- [ ] Revisar JavaScript funcionalidad
- [ ] Analizar HTML templates
- [ ] Probar formularios
- [ ] Ver cómo se ven en mobile (F12 DevTools)
- [ ] Revisar static files en DevTools (Network tab)

---

## 📚 Recursos útiles

### Django Documentation
- https://docs.djangoproject.com/en/6.0/

### Testing
- https://docs.pytest.org/
- https://pytest-django.readthedocs.io/

### Your local files
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Para producción
- [DOCKER_READY.md](DOCKER_READY.md) - Resumen de deployment
- [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md) - Checklist

---

## 🎯 Próximos pasos después de analizar

1. **Análisis completo** de la interfaz (URLs, templates, CSS, JS)
2. **Cambios/mejoras** que necesites hacer
3. **Commit de cambios** a GitHub
4. **Deploy a producción** con Docker

---

**¡Disfruta analizando la interfaz! El servidor está corriendo en background.** 

Cualquier duda o error que veas, me avisas y lo arreglamos.
