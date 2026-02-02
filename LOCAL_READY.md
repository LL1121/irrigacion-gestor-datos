# ✅ DESARROLLO LOCAL - LISTO PARA ANALIZAR

**Status:** 🚀 SERVIDOR CORRIENDO  
**URL:** http://127.0.0.1:8000/  
**Admin:** http://127.0.0.1:8000/admin/  
**Base de datos:** SQLite (local, sin Docker)

---

## ✅ Setup completado

```
✅ Python 3.13.7 + venv
✅ Django 6.0.1 + todas las dependencias
✅ .env.local configurado para SQLite
✅ Migraciones ejecutadas
✅ Superusuario admin creado
  - Usuario: admin
  - Contraseña: admin123
✅ Static files recolectados (135 archivos)
✅ Servidor Django CORRIENDO en http://127.0.0.1:8000
✅ Auto-reload habilitado (cambios = reload automático)
```

---

## 🌐 Acceso a la app

### Puntos de entrada principales:

| URL | Descripción | Requiere Login |
|-----|-------------|---|
| `http://127.0.0.1:8000/` | Home page | ❌ No |
| `http://127.0.0.1:8000/admin/` | Django Admin | ✅ Sí |
| `http://127.0.0.1:8000/health/` | Health Check API | ❌ No |
| `http://127.0.0.1:8000/dashboard/` | Dashboard de mediciones | ✅ Sí |
| `http://127.0.0.1:8000/mapa/` | Mapa interactivo | ✅ Sí |

### Credenciales:
```
👤 Usuario: admin
🔑 Contraseña: admin123
```

---

## 📊 Lo que puedes analizar

### 1. **Admin Django** (http://127.0.0.1:8000/admin/)
   - Estructura de modelos
   - Gestión de usuarios
   - Datos de la aplicación
   - Permisos y grupos

### 2. **Interfaz Principal** (http://127.0.0.1:8000/)
   - Layout y diseño
   - Navegación
   - Formularios
   - Responsividad

### 3. **Dashboard** (http://127.0.0.1:8000/dashboard/)
   - Vistas protegidas
   - Datos de mediciones
   - Filtros y búsqueda

### 4. **API & Endpoints**
   - Health check: `/health/` (JSON)
   - Exportación CSV (si existe)
   - Upload de imágenes

### 5. **Archivos CSS/JS**
   - DevTools → Network → ver static files
   - DevTools → Console → ver si hay errores JavaScript
   - DevTools → Elements → inspeccionar HTML

---

## 🔧 Comandos útiles mientras analizas

### Parar el servidor
```powershell
# Presiona Ctrl+C en el terminal del servidor
```

### Reiniciar servidor (si haces cambios)
```powershell
# Ctrl+C para parar
# Luego ejecutar de nuevo:
.\venv\Scripts\python.exe manage.py runserver
```

### Ver logs del servidor
```powershell
# Los logs aparecen automáticamente en el terminal
# Busca líneas como:
# [INFO] Request GET /health/
# [ERROR] si algo falla
```

### Ejecutar un comando Django rápido
```powershell
# Sin parar el servidor, en otra PowerShell:
.\venv\Scripts\python.exe manage.py shell

# Dentro del shell:
>>> from django.contrib.auth.models import User
>>> User.objects.all()
```

### Ver base de datos
```powershell
# El archivo está en:
# db.sqlite3

# Para inspeccionar contenido:
.\venv\Scripts\python.exe manage.py dbshell
```

---

## 🎨 Analizando la Interfaz (Checklist)

### Estructura HTML
- [ ] Abrir DevTools (F12)
- [ ] Tab Elements
- [ ] Explorar estructura HTML
- [ ] Ver usar de templates
- [ ] Analizar forms

### Styling (CSS)
- [ ] DevTools → Elements → Styles
- [ ] Ver qué CSS se aplica
- [ ] Identificar clases personalizadas
- [ ] Analizar responsive design
- [ ] Probar en mobile (F12 → Toggle device toolbar)

### Funcionalidad (JavaScript)
- [ ] DevTools → Console
- [ ] Ver si hay errores de JS
- [ ] Buscar en Sources → ver archivos JS
- [ ] Probar interactividad (clicks, formularios)

### Rendimiento
- [ ] DevTools → Network
- [ ] Ver request/response times
- [ ] Tamaño de archivos
- [ ] Static files loading

### API Endpoints
- [ ] Abrir DevTools → Network
- [ ] Hacer acciones en la app
- [ ] Ver XHR/Fetch requests
- [ ] Analizar payloads

---

## 📁 Archivos importantes para revisar

### Templates (HTML)
```
templates/web/
├── base.html                 ← Template base
├── home.html                 ← Home page
├── dashboard.html            ← Dashboard
├── mapa.html                 ← Mapa
├── login.html                ← Login
└── ...
```

**Cómo verlos:**
1. Ir a la página en navegador
2. DevTools (F12) → Elements
3. Click derecho → "Edit as HTML"

### Vistas (Python)
```
web/
├── views.py                  ← Contiene todas las vistas
├── models.py                 ← Modelos de datos
└── urls.py                   ← Rutas de URL
```

**Para editarlos:**
1. Abrir archivo en VS Code
2. Cambios se aplican automáticamente (auto-reload)
3. Refrescar navegador

### Static Files (CSS/JS)
```
staticfiles/
├── admin/                    ← Admin Django CSS/JS
├── css/                      ← Tu CSS personalizado
└── js/                       ← Tu JavaScript
```

**Ver en DevTools:**
- F12 → Network
- Filter por CSS/JS
- Click en archivo para ver contenido

---

## 🐛 Errores comunes y soluciones

### "ConnectionRefusedError" al acceder a localhost:8000
```
→ El servidor no está corriendo
→ Ejecuta: .\venv\Scripts\python.exe manage.py runserver
```

### Cambios no aparecen después de editar
```
→ Necesitas refrescar (Ctrl+R o Cmd+R)
→ Para CSS: Ctrl+Shift+R (hard refresh)
→ Auto-reload toma 2-3 segundos
```

### Error "SyntaxError" en Python
```
→ Abrir el archivo en VS Code
→ Ver línea del error
→ Django mostrará el error en una página roja
→ Corregir y auto-reload debería funcionar
```

### 404 en CSS/JS
```
→ Ejecutar: .\venv\Scripts\python.exe manage.py collectstatic --noinput
→ Parar y reiniciar servidor
```

### Base de datos bloqueada
```
→ Parar el servidor (Ctrl+C)
→ Reiniciar: .\venv\Scripts\python.exe manage.py runserver
```

---

## 💡 Pro Tips para analizar

### 1. **Inspeccionar elemento y ver qué template lo renderea**
   - DevTools → Elements
   - Click en elemento
   - Buscar en templates/

### 2. **Seguir un request HTTP**
   - DevTools → Network
   - Click en la acción en la app
   - Ver request URL, method, headers, response

### 3. **Ver datos en la base de datos**
   - Ir a http://127.0.0.1:8000/admin/
   - Explorar cada modelo
   - Ver qué datos hay

### 4. **Activar Django Debug Toolbar** (opcional)
   ```powershell
   pip install django-debug-toolbar
   # Agregar a INSTALLED_APPS en settings.py
   # Agregara una barra en la página con info detallada
   ```

### 5. **Usar Django Shell para probar**
   ```powershell
   .\venv\Scripts\python.exe manage.py shell
   
   # Dentro:
   >>> from web.models import Medicion
   >>> Medicion.objects.all().count()  # Ver cuántas mediciones hay
   ```

---

## 🔍 Checklist de Análisis Completo

### Código Backend
- [ ] Revisar models.py (estructura de datos)
- [ ] Revisar views.py (lógica de negocio)
- [ ] Revisar urls.py (rutas)
- [ ] Revisar tests/ (qué se prueba)

### Interfaz Frontend
- [ ] Revisar HTML (estructura)
- [ ] Revisar CSS (estilos)
- [ ] Revisar JavaScript (interactividad)
- [ ] Probar formularios
- [ ] Probar en mobile

### Funcionalidad
- [ ] Login funciona
- [ ] CRUD de datos
- [ ] Filtros/búsqueda
- [ ] Uploads de archivos (si existen)
- [ ] APIs responden correctamente

### Seguridad
- [ ] @login_required en vistas protegidas
- [ ] CSRF tokens en formularios
- [ ] Permisos de usuario
- [ ] Validación de inputs

### Performance
- [ ] DevTools → Network → ver tiempos
- [ ] DevTools → Performance → medir
- [ ] Cargas de página rápidas

---

## 📝 Notas sobre el Desarrollo Local

- **SQLite:** No necesita PostgreSQL instalado. Datos se guardan en db.sqlite3
- **Auto-reload:** Cambios en Python se aplican automáticamente en 2-3 segundos
- **Debug mode:** DEBUG=True muestra errores detallados (solo en desarrollo)
- **Static files:** Necesita collectstatic para que se sirvan archivos CSS/JS
- **Email:** En dev se loguea, no se envía realmente

---

## 🎯 Próximos pasos

Después de analizar la interfaz:

1. **Documenta lo que viste**
   - Qué templates existen
   - Qué vistas están implementadas
   - Qué funcionalidades hay

2. **Identifica mejoras**
   - Cambios de diseño
   - Nuevas features
   - Bugs o errores

3. **Haz los cambios localmente**
   - Edita archivos
   - Prueba en browser
   - Verifica que funcione

4. **Commit a GitHub**
   ```powershell
   git add -A
   git commit -m "Descripción de cambios"
   git push
   ```

5. **Deploy a producción**
   - Cuando esté todo OK
   - Usar docker-deploy.sh en servidor
   - ¡A producción!

---

## 📞 Comandos rápidos

```powershell
# Activar venv
.\venv\Scripts\activate.ps1

# Instalar dependencias
pip install -r requirements/dev.txt

# Ver migraciones
.\venv\Scripts\python.exe manage.py showmigrations

# Hacer migraciones
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate

# Ejecutar tests
.\venv\Scripts\python.exe -m pytest web/tests/ -v

# Django shell
.\venv\Scripts\python.exe manage.py shell

# Runserver
.\venv\Scripts\python.exe manage.py runserver

# Collectstatic
.\venv\Scripts\python.exe manage.py collectstatic --noinput

# Crear superusuario
.\venv\Scripts\python.exe manage.py createsuperuser
```

---

**¡El servidor está corriendo! Analiza la interfaz con tranquilidad.**

Cuando termines, me avisas y coordinamos los cambios que necesites hacer antes del deploy. 🚀
