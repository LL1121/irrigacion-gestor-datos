# 🐳 DOCKER DEPLOYMENT - GUÍA RÁPIDA

## ✅ Archivos Creados/Modificados

### Estructura de Requerimientos
```
requirements/
├── base.txt        ← Dependencias principales
├── dev.txt         ← Dev + testing
└── prod.txt        ← Solo producción
requirements.txt    ← Root (importa base.txt)
```

### Docker Setup
```
Dockerfile              ← Build de la imagen (multi-stage)
docker-compose.yml      ← Orquestación de servicios (Django + PostgreSQL + Redis)
.dockerignore          ← Qué NO incluir en imagen
```

### Environment
```
.env.production        ← Plantilla para producción (NUNCA commit)
.env                   ← Copia local de .env.production (agregado a .gitignore)
```

### Deployment Scripts
```
docker-deploy.sh       ← Script de deployment + comandos útiles
DOCKER_DEPLOYMENT.md   ← Guía completa paso-a-paso
```

### Nginx (Opcional)
```
nginx-docker.conf      ← Config para si quieres Nginx en el futuro
```

---

## 🚀 DEPLOYMENT EN 5 MINUTOS

### 1. En el servidor
```bash
# SSH al servidor
ssh root@tu-ip-del-servidor

# Actualizar
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Clonar repo
cd /home
git clone https://github.com/tu-usuario/IrrigacionPetroleras.git
cd IrrigacionPetroleras
```

### 2. Configurar .env
```bash
# Copiar plantilla
cp .env.production .env

# Editar con valores reales
nano .env

# IMPORTANTE cambiar:
# - SECRET_KEY (generar con: python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
# - DB_PASSWORD (contraseña segura)
# - REDIS_PASSWORD (contraseña segura)
```

### 3. Deploy
```bash
# Hacer ejecutable
chmod +x docker-deploy.sh

# Ejecutar deploy
sudo bash docker-deploy.sh deploy

# Esperar ~30 segundos a que inicialice...

# Crear admin
docker-compose exec web python manage.py createsuperuser
```

### 4. Verificar
```bash
# Health check
curl http://localhost:8000/health/

# Ver logs
docker-compose logs web

# Acceder a https://irrigacionmalargue.net
```

### 5. Cloudflare
```
DNS Record:
- Type: A
- Name: @
- IPv4: [Tu IP del servidor]
- Proxy: Proxied (naranja)
```

---

## 📝 Estructura de Archivos

```
IrrigacionPetroleras/
├── requirements/
│   ├── base.txt              ← Deps base (Django, PostgreSQL, Redis, etc)
│   ├── dev.txt               ← + pytest, coverage, livereload
│   └── prod.txt              ← Solo base.txt
├── config/
│   ├── settings.py           ← Ya configurado para Docker
│   ├── wsgi.py
│   └── urls.py
├── web/
│   ├── views.py              ← Incluye health check
│   ├── urls.py
│   └── ...
├── Dockerfile                ← Multi-stage, 2GB final
├── docker-compose.yml        ← Django + PostgreSQL + Redis
├── .dockerignore              ← No subir __pycache__, .git, etc
├── .env.production            ← Plantilla (NUNCA commit)
├── .env                       ← Local (no commit)
├── .gitignore                 ← Ignora .env
├── docker-deploy.sh           ← Deploy script
├── DOCKER_DEPLOYMENT.md       ← Guía completa
├── nginx-docker.conf          ← Nginx config (opcional)
└── ...
```

---

## 🐳 Docker Compose Services

### PostgreSQL
```yaml
- Container: malargue_postgres
- Port: 5432 (interno, no expuesto a internet)
- Database: malargue_db
- User: malargue_user
- Password: (de .env)
- Volumen: postgres_data
```

### Redis
```yaml
- Container: malargue_redis
- Port: 6379 (interno, no expuesto a internet)
- Password: (de .env)
- Volumen: redis_data
```

### Django App
```yaml
- Container: malargue_app
- Port: 8000 (interno, expuesto a internet vía Nginx/Cloudflare)
- WSGI: Gunicorn
- Workers: Auto (cpu_count * 2 + 1)
```

---

## 🔐 Security

✅ Contraseñas seguras en .env (DB + Redis)  
✅ .env nunca se commitea (en .gitignore)  
✅ No hay credenciales en el Dockerfile  
✅ Usuario no-root en el contenedor (malargue:1000)  
✅ Ports: 8000 (app) únicamente expuesto  
✅ Cloudflare en frente (SSL, DDoS, rate limiting)  

---

## 📊 Volúmenes Docker

| Volumen | Contenedor | Propósito |
|---------|-----------|----------|
| `postgres_data` | PostgreSQL | Base de datos persistente |
| `redis_data` | Redis | Cache persistente |
| `./media` | Django | Fotos/archivos subidos |
| `./staticfiles` | Django | CSS/JS compilados |
| `./logs` | Django | Logs de app |

---

## 🔄 Comandos Frecuentes

```bash
# Ver estado
docker-compose ps
docker-compose logs web -n 50

# Reiniciar servicio
docker-compose restart web
docker-compose restart postgres
docker-compose restart redis

# Ejecutar comando Django
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Backup
docker-compose exec -T postgres pg_dump -U malargue_user malargue_db > backup.sql

# Actualizar código
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Ver logs tiempo real
docker-compose logs -f web
```

---

## 🎯 Next Steps

1. ✅ Archivos Docker creados
2. ✅ docker-deploy.sh listo
3. ✅ DOCKER_DEPLOYMENT.md con pasos detallados
4. ⏭️ Pushear a GitHub
5. ⏭️ En servidor: clonar + ejecutar docker-deploy.sh
6. ⏭️ Configurar Cloudflare DNS
7. ⏭️ ¡En producción!

---

## 💡 Pro Tips

- Las contraseñas en .env son solo para el deploy inicial
- Después puedes cambiarlas en el servidor sin rebuildar
- Docker hace que todo sea reproducible en cualquier servidor
- Health check (`/health/`) verifica que todo funciona

---

**Entendés? Todo listo para que lo hagas en el servidor.** ¿Querés que te ayude con algo específico del deployment?
