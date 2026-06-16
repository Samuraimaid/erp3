# MC-LarenS ERP Stack Backup

Backup completo de la base de datos y configuración del MC-LarenS ERP (Mundo Accesorios).

## ⚠️ Contenido del Backup

✅ **Incluido:**
- `docker-compose.yml` - Configuración de servicios
- `mongodb-backup/` - Dump completo de la base de datos MongoDB
- Instrucciones de restauración

❌ **NO Incluido:**
- Imágenes Docker (`.tar` files) - Se descargan automáticamente desde la máquina donde se ejecuta
- WhatsApp CRM (excluido por solicitud)

## Estructura

```
erp-stack-backup/
├── docker-compose.yml      # Configuración de servicios
├── mongodb-backup/         # Dump de MongoDB con todos los datos
├── restore.sh             # Script para restaurar stack
├── backup.sh              # Script para hacer backups
└── README.md              # Este archivo
```

## Stack Components

### MongoDB 7.0
- Database: `mc-larens2_mundo_accesorios_erp`
- Puerto: 27017
- Colecciones: products, customers, inventory, vehicles, users, etc.

### Backend (FastAPI Python)
- Image: `mc-larenserp20-backend:updated-20260219`
- Puerto: 8001
- Entrypoint: `uvicorn backend.server:app`
- Dependencia: MongoDB

### Frontend (React + Nginx)
- Image: `mundo-frontend:updated-20260219`
- Puerto: 3000
- Reverse proxy: Nginx
- Dependencia: Backend

## Requisitos

- Docker Engine (latest)
- Docker Compose v2.x
- 2GB+ RAM disponible
- 5GB+ espacio en disco

## Instalación & Restauración

### Opción 1: Restaurar desde el backup

```bash
# 1. Clonar el repositorio
git clone https://github.com/Samuraimaid/erp3.git
cd erp3

# 2. Asegúrate de tener las imágenes Docker (si no están en local, Docker las descargará)
# Las imágenes se usan como están, si no existen se construirán

# 3. Restaurar stack completo (requiere script bash)
bash restore.sh

# O manualmente:
docker compose up -d
sleep 10
docker exec mclarens2-mongodb mongorestore /restore-backup
```

### Opción 2: Fresh start sin datos

```bash
# Solo inicia los servicios sin restaurar datos previos
docker compose up -d
```

## Verificación

### Servicios en ejecución
```bash
docker compose ps
```

### Logs
```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb
```

### Acceso a servicios

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8001 |
| MongoDB | localhost:27017 |

### Conectar a MongoDB
```bash
docker exec -it mclarens2-mongodb mongosh
use mc-larens2_mundo_accesorios_erp
show collections
```

## Datos de Acceso (si aplica)

Configura en `docker-compose.yml`:
- PIN Usuario: `0101`
- PIN Acceso: `01011990`
- Email: `xinon@local`

## Hacer Backup Nuevo

```bash
# Exportar base de datos
docker exec mclarens2-mongodb mongodump --out /dump
docker cp mclarens2-mongodb:/dump ./mongodb-backup

# Limpiar
docker exec mclarens2-mongodb rm -rf /dump
```

## Detener Stack

```bash
docker compose down
```

## Detener y eliminar volúmenes

```bash
docker compose down -v
```

## Troubleshooting

### Contenedor MongoDB no inicia
```bash
docker compose logs mongodb
docker volume prune  # Limpiar volúmenes huérfanos
```

### Error de conexión Backend -> MongoDB
```bash
# Verificar red
docker network inspect erp-stack-backup_mundo-network

# Reiniciar servicios
docker compose restart
```

### Puerto ya en uso
```bash
# Cambiar puerto en docker-compose.yml
# De: "8001:8001"
# A:  "8080:8001"
```

### Memoria insuficiente
```bash
docker compose down
# Aumentar memoria asignada a Docker Desktop
docker compose up -d
```

## Notas Importantes

⚠️ **Seguridad:**
- Cambiar contraseñas y secrets antes de producción
- No compartir este backup sin encriptar
- Usar `.env` file en producción, no hardcoded values

⚠️ **Rendimiento:**
- MongoDB consume ~500MB RAM
- Backend consume ~300MB RAM
- Frontend consume ~100MB
- Total mínimo: 1GB RAM

## Soporte

Para obtener más información sobre los servicios:
- FastAPI docs: http://localhost:8001/docs
- MongoDB: https://docs.mongodb.com/

---

Último backup: 2026-06-16
