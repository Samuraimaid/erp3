# 🚀 SETUP COMPLETO - MC-LARENS ERP EN OTRO PC

## ¿Qué contiene este repositorio?

✅ **Todo lo que necesitas:**
- `backend-source/` - Código fuente del backend FastAPI (Python)
- `frontend-build/` - Frontend React compilado
- `mongodb-backup/` - Datos completos de MongoDB (BD del ERP)
- `docker-compose.yml` - Configuración de los 3 servicios
- `Dockerfile.backend` y `Dockerfile.frontend` - Instrucciones para buildear imágenes
- `.env.example` - Variables de entorno de ejemplo

❌ **No contiene:**
- Imágenes Docker precompiladas (se crean automáticamente)
- Credenciales reales (solo ejemplos en `.env.example`)

---

## 📋 PASO 1: REQUISITOS

En el PC donde quieres restaurar el ERP:

1. **Docker Desktop instalado**
   - Windows: https://www.docker.com/products/docker-desktop
   - macOS: https://www.docker.com/products/docker-desktop
   - Linux: `sudo apt-get install docker.io docker-compose`

2. **Git instalado**
   - Windows/macOS: https://git-scm.com/downloads
   - Linux: `sudo apt-get install git`

3. **Al menos 5GB de espacio libre en disco**

4. **Ram mínimo: 2GB (recomendado: 4GB+)**

---

## 🔧 PASO 2: CLONAR EL REPOSITORIO

En PowerShell, CMD o Terminal:

```powershell
# Ir a la carpeta donde quieres el proyecto
cd C:\  # o tu ruta preferida

# Clonar el repositorio
git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP

# Entrar a la carpeta
cd MC-LARENS-ERP

# Ver lo que se clonó
dir   # En Windows
# ls    # En macOS/Linux
```

---

## ⚙️ PASO 3: CONFIGURAR VARIABLES DE ENTORNO

```powershell
# Copiar el archivo de ejemplo
Copy-Item .env.example .env

# Editar .env (opcional, los valores por defecto funcionan)
# Si necesitas cambiar puertos, URLs, etc., edita el archivo
```

---

## 🐳 PASO 4: CONSTRUIR LAS IMÁGENES DOCKER

```powershell
# Buildear las imágenes del backend y frontend
docker compose build

# Esto tomará 10-15 minutos la primera vez
# (descarga dependencias de Python/Node)
```

---

## ▶️ PASO 5: INICIAR EL STACK

```powershell
# Levanta todos los servicios
docker compose up -d

# Espera ~30 segundos para que se inicien
Start-Sleep -Seconds 30

# Verifica que estén corriendo
docker compose ps

# Deberías ver 3 contenedores: mongodb, backend, frontend (todos "Up")
```

---

## 📦 PASO 6: RESTAURAR LOS DATOS DE MONGODB

```powershell
# Ver si MongoDB está listo
docker compose logs mongodb | Select-String "waiting for connections"

# Una vez que veas ese mensaje, restaura los datos
docker exec mclarens2-mongodb mongorestore /mongodb-backup

# Esto restaura TODOS los datos históricos del ERP
# (puede tardar 1-5 minutos según la cantidad de datos)
```

---

## ✅ PASO 7: VERIFICAR QUE TODO FUNCIONA

### Ver logs
```powershell
# Logs de todos los servicios
docker compose logs

# Logs de un servicio específico
docker compose logs backend
docker compose logs frontend
docker compose logs mongodb
```

### Acceder a los servicios

Abre en tu navegador:

| Servicio | URL |
|----------|-----|
| **Frontend ERP** | http://localhost:3000 |
| **Backend API Docs** | http://localhost:8001/docs |
| **MongoDB** | localhost:27017 |

### Probar el backend
```powershell
# Test de conexión rápido
curl http://localhost:8001/docs

# O en PowerShell
(Invoke-WebRequest http://localhost:8001/docs).StatusCode
# Deberías ver: 200
```

---

## 🔐 PASO 8: CREDENCIALES DE ACCESO

Si el ERP tiene login, usa:

```
Email:     xinon@local
PIN:       0101
PIN Login: 01011990
```

*Cambialos en producción - no uses estos datos en un servidor público*

---

## 📝 CONFIGURACIÓN AVANZADA

### Cambiar puertos

Si los puertos 3000, 8001 o 27017 ya están en uso:

Edita `docker-compose.yml`:
```yaml
# Frontend (cambiar primer número)
ports:
  - "3000:80"    # Cambiar 3000 a otro puerto
  
# Backend (cambiar primer número)
ports:
  - "8001:8001"  # Cambiar 8001 a otro puerto
  
# MongoDB (cambiar primer número)
ports:
  - "27017:27017" # Cambiar 27017 a otro puerto
```

Luego:
```powershell
docker compose down
docker compose up -d
```

### Variables de entorno personalizadas

Edita el archivo `.env`:
```
MONGO_URL=mongodb://mongodb:27017
DB_NAME=mc-larens2_mundo_accesorios_erp
DEFAULT_PIN_USER_PIN=0101
DEFAULT_LOGIN_PIN_USER_PIN=01011990
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

---

## 🛠️ COMANDOS ÚTILES

```powershell
# Ver estado de servicios
docker compose ps

# Ver logs en vivo
docker compose logs -f

# Detener servicios (sin eliminar datos)
docker compose stop

# Reiniciar servicios
docker compose restart

# Detener y eliminar todo (CUIDADO: pierde datos en volúmenes)
docker compose down -v

# Ver volúmenes (donde se guardan los datos)
docker volume ls

# Conectar a MongoDB desde la terminal
docker exec -it mclarens2-mongodb mongosh

# Hacer un nuevo backup de MongoDB
docker exec mclarens2-mongodb mongodump --out /backup
docker cp mclarens2-mongodb:/backup ./mongodb-backup-nuevo
docker exec mclarens2-mongodb rm -rf /backup
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### "Puerto ya en uso"
```powershell
# Ver qué proceso usa el puerto (Windows)
netstat -ano | findstr :3000
# Cambiar en docker-compose.yml o hacer que libere el puerto
```

### "MongoDB no inicia"
```powershell
# Ver logs
docker compose logs mongodb

# Limpiar volúmenes huérfanos
docker volume prune

# Reintentar
docker compose down -v
docker compose up -d
```

### "Backend no se conecta a MongoDB"
```powershell
# Reiniciar el backend
docker compose restart backend

# Ver logs detallados
docker compose logs backend
```

### "Frontend muestra en blanco / error"
```powershell
# Reiniciar frontend
docker compose restart frontend

# Limpiar caché del navegador (Ctrl+Shift+Delete)
# Recargar página (Ctrl+F5)
```

### "Memoria insuficiente"
```powershell
# Detener otros contenedores
docker ps -a
docker stop [container-id]

# O aumentar RAM en Docker Desktop:
# Configuración > Resources > Memory: aumentar a 4GB+
```

---

## 📊 MONITOREO

Ver consumo de recursos:
```powershell
docker stats
```

Ver inspección detallada de un contenedor:
```powershell
docker inspect mundo-backend
docker inspect mclarens2-mongodb
docker inspect mundo-frontend
```

---

## 🔄 ACTUALIZAR EL REPOSITORIO

Si hay cambios en GitHub:

```powershell
cd C:\MC-LARENS-ERP
git pull origin main

# Rebuild de imágenes si cambió el código
docker compose build

# Reiniciar servicios
docker compose down
docker compose up -d
```

---

## 📞 SOPORTE

- **Documentación adicional:** Ver archivos `.md` en el repositorio
- **API Docs interactivo:** http://localhost:8001/docs (cuando el backend esté corriendo)
- **MongoDB Docs:** https://docs.mongodb.com/

---

## ✔️ CHECKLIST FINAL

- [ ] Docker Desktop instalado y corriendo
- [ ] Repositorio clonado (`git clone`)
- [ ] Archivo `.env` copiado desde `.env.example`
- [ ] Imágenes construidas (`docker compose build`)
- [ ] Stack iniciado (`docker compose up -d`)
- [ ] MongoDB restaurado (`mongorestore`)
- [ ] Frontend accesible en http://localhost:3000
- [ ] Backend accesible en http://localhost:8001
- [ ] Login funciona con credenciales de prueba
- [ ] Datos del ERP visibles en frontend

---

**¡Listo! Tu ERP está corriendo. Accede a http://localhost:3000**

