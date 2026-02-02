# 🐳 MALARGUE DOCKER DEPLOYMENT GUIDE

**Dominio:** `irrigacionmalargue.net`  
**Método:** Docker + Docker Compose  
**Tiempo estimado:** 20-30 minutos  
**Dificultad:** Media

---

## 📋 Prerequisites

### En tu máquina local (Development)
- ✅ Git instalado
- ✅ Código en GitHub (repositorio público o private)
- ✅ Todos los tests pasando (`pytest`)
- ✅ Código commiteado y pusheado

### En el servidor (Production)
- Ubuntu 20.04 LTS o superior (recomendado Ubuntu 22.04)
- Debian 11 o superior
- 2GB RAM mínimo (4GB recomendado)
- 20GB storage mínimo
- SSH access como root o con sudo
- Conexión a internet estable
- Dominio registrado y apuntando a Cloudflare

---

## 🚀 DEPLOYMENT STEP-BY-STEP

### PASO 1: Preparar el servidor

**Conectarse al servidor:**
```bash
ssh root@tu-ip-del-servidor
# O si usas clave:
ssh -i /path/to/key root@tu-ip-del-servidor
```

**Actualizar sistema:**
```bash
apt update && apt upgrade -y
apt install -y curl git
```

**Instalar Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar que Docker está instalado
docker --version
docker-compose --version
```

**Crear usuario para la aplicación (optional but recommended):**
```bash
useradd -m -s /bin/bash malargue
usermod -aG docker malargue
```

---

### PASO 2: Clonar el repositorio

```bash
cd /home/malargue
git clone https://github.com/your-username/IrrigacionPetroleras.git
cd IrrigacionPetroleras
```

Reemplaza `your-username` con tu usuario de GitHub.

---

### PASO 3: Configurar variables de entorno

**Copiar plantilla:**
```bash
cp .env.production .env
```

**Editar .env con valores de producción:**
```bash
nano .env
```

**Valores que DEBES cambiar:**
```env
# CRÍTICO - Generar nuevo con:
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY=TU_NUEVA_CLAVE_SUPER_SEGURA_AQUI

# CRÍTICO - Contraseña segura (32+ caracteres)
DB_PASSWORD=ContrasenaSeguraParaPostgreSQL123!@#

# CRÍTICO - Contraseña segura (32+ caracteres)
REDIS_PASSWORD=ContrasenaSeguraParaRedis123!@#

# OPCIONAL - Si usas Sentry para monitoreo
SENTRY_DSN=

# VERIFICAR - Debe apuntar a tu dominio
ALLOWED_HOSTS=irrigacionmalargue.net,www.irrigacionmalargue.net
CSRF_TRUSTED_ORIGINS=https://irrigacionmalargue.net,https://www.irrigacionmalargue.net
```

**Generar SECRET_KEY seguro:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copia el resultado y ponlo en `SECRET_KEY=...`

---

### PASO 4: Crear directorios y permisos

```bash
mkdir -p media staticfiles logs
chmod 755 media staticfiles logs

# Si creaste usuario malargue:
chown -R malargue:malargue /home/malargue/IrrigacionPetroleras
```

---

### PASO 5: Construir e iniciar contenedores

```bash
# Construir la imagen de Docker
docker-compose build --no-cache

# Iniciar los contenedores
docker-compose up -d

# Esperar 15 segundos para que se inicialicen
sleep 15

# Verificar que todo está corriendo
docker-compose ps
```

Deberías ver 3 contenedores corriendo:
- `malargue_postgres` (PostgreSQL)
- `malargue_redis` (Redis)
- `malargue_app` (Django app)

---

### PASO 6: Ejecutar migraciones

```bash
# Las migraciones se ejecutan automáticamente en el docker-compose.yml
# Pero si quieres ejecutarlas manualmente:
docker-compose exec web python manage.py migrate

# Verificar que completaron:
# Deberías ver algo como: "Applying [app] [migration]..."
```

---

### PASO 7: Crear superusuario (Admin)

```bash
docker-compose exec web python manage.py createsuperuser

# Te pedirá:
# Username: admin
# Email: admin@irrigacionmalargue.net
# Password: Tu contraseña admin
```

---

### PASO 8: Verificar que funciona

**Health check:**
```bash
curl http://localhost:8000/health/
```

Deberías ver algo como:
```json
{"status": "healthy", "database": "connected", "cache": "connected", "timestamp": "..."}
```

**Ver logs:**
```bash
docker-compose logs web
docker-compose logs postgres
docker-compose logs redis
```

---

### PASO 9: Configurar Cloudflare

**En tu panel de Cloudflare (cloudflare.com):**

1. **DNS Records:**
   - Tipo: `A`
   - Nombre: `@` (raíz del dominio)
   - IPv4: Tu IP del servidor
   - Proxy status: `Proxied` (nube naranja)

2. **SSL/TLS:**
   - Modo: `Full` (no Full Strict)
   - Certificados autofirmados están OK

3. **Firewall Rules (Opcional):**
   - Bloquear bots
   - Limitar requests por IP
   - Rate limiting

4. **Page Rules (Opcional):**
   - Cache TTL: 1 hora
   - Compression: Enable

---

### PASO 10: Pruebas finales

**Acceder a la app:**
```
https://irrigacionmalargue.net
https://irrigacionmalargue.net/admin  (login con superuser)
```

**Ver logs en tiempo real:**
```bash
docker-compose logs -f web
```

**Reiniciar si es necesario:**
```bash
docker-compose restart web
docker-compose restart postgres
docker-compose restart redis
```

---

## 🔄 Comandos útiles en Producción

### Ver estado
```bash
docker-compose ps
docker-compose logs web -n 50  # Últimas 50 líneas
```

### Reiniciar servicios
```bash
docker-compose restart web        # Solo app
docker-compose restart postgres   # Solo DB
docker-compose restart redis      # Solo cache
docker-compose restart            # Todos
```

### Parar todo
```bash
docker-compose down
```

### Actualizar código (pull de GitHub y reiniciar)
```bash
git pull origin main
docker-compose build --no-cache
docker-compose up -d
docker-compose exec -T web python manage.py migrate
```

### Ejecutar comando Django
```bash
docker-compose exec web python manage.py [comando]

# Ejemplos:
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

### Backup de datos
```bash
docker-compose exec -T postgres pg_dump -U malargue_user malargue_db > backup-$(date +%Y-%m-%d).sql
```

### Restore de datos
```bash
docker-compose exec -T postgres psql -U malargue_user malargue_db < backup-2026-02-02.sql
```

---

## 🐛 Troubleshooting

### Error: "Connection refused" en PostgreSQL
```bash
# PostgreSQL tarda en iniciar, espera 30 segundos
sleep 30
docker-compose logs postgres

# Si sigue fallando:
docker-compose down
docker-compose up -d
docker-compose logs postgres
```

### Error: "Redis connection refused"
```bash
docker-compose restart redis
sleep 10
curl http://localhost:8000/health/
```

### Static files not loading (404 en CSS/JS)
```bash
docker-compose exec web python manage.py collectstatic --noinput --clear
docker-compose restart web
```

### Error: "Address already in use"
```bash
# Puerto 8000 está en uso, cambiar en docker-compose.yml
# O matar el proceso:
lsof -i :8000
kill -9 [PID]
docker-compose up -d
```

### Error: "Insufficient disk space"
```bash
# Limpiar imágenes Docker sin usar
docker image prune -a

# Limpiar volúmenes sin usar
docker volume prune

# Ver uso de disco
df -h
```

### Ver logs detallados de error
```bash
docker-compose logs web --tail=100  # Últimas 100 líneas
docker-compose logs web --follow    # En tiempo real
```

---

## 📊 Monitoreo

### Health check automático
```bash
# Docker ya verifica cada 30 segundos
# Ver estado:
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### CPU y memoria
```bash
docker stats
```

### Base de datos
```bash
docker-compose exec -T postgres psql -U malargue_user -d malargue_db -c "SELECT version();"
```

### Cache
```bash
docker-compose exec redis redis-cli ping
```

---

## 🔐 Security Checklist

- [ ] SECRET_KEY es único y seguro (50+ caracteres)
- [ ] DB_PASSWORD es único y seguro (32+ caracteres)
- [ ] REDIS_PASSWORD es único y seguro (32+ caracteres)
- [ ] DEBUG=False en .env
- [ ] ALLOWED_HOSTS solo tiene tu dominio
- [ ] Cloudflare está configurado en modo "Proxied"
- [ ] Firewall UFW habilitado (si es posible)
- [ ] SSH key configurada (sin password login)
- [ ] Backups automáticos configurados (cron)
- [ ] Monitoring configurado (Sentry opcional)

---

## 📈 Performance Tips

1. **Aumentar workers de Gunicorn:**
   ```bash
   # En gunicorn.conf.py:
   workers = (2 * cpu_count()) + 1  # Para más traffic
   ```

2. **Optimizar PostgreSQL:**
   ```sql
   -- Crear índices en campos que se usan mucho
   CREATE INDEX idx_field_name ON table_name(field_name);
   ```

3. **Cache static files:**
   - Cloudflare maneja esto automáticamente

4. **Usar Redis para sessions:**
   - Ya configurado en settings.py

---

## 📞 Emergency Recovery

**Si algo se rompe en producción:**

```bash
# 1. Ver logs
docker-compose logs web -n 100

# 2. Parar app
docker-compose down

# 3. Volver al último commit
git log --oneline -5
git checkout [commit_anterior]

# 4. Reiniciar
docker-compose up -d
docker-compose exec -T web python manage.py migrate
```

---

## ✅ Post-Deployment Checklist

- [ ] App accesible en `https://irrigacionmalargue.net`
- [ ] Admin login funciona
- [ ] Health check responde OK
- [ ] Logs sin errores
- [ ] Static files cargan correctamente
- [ ] Database conectada
- [ ] Redis conectado
- [ ] Backups configurados
- [ ] Monitoring configurado
- [ ] Team informado del deploy

---

**¡Listo! Tu app Malargue está en producción.** 🚀
