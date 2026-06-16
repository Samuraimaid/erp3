# Arquitectura del Sistema MC-LarenS ERP

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Cliente Web Browser                      │
│              http://localhost:3000 (HTTPS prod)              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTP/WebSocket
                             │
┌─────────────────────────────┴────────────────────────────────┐
│                   NGINX (Reverse Proxy)                      │
│              Port 3000 - Frontend Distribution               │
│    - Static files caching                                    │
│    - Proxy /api → Backend                                    │
│    - WebSocket proxying                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    │ HTTP API        │ WebSocket
                    │                 │
        ┌───────────▼──────┐   ┌──────▼────────┐
        │   FastAPI Backend │   │  WebSocket   │
        │  (Python 3.11)    │   │  Manager     │
        │  Port 8001        │   │              │
        │                   │   └──────┬───────┘
        │  ├─ Auth Routes   │          │
        │  ├─ API v1        │   (Real-time updates)
        │  ├─ Services      │
        │  └─ Middleware    │
        └────────┬──────────┘
                 │
        ┌────────▼──────────┐
        │  Async Motor ORM  │
        │  PyMongo Driver   │
        └────────┬──────────┘
                 │ TCP/27017
        ┌────────▼──────────┐
        │   MongoDB 7.0     │
        │   Port 27017      │
        │                   │
        │ ├─ admin          │
        │ ├─ mc-larens2_    │
        │ │  mundo_accesor. │
        │ │  _erp           │
        │ └─ [10 colecciones]
        └───────────────────┘
```

## Componentes

### 1. Frontend (React + Vite + Nginx)
- **Tecnología**: React 18, Vite, TypeScript
- **Container**: `mundo-frontend:updated-20260219`
- **Puerto**: 3000 (HTTP)
- **Runtime**: Nginx Alpine
- **Características**:
  - SPA (Single Page Application)
  - Gráficas y reportes interactivos
  - PWA (Progressive Web App)
  - Módulos:
    - Dashboard
    - Gestión de Ventas
    - Gestión de Clientes
    - Inventario
    - Recursos Humanos
    - Reportes

### 2. Backend (FastAPI Python)
- **Tecnología**: FastAPI, Python 3.11, Uvicorn
- **Container**: `mc-larenserp20-backend:updated-20260219`
- **Puerto**: 8001 (HTTP)
- **Características**:
  - REST API completa
  - WebSocket para tiempo real
  - Autenticación JWT + PIN
  - Rate limiting
  - CORS habilitado
  - Documentación Swagger/ReDoc integrada
  
**Módulos**:
- `api/v1/` - Rutas API versadas
- `core/` - Autenticación y seguridad
- `services/` - Lógica de negocio
- `models/` - Modelos de datos
- `routes/` - Rutas específicas
- `middlewares/` - Middleware personalizado
- `templates/` - Templates (emails, reportes)
- `tests/` - Suite de tests

### 3. Base de Datos (MongoDB)
- **Imagen**: `mongo:7.0`
- **Puerto**: 27017
- **Volumen**: `mongodb_data` (persistencia)
- **Database**: `mc-larens2_mundo_accesorios_erp`

**Colecciones**:
- `users` - Usuarios del sistema
- `customers` - Clientes
- `products` - Catálogo de productos
- `inventory` - Stock y movimientos
- `vehicles` - Vehículos de clientes
- `sales` - Ventas/Transacciones
- `sales_items` - Detalles de ventas
- `warehouses` - Almacenes
- `branches` - Sucursales
- `audit_logs` - Logs de auditoría
- `sessions` - Sesiones activas
- `notifications` - Notificaciones
- `approval_requests` - Solicitudes de aprobación
- `drafts` - Borradores de documentos

### 4. Networking
```
Network: mundo-network (bridge)
├── Backend: 172.22.0.2:8001
├── Frontend: 172.22.0.4:80
└── MongoDB: 172.22.0.3:27017
```

## Flujo de Datos

### 1. Autenticación
```
Cliente → Frontend → Backend (/api/v1/auth/login)
                      ↓
                   MongoDB (verificar usuario)
                      ↓
                   Backend (generar JWT)
                      ↓
Frontend (guardar token) → Almacenamiento local
```

### 2. Operación CRUD
```
Frontend → API Request (con JWT)
             ↓
Backend (validar token)
         ↓
         Middleware
         ↓
         Route handler
         ↓
         Service (lógica)
         ↓
         Motor ORM → MongoDB
         ↓
JSON Response → Frontend (render)
```

### 3. Actualizaciones en Tiempo Real
```
Backend (evento generado)
    ↓
WebSocket Manager
    ↓
Broadcast a clientes conectados
    ↓
Frontend (actualiza UI)
```

## Almacenamiento

### Volúmenes Docker
```
mongodb_data/          → Datos persistentes de MongoDB
mongodb_config/        → Configuración de MongoDB
```

### Backups
```
mongodb-backup/        → Dump de MongoDB (mongodump format)
                         Restaurable con mongorestore
```

## Seguridad

### Autenticación
- **JWT tokens**: Basados en email + PIN
- **PIN validation**: Longitud mínima 4 dígitos
- **Session timeout**: 24 horas

### Autorización
- **Roles**: admin, manager, usuario, invitado
- **RBAC**: Control basado en roles
- **Audit logging**: Todas las operaciones registradas

### CORS
```
Orígenes permitidos:
- http://127.0.0.1:3000
- http://localhost:3000
- http://127.0.0.1:8001
- http://localhost:8001
```

## Performance

### Caching
- Frontend: Cache busting con hash de assets
- Backend: Rate limiting (100 req/min)
- MongoDB: Índices en campos principales

### Escalabilidad
- Stateless backend (múltiples replicas posibles)
- WebSocket soporta múltiples conexiones
- MongoDB replica set ready

## Deployment

### Desarrollo
```bash
docker compose up -d
```

### Producción (cambios necesarios)
1. `COOKIE_SECURE=true`
2. `ENABLE_TEST_ENDPOINTS=false`
3. Certificados SSL/TLS
4. MongoDB con autenticación
5. Reverse proxy con Traefik/Nginx
6. Backups automáticos

## Monitoreo

### Health Checks
```bash
# Frontend
curl http://localhost:3000/health

# Backend
curl http://localhost:8001/health

# MongoDB
docker exec mclarens2-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Logs
```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f mongodb
```

### Métricas (opcional)
- Prometheus para métricas
- Grafana para visualización
- ELK stack para logs centralizados

## Troubleshooting

### Backend no conecta a MongoDB
```bash
docker exec mundo-backend curl mongodb:27017
docker network inspect mundo-network
```

### Frontend no ve el backend
```bash
# Verificar proxy en nginx.conf
# Verificar CORS en backend
curl -H "Origin: http://localhost:3000" http://localhost:8001
```

### MongoDB lleno
```bash
docker exec mclarens2-mongodb db.collection.deleteMany({})
docker volume prune
```

## Roadmap Futuro

- [ ] Autenticación OAuth2/Google
- [ ] Caché con Redis
- [ ] Search con Elasticsearch
- [ ] Notificaciones por email/SMS
- [ ] Mobile app nativa
- [ ] API GraphQL
- [ ] Machine Learning para pronósticos
- [ ] Integración ERP externo
