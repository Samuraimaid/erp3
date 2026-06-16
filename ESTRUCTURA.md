# 📂 ESTRUCTURA DEL REPOSITORIO

## Backend

```
/backend/
├── requirements.txt              # Dependencias Python
├── requirements.local.txt        # Dependencias locales
├── requirements.prod.txt         # Dependencias producción
├── Dockerfile                    # Imagen Docker del backend
├── .dockerignore                 # Archivos a excluir del build
├── entrypoint.sh                 # Script de inicio
├── main.py                       # Punto de entrada
├── server.py                     # Aplicación FastAPI
│
└── backend/                      # Código de la aplicación
    ├── api/
    │   └── v1/                   # Versión 1 de la API
    │       ├── approvals.py      # Endpoints de aprobaciones
    │       ├── auth.py           # Endpoints de autenticación
    │       ├── reports.py        # Endpoints de reportes
    │       └── websockets.py     # Websockets
    │
    ├── routes/
    │   ├── human_resources.py    # Rutas de RRHH
    │   └── inventory.py          # Rutas de inventario
    │
    ├── services/                 # Lógica de negocio
    │   ├── approval_service.py
    │   ├── audit.py
    │   ├── cash.py
    │   ├── pin_policy.py
    │   ├── token_cleanup.py
    │   ├── venta_service.py
    │   └── weekly_business_sentinel.py
    │
    ├── models/                   # Modelos de datos
    │   └── approval_request.py
    │
    ├── db/
    │   └── session.py            # Conexión a MongoDB
    │
    ├── core/
    │   ├── security.py           # Seguridad y autenticación
    │   └── websocket_manager.py  # Gestor de websockets
    │
    ├── middlewares/
    │   └── manager_pin.py        # Middleware de PIN
    │
    ├── data/
    │   ├── demo_products.py      # Datos de demostración
    │   ├── product_template.csv
    │   ├── drafts.json
    │   └── seeds/
    │       └── core_seed.json    # Seed de datos
    │
    ├── scripts/                  # Scripts útiles
    │   ├── add_vehicles_per_customer.py
    │   ├── check_customers_list.py
    │   ├── create_customers_validator.py
    │   ├── e2e_quick_approval.py
    │   ├── inspect_customers.py
    │   ├── mark_notification_read_and_check.py
    │   ├── migrate_customers_is_active.py
    │   ├── repro_trace_create_customer.py
    │   └── repro_users_pin.py
    │
    ├── tests/                    # Tests automatizados
    │   ├── test_bug_fixes_iteration7.py
    │   ├── test_csv_import_installation.py
    │   ├── test_customer_integration.py
    │   ├── test_p1_features.py
    │   ├── test_pin_integration.py
    │   ├── test_pin_lockout.py
    │   ├── test_pin_qc_compatibility.py
    │   ├── test_pin_validation.py
    │   └── test_technicians_crud.py
    │
    ├── templates/
    │   └── invoice.html          # Template de factura
    │
    └── (otros archivos)
```

## Frontend

```
/frontend/
├── package.json                  # Dependencias Node.js
├── package-lock.json
├── vite.config.js                # Config de Vite
├── Dockerfile                    # Imagen Docker del frontend
├── nginx.conf                    # Config de Nginx
│
└── src/                          # Código React
    ├── App.jsx
    ├── main.jsx
    ├── components/               # Componentes React
    ├── pages/                    # Páginas
    ├── services/                 # Servicios API
    ├── hooks/                    # Hooks personalizados
    ├── utils/                    # Utilidades
    ├── styles/                   # Estilos
    └── assets/                   # Imágenes y assets
```

## Configuración Docker

```
/
├── docker-compose.yml            # Stack principal (puertos 3000, 8001, 27017)
├── docker-compose.no-conflict.yml # Stack GitHub (puertos 3002, 8003, 27019)
├── Dockerfile.backend            # Build del backend
├── Dockerfile.frontend           # Build del frontend
└── nginx.conf                    # Config reverse proxy
```

## Base de Datos

```
/mongodb-backup/
└── mc-larens2_mundo_accesorios_erp/
    ├── branches.bson
    ├── customers.bson
    ├── inventory.bson
    ├── products.bson
    ├── users.bson
    ├── vehicles.bson
    ├── sales.bson
    ├── audit_logs.bson
    ├── notifications.bson
    ├── pin_auth_logs.bson
    ├── hypervisor_events.bson
    ├── sessions.bson
    ├── dispatch_orders.bson
    ├── inventory_movements.bson
    ├── manager_authorizations.bson
    ├── exchange_rates.bson
    ├── price_history.bson
    ├── push_subscriptions.bson
    ├── settings.bson
    ├── user_draft_state.bson
    ├── user_drafts.bson
    ├── warehouses.bson
    ├── approval_requests.bson
    ├── drafts_backup.bson
    ├── hr_runtime_meta.bson
    ├── sample_requests.bson
    └── [archivos .metadata.json]
```

## Documentación

```
/
├── README.md                     # Introducción general
├── SETUP_COMPLETO.md             # Guía completa de instalación
├── LEVANTAR_SIN_CONFLICTOS.md    # Cómo levantar 3 stacks sin conflictos
├── COMANDOS_RAPIDOS.md           # Comandos listos para copiar
├── RESUMEN_EJECUTIVO.md          # Resumen ejecutivo
├── ARQUITECTURA.md               # Descripción de la arquitectura
├── API.md                        # Documentación de API endpoints
├── DEVELOPMENT.md                # Guía para desarrolladores
└── ESTRUCTURA.md                 # Este archivo
```

## Scripts

```
/
├── setup-auto.bat                # Setup automático (Windows)
├── setup-no-conflicts.ps1        # Setup sin conflictos (PowerShell)
├── backup.sh                     # Script de backup
└── restore.sh                    # Script de restauración
```

## Configuración

```
/
├── .env.example                  # Variables de entorno (ejemplo)
└── .gitignore                    # Archivos ignorados por Git
```

---

## 📍 Ubicación de archivos principales

| Archivo/Carpeta | Ubicación | Descripción |
|-----------------|-----------|-------------|
| API FastAPI | `/backend/server.py` | Servidor principal de la API |
| Rutas RRHH | `/backend/backend/routes/human_resources.py` | Endpoints de recursos humanos |
| Rutas Inventario | `/backend/backend/routes/inventory.py` | Endpoints de inventario |
| Frontend React | `/frontend/src/` | Código del interfaz de usuario |
| DB Dump | `/mongodb-backup/` | Respaldo completo de MongoDB |
| Config Docker | `/docker-compose.yml` | Configuración de servicios |
| Tests | `/backend/backend/tests/` | Tests automatizados |
| Seeds/Datos | `/backend/backend/data/seeds/` | Datos iniciales |

---

## 🚀 Para editar en VSCode

```powershell
code C:\tmp\erp3
```

**Carpetas principales a conocer:**

1. **Backend Python:**
   - `backend/server.py` — Archivo principal de la API
   - `backend/backend/routes/` — Endpoints
   - `backend/backend/services/` — Lógica de negocio
   - `backend/backend/models/` — Esquemas de datos

2. **Frontend React:**
   - `frontend/src/App.jsx` — Componente principal
   - `frontend/src/components/` — Componentes reutilizables
   - `frontend/src/pages/` — Páginas/vistas
   - `frontend/src/services/` — Llamadas a API

3. **Docker & Config:**
   - `docker-compose.yml` — Stack principal
   - `docker-compose.no-conflict.yml` — Stack alternativo
   - `Dockerfile.backend` y `Dockerfile.frontend` — Builds

