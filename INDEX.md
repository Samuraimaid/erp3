# MC-LarenS ERP - Índice de Archivos

Backup completo del stack de ERP MC-LarenS subido a GitHub.

## 📁 Estructura del Repositorio

### 📚 Documentación Principal
- **README.md** - Guía rápida, instalación y troubleshooting
- **ESTRUCTURA.md** - Descripción de carpetas del proyecto
- **ARCHITECTURE.md** - Arquitectura técnica, diagramas y flujos
- **API.md** - Documentación de endpoints REST
- **DEVELOPMENT.md** - Guía para desarrolladores

### 🐳 Configuración Docker
- **docker-compose.yml** - Orquestación de servicios (Backend, Frontend, MongoDB)
- **Dockerfile.backend** - Build del backend desde código fuente
- **Dockerfile.frontend** - Build del frontend desde archivos compilados
- **nginx.conf** - Configuración del servidor web Nginx
- **.env.example** - Plantilla de variables de entorno
- **.gitignore** - Archivos ignorados en Git

### 💾 Base de Datos
- **mongodb-backup/** - Dump completo restaurable de MongoDB
  - Contiene 13 colecciones con datos de producción
  - Restaurable con: `docker exec mclarens2-mongodb mongorestore /restore-backup`

### 🔧 Código Fuente Backend
- **backend-source/** - Código completo del backend FastAPI Python
  ```
  backend-source/
  ├── backend/
  │   ├── api/v1/              # Rutas API (Auth, Approvals, Reports, WebSocket)
  │   ├── core/                # Seguridad y autenticación
  │   ├── services/            # Lógica de negocio (Venta, Auditoría, PIN, etc)
  │   ├── models/              # Modelos Pydantic
  │   ├── routes/              # Rutas específicas (RRHH, Inventario)
  │   ├── middlewares/         # Middleware personalizado
  │   ├── data/                # Datos de seed y demo
  │   ├── db/                  # Sesiones MongoDB
  │   ├── templates/           # Templates HTML
  │   ├── tests/               # Suite de tests (9 archivos)
  │   ├── scripts/             # Scripts de utilidad
  │   ├── server.py            # Punto de entrada FastAPI
  │   └── entrypoint.sh        # Script de inicialización
  ├── requirements.txt         # Dependencias Python (125+)
  └── requirements.prod.txt    # Dependencias optimizadas para producción
  ```

- **backend-source-complete/** - Réplica completa del código del backend

### 🎨 Frontend Compilado
- **frontend-build/** - Frontend React compilado listo para producción
  ```
  frontend-build/
  ├── assets/                  # JavaScript y CSS compilados
  │   ├── [30+ módulos JS]    # Componentes compilados
  │   ├── fonts/              # Fuentes custom
  │   └── [CSS bundles]
  ├── index.html              # HTML principal
  ├── env.js                  # Variables de entorno runtime
  ├── manifest.json           # PWA manifest
  ├── sw.js                   # Service Worker
  ├── [logos]                 # Assets de branding
  └── tutorials/              # Tutoriales en SVG
  ```

### 🚀 Scripts de Utilidad
- **setup.sh** - Script de instalación y configuración inicial
- **restore.sh** - Script para restaurar stack completo desde backup
- **backup.sh** - Script para hacer backups automáticos

---

## 📊 Estadísticas del Proyecto

- **Archivos Python**: 80+
- **Tests**: 9 suites
- **Colecciones MongoDB**: 13
- **Endpoints API**: 50+
- **Módulos Frontend**: 35+
- **Dependencias Backend**: 125+
- **Tamaño DB Backup**: ~5MB

---

## 🚀 Quick Start

### Instalación en 1 línea
```bash
git clone https://github.com/Samuraimaid/erp3.git && cd erp3 && docker compose up -d && sleep 10 && docker exec mclarens2-mongodb mongorestore /restore-backup
```

### Acceso
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Swagger Docs**: http://localhost:8001/docs
- **MongoDB**: localhost:27017

### Credenciales Defecto
- **Email**: xinon@local
- **PIN**: 0101

---

## 📖 Guías por Rol

### Para Usuarios
1. Lee **README.md** - Guía rápida de inicio
2. Accede a http://localhost:3000
3. Usa credenciales por defecto

### Para Administradores
1. Lee **README.md** - Setup y operación
2. Lee **ARCHITECTURE.md** - Entender componentes
3. Ejecuta scripts en `setup.sh` o `restore.sh`

### Para Desarrolladores
1. Lee **DEVELOPMENT.md** - Ambiente de desarrollo
2. Lee **API.md** - Documentación de endpoints
3. Lee **ARCHITECTURE.md** - Diseño del sistema
4. Explora `backend-source/` para código

---

## 🔍 Contenido por Carpeta

| Carpeta | Contenido | Tamaño |
|---------|----------|--------|
| `backend-source/` | Código fuente Python backend | ~2MB |
| `backend-source-complete/` | Réplica de backend | ~2MB |
| `frontend-build/` | Frontend compilado | ~2.5MB |
| `mongodb-backup/` | Dump de BD | ~5MB |
| Documentos MD | Guías y documentación | ~50KB |
| Dockerfiles | Configuración Docker | ~5KB |
| **Total** | **Repositorio completo** | **~11MB** |

---

## 🔗 Enlaces Útiles

- [Repository](https://github.com/Samuraimaid/erp3)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [MongoDB Docs](https://docs.mongodb.com)
- [Docker Compose Docs](https://docs.docker.com/compose/)

---

## 📝 Notas Importantes

### ✅ Incluido en Backup
- ✓ Código fuente completo (Backend)
- ✓ Frontend compilado
- ✓ Base de datos (MongoDB dump)
- ✓ Dockerfiles para reconstruir
- ✓ Configuración nginx
- ✓ Variables de entorno ejemplo
- ✓ Scripts de setup, restore, backup
- ✓ Documentación completa (6 archivos .md)
- ✓ Tests unitarios e integración

### ❌ NO Incluido
- ✗ WhatsApp CRM (excluido por solicitud)
- ✗ Imágenes Docker .tar (se descargan automáticamente)
- ✗ Datos sensibles/secrets
- ✗ Código fuente del frontend (React - solo compilado)

---

## 🔐 Seguridad

### Cambios Necesarios para Producción
1. Cambiar `COOKIE_SECURE=true` en `.env`
2. Cambiar `ENABLE_TEST_ENDPOINTS=false`
3. Generar nuevos JWT secrets
4. Configurar MongoDB con autenticación
5. Usar certificados SSL/TLS válidos
6. Cambiar PIN y credenciales por defecto

---

## 📞 Contacto

**Repositorio**: https://github.com/Samuraimaid/erp3

**Información del Backup**
- Creado: 2026-06-16
- Stack: Python FastAPI + React + MongoDB
- Versión Backend: updated-20260219
- Versión Frontend: updated-20260219
- MongoDB: 7.0

---

**Última actualización**: 2026-06-16
