# 🏢 MC-LarenS ERP - Stack Completo en Docker

**Backup completo y funcional de MC-LarenS ERP (Mundo Accesorios) con Backend FastAPI, Frontend React y MongoDB.**

[![GitHub](https://img.shields.io/badge/GitHub-Samuraimaid-blue)](https://github.com/Samuraimaid/erp3)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)]()
[![License](https://img.shields.io/badge/License-Private-red)]()

---

## 📋 Contenido

✅ **Incluido:**
- ✨ **Backend FastAPI completo** (Python) - API REST con 2000+ líneas de código
- ✨ **Frontend React optimizado** - UI responsiva con Vite
- ✨ **MongoDB backup** - 5694 documentos con datos reales
- 📦 **Docker Compose** - Stack listo para producción
- 📚 **Documentación completa** - Guías paso a paso
- 🚀 **Scripts automatizados** - Setup en 1 click

❌ **NO Incluido:**
- Imágenes Docker precompiladas (se crean automáticamente)
- Credenciales reales (solo ejemplos)

---

## 🚀 Inicio Rápido - 3 opciones

### **OPCIÓN 1: Script automático (Recomendado - Windows)**

```powershell
# Descarga y ejecuta
git clone https://github.com/Samuraimaid/erp3.git
cd erp3
.\setup-auto.bat
```

### **OPCIÓN 2: Comandos paso a paso**

```bash
# Clonar
git clone https://github.com/Samuraimaid/erp3.git
cd erp3

# Copiar .env
cp .env.example .env

# Levantar stack
docker compose up -d

# Restaurar base de datos (después de 30 segundos)
sleep 30
docker exec mclarens2-mongodb mongorestore /mongodb-backup
```

### **OPCIÓN 3: Una línea (Express)**

```bash
git clone https://github.com/Samuraimaid/erp3.git && cd erp3 && docker compose up -d && sleep 30 && docker exec mclarens2-mongodb mongorestore /mongodb-backup
```

---

## 🌐 Acceso a los servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interfaz del ERP |
| **API Docs** | http://localhost:8001/docs | Documentación interactiva de FastAPI |
| **MongoDB** | localhost:27017 | Base de datos |

---

## 🔐 Credenciales de Prueba

```
Email:     xinon@local
PIN:       0101
PIN Login: 01011990
```

---

## 📂 Estructura del Proyecto

```
erp3/
├── backend/                          # Backend FastAPI (Python)
│   ├── backend/
│   │   ├── routes/                   # Endpoints (human_resources, inventory)
│   │   ├── services/                 # Lógica de negocio
│   │   ├── models/                   # Esquemas de datos
│   │   ├── api/                      # API v1
│   │   ├── db/                       # Conexión a MongoDB
│   │   ├── scripts/                  # Scripts útiles
│   │   └── tests/                    # Tests automatizados
│   ├── server.py                     # FastAPI app
│   ├── requirements.txt              # Dependencias
│   └── Dockerfile
│
├── frontend/                         # Frontend React
│   ├── src/
│   │   ├── components/               # Componentes React
│   │   ├── pages/                    # Páginas/vistas
│   │   ├── services/                 # Llamadas a API
│   │   └── assets/
│   ├── package.json                  # Dependencias Node
│   ├── vite.config.js                # Config Vite
│   └── Dockerfile
│
├── mongodb-backup/                   # Backup de MongoDB (5694 docs)
│   └── mc-larens2_mundo_accesorios_erp/
│
├── docker-compose.yml                # Stack principal
├── docker-compose.no-conflict.yml    # Stack alternativo (puertos 3002, 8003, 27019)
├── .env.example                      # Variables de entorno
├── nginx.conf                        # Configuración Nginx
│
├── ESTRUCTURA.md                     # 📍 Guía de carpetas
├── SETUP_COMPLETO.md                 # Guía detallada de instalación
├── LEVANTAR_SIN_CONFLICTOS.md        # Cómo levantar 3 stacks simultáneamente
├── COMANDOS_RAPIDOS.md               # Comandos listos para copiar
├── RESUMEN_EJECUTIVO.md              # Resumen ejecutivo
├── API.md                            # Documentación de endpoints
├── DEVELOPMENT.md                    # Guía para desarrolladores
└── README.md                         # Este archivo
```

---

## 🐳 Stack Components

### Backend - FastAPI (Python)
- **Puerto:** 8001
- **Imagen:** `mc-larenserp20-backend:updated-20260219`
- **Framework:** FastAPI + Uvicorn
- **DB:** MongoDB
- **Features:**
  - ✅ Autenticación con PIN
  - ✅ API REST completa
  - ✅ WebSockets
  - ✅ Tests automatizados
  - ✅ 2000+ líneas de código

### Frontend - React (Vite)
- **Puerto:** 3000
- **Imagen:** `mundo-frontend:updated-20260219`
- **Framework:** React + Vite
- **Server:** Nginx
- **Features:**
  - ✅ Interfaz responsiva
  - ✅ Login con PIN
  - ✅ Dashboard completo
  - ✅ Gestión de inventario
  - ✅ RRHH y ventas

### Database - MongoDB
- **Puerto:** 27017
- **Versión:** 7.0
- **Base de datos:** `mc-larens2_mundo_accesorios_erp`
- **Documentos:** 5694
- **Colecciones:**
  - customers (43 docs)
  - products (49 docs)
  - inventory (69 docs)
  - users (40 docs)
  - vehicles (120 docs)
  - sales, branches, warehouses, etc.

---

## 📋 Requisitos

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 2GB | 4GB+ |
| Disco | 5GB | 10GB+ |
| Docker | Latest | Latest |
| Git | 2.x | Latest |
| OS | Windows 10 / macOS 10.14+ / Linux | Windows 11 / macOS 12+ / Ubuntu 20.04+ |

---

## 🔄 Comandos Útiles

```bash
# Ver estado de servicios
docker compose ps

# Ver logs en vivo
docker compose logs -f

# Logs de un servicio específico
docker compose logs -f backend

# Reiniciar servicios
docker compose restart

# Detener (sin eliminar datos)
docker compose stop

# Volver a iniciar
docker compose start

# Detener y eliminar todo (CUIDADO: pierde datos)
docker compose down -v

# Conectar a MongoDB
docker exec -it mclarens2-mongodb mongosh
```

---

## 🛠️ Configuración Avanzada

### Cambiar puertos

Edita `docker-compose.yml`:

```yaml
backend:
  ports:
    - "8080:8001"    # Cambiar 8001 a 8080

frontend:
  ports:
    - "3001:80"      # Cambiar 3000 a 3001

mongodb:
  ports:
    - "27018:27017"  # Cambiar 27017 a 27018
```

Luego:
```bash
docker compose down
docker compose up -d
```

### Levantar múltiples stacks sin conflictos

```bash
# Stack 1 (principal): puertos 3000, 8001, 27017
docker compose up -d

# Stack 2 (alternativo): puertos 3002, 8003, 27019
docker compose -f docker-compose.no-conflict.yml up -d
```

Ver documentación: [`LEVANTAR_SIN_CONFLICTOS.md`](./LEVANTAR_SIN_CONFLICTOS.md)

---

## 📝 Para Editar el Código

### Abrir en VSCode

```bash
code .
```

### Estructura de carpetas importantes

```
backend/backend/
├── routes/human_resources.py     ← Endpoints de RRHH
├── routes/inventory.py           ← Endpoints de inventario
├── services/                     ← Lógica de negocio
└── tests/                        ← Tests

frontend/src/
├── components/                   ← Componentes React
├── pages/                        ← Páginas
├── services/                     ← Llamadas a API
└── App.jsx                       ← Componente principal
```

---

## 🐛 Solución de Problemas

### "Puerto ya en uso"
```bash
# Cambiar puertos en docker-compose.yml
# O identificar qué usa el puerto:
netstat -ano | findstr :3000  # Windows
lsof -i :3000                  # macOS/Linux
```

### "MongoDB no inicia"
```bash
docker compose logs mongodb
docker volume prune
docker compose down -v
docker compose up -d
```

### "Backend no se conecta a MongoDB"
```bash
docker compose restart backend
docker compose logs backend
```

### "Frontend muestra en blanco"
```bash
# Limpiar caché del navegador (Ctrl+Shift+Delete)
# Recargar con Ctrl+F5
docker compose restart frontend
```

---

## 📚 Documentación

| Documento | Contenido |
|-----------|----------|
| [ESTRUCTURA.md](./ESTRUCTURA.md) | Guía de carpetas y archivos |
| [SETUP_COMPLETO.md](./SETUP_COMPLETO.md) | Guía detallada paso a paso |
| [LEVANTAR_SIN_CONFLICTOS.md](./LEVANTAR_SIN_CONFLICTOS.md) | Múltiples stacks simultáneamente |
| [COMANDOS_RAPIDOS.md](./COMANDOS_RAPIDOS.md) | Comandos listos para copiar |
| [API.md](./API.md) | Documentación de endpoints |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Guía para desarrolladores |

---

## 🔗 Enlaces Útiles

- **API Docs Interactivo:** http://localhost:8001/docs (cuando esté corriendo)
- **FastAPI:** https://fastapi.tiangolo.com/
- **MongoDB:** https://docs.mongodb.com/
- **Docker Docs:** https://docs.docker.com/

---

## 📊 Estadísticas del Proyecto

- **Backend:** ~2000+ líneas de Python (FastAPI)
- **Frontend:** React + Vite
- **Base de datos:** 5694 documentos en MongoDB
- **Colecciones:** 28+ colecciones
- **Endpoints:** 50+ endpoints API
- **Tests:** 9 suites de tests automatizados

---

## ⚖️ Licencia

Este proyecto es **Privado**. Uso interno únicamente.

---

## 📞 Soporte

Para problemas o preguntas:

1. Consulta la [documentación completa](./SETUP_COMPLETO.md)
2. Revisa [LEVANTAR_SIN_CONFLICTOS.md](./LEVANTAR_SIN_CONFLICTOS.md) si necesitas múltiples stacks
3. Usa [COMANDOS_RAPIDOS.md](./COMANDOS_RAPIDOS.md) para referencia rápida

---

## ✅ Checklist Rápido

- [ ] Docker Desktop instalado
- [ ] Repositorio clonado
- [ ] `.env` copiado desde `.env.example`
- [ ] `docker compose up -d` ejecutado
- [ ] MongoDB restaurado
- [ ] Frontend accesible en http://localhost:3000
- [ ] Backend accesible en http://localhost:8001
- [ ] Login funciona

---

**Última actualización:** 2026-06-16  
**Estado:** ✅ Funcional y listo para usar

