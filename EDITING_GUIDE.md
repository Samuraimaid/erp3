# 🔧 GUÍA DE EDICIÓN - VSCode

## 📁 Cómo abrir el proyecto en VSCode

```powershell
# Abre VSCode en la carpeta del proyecto
code C:\tmp\erp3
```

---

## 📂 Estructura de carpetas para editar

Una vez que abras VSCode, verás:

```
erp3/
├── backend/                          ← Backend Python
│   └── backend/
│       ├── routes/                   ← ⭐ Endpoints (editar aquí)
│       │   ├── human_resources.py    ← Rutas RRHH
│       │   └── inventory.py          ← Rutas Inventario
│       ├── services/                 ← Lógica de negocio
│       ├── models/                   ← Esquemas
│       ├── tests/                    ← Tests
│       └── server.py                 ← API principal
│
├── frontend/                         ← Frontend React
│   └── src/
│       ├── components/               ← ⭐ Componentes React
│       ├── pages/                    ← Páginas
│       ├── services/                 ← Llamadas API
│       └── App.jsx                   ← Componente principal
│
└── [Archivos de config]
```

---

## 🚀 Tareas comunes

### 1️⃣ Editar un endpoint del Backend

**Ejemplo: Agregar un nuevo endpoint en Human Resources**

1. Abre: `backend/backend/routes/human_resources.py`
2. Busca la función que quieres editar o agrega una nueva
3. Guarda (Ctrl+S)
4. Reinicia el backend:
   ```bash
   docker compose restart backend
   ```
5. Prueba en: http://localhost:8001/docs

### 2️⃣ Editar un componente del Frontend

**Ejemplo: Cambiar el Dashboard**

1. Abre: `frontend/src/pages/` (encuentra el archivo)
2. O abre: `frontend/src/components/` (para componentes específicos)
3. Edita el código React
4. Guarda (Ctrl+S)
5. El frontend se recarga automáticamente en el navegador

### 3️⃣ Editar la lógica de negocio

**Ejemplo: Cambiar reglas de inventario**

1. Abre: `backend/backend/services/` 
2. Edita el archivo correspondiente
3. Guarda y reinicia:
   ```bash
   docker compose restart backend
   ```

### 4️⃣ Agregar una nueva ruta/endpoint

1. Abre: `backend/backend/routes/` (elegir o crear archivo)
2. Agrega tu función con decorador `@router.get()` o `@router.post()`
3. Ejemplo:
   ```python
   @router.get("/new-endpoint")
   async def get_new_data():
       return {"message": "Hello"}
   ```
4. Guarda y reinicia backend
5. Prueba en http://localhost:8001/docs

---

## 🎯 Archivos importantes por tarea

| Tarea | Archivo | Ruta |
|-------|---------|------|
| Agregar endpoint RRHH | `human_resources.py` | `backend/backend/routes/` |
| Agregar endpoint Inventario | `inventory.py` | `backend/backend/routes/` |
| Cambiar lógica de datos | Servicios | `backend/backend/services/` |
| Editar esquema de datos | Modelos | `backend/backend/models/` |
| Cambiar UI | Componentes | `frontend/src/components/` |
| Cambiar página | Páginas | `frontend/src/pages/` |
| Cambiar llamadas API | Servicios | `frontend/src/services/` |
| Agregar test | Tests | `backend/backend/tests/` |

---

## 💡 Tips en VSCode

### Extensiones recomendadas

Instala estas extensiones en VSCode:

1. **Python**
   - Publisher: Microsoft
   - Ayuda a editar Python

2. **FastAPI**
   - Publisher: Pycln/Sourcery
   - Soporte para FastAPI

3. **Pylint**
   - Para validar código Python

4. **ES7+ React/Redux/React-Native snippets**
   - Para React

5. **Prettier**
   - Formateador de código

### Búsqueda rápida

```
Ctrl+P   → Buscar archivos por nombre
Ctrl+F   → Buscar en archivo actual
Ctrl+H   → Buscar y reemplazar
Ctrl+/   → Comentar/descomentar línea
```

### Debugging

Para debuguear el backend:

1. Abre VSCode
2. Ve a Run > Add Configuration
3. Elige "Python"
4. Selecciona "FastAPI" o "Python"
5. Ejecuta: F5

---

## 📝 Flujo de edición típico

### Backend (Python)

```
1. Edita archivo en backend/backend/routes/
   ↓
2. Guarda (Ctrl+S)
   ↓
3. En terminal: docker compose restart backend
   ↓
4. Prueba en http://localhost:8001/docs
   ↓
5. Si está bien, haz commit y push a Git
```

### Frontend (React)

```
1. Edita archivo en frontend/src/
   ↓
2. Guarda (Ctrl+S)
   ↓
3. El navegador se recarga automáticamente
   ↓
4. Prueba en http://localhost:3000
   ↓
5. Si está bien, haz commit y push a Git
```

---

## 🔄 Actualizar desde GitHub

Si alguien hizo cambios en GitHub:

```bash
git pull origin main
docker compose restart
```

---

## 📊 Estructura de carpetas detallada

### Backend

```
backend/
├── server.py                    ← Archivo principal FastAPI
├── requirements.txt             ← Dependencias Python
├── Dockerfile                   ← Build del backend
├── entrypoint.sh                ← Script de inicio
│
└── backend/                     ← Código de la app
    ├── routes/
    │   ├── human_resources.py   ← 80KB - Rutas RRHH (80+ endpoints)
    │   ├── inventory.py         ← 33KB - Rutas Inventario
    │   └── __init__.py
    │
    ├── services/                ← Lógica de negocio
    │   ├── approval_service.py
    │   ├── audit.py
    │   ├── cash.py
    │   ├── pin_policy.py
    │   ├── token_cleanup.py
    │   ├── venta_service.py
    │   ├── weekly_business_sentinel.py
    │   └── __init__.py
    │
    ├── models/
    │   └── approval_request.py
    │
    ├── api/
    │   └── v1/
    │       ├── approvals.py
    │       ├── auth.py
    │       ├── reports.py
    │       └── websockets.py
    │
    ├── core/
    │   ├── security.py
    │   └── websocket_manager.py
    │
    ├── db/
    │   └── session.py
    │
    ├── middlewares/
    │   └── manager_pin.py
    │
    ├── data/
    │   ├── seeds/
    │   │   └── core_seed.json
    │   ├── demo_products.py
    │   ├── product_template.csv
    │   └── drafts.json
    │
    ├── scripts/
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
    ├── tests/
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
    │   └── invoice.html
    │
    ├── frontend/
    │   └── package-lock.json
    │
    └── (otros archivos Python)
```

### Frontend

```
frontend/
├── package.json                 ← Dependencias Node
├── vite.config.js               ← Config Vite
├── Dockerfile                   ← Build del frontend
├── nginx.conf                   ← Config Nginx
│
├── src/
│   ├── App.jsx                  ← Componente principal
│   ├── main.jsx                 ← Punto de entrada
│   │
│   ├── components/              ← Componentes reutilizables
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   ├── DashboardCard.jsx
│   │   └── ...
│   │
│   ├── pages/                   ← Páginas/vistas
│   │   ├── Dashboard.jsx
│   │   ├── Inventory.jsx
│   │   ├── HumanResources.jsx
│   │   ├── Sales.jsx
│   │   └── ...
│   │
│   ├── services/                ← Llamadas a API
│   │   ├── api.js               ← Cliente HTTP
│   │   ├── inventoryService.js
│   │   ├── hrService.js
│   │   ├── salesService.js
│   │   └── ...
│   │
│   ├── hooks/                   ← Hooks personalizados
│   │   ├── useAuth.js
│   │   ├── useInventory.js
│   │   └── ...
│   │
│   ├── utils/                   ← Utilidades
│   │   ├── helpers.js
│   │   ├── constants.js
│   │   ├── formatters.js
│   │   └── ...
│   │
│   ├── styles/                  ← Estilos CSS
│   │   ├── App.css
│   │   ├── index.css
│   │   └── ...
│   │
│   └── assets/                  ← Imágenes y assets
│       ├── logo.png
│       ├── icons/
│       └── ...
│
├── public/
│   └── (archivos públicos)
│
└── dist/                        ← Build compilado (generado)
```

---

## ✅ Checklist antes de editar

- [ ] VSCode abierto en `C:\tmp\erp3`
- [ ] Terminal de VSCode abierta (Ctrl+`)
- [ ] Containers corriendo (`docker ps`)
- [ ] Entiendes qué archivo editar
- [ ] Tienes Git configurado (`git config --global user.name`)

---

## 📞 Comandos útiles en la terminal de VSCode

```bash
# Ver estado de containers
docker ps

# Reiniciar backend
docker compose restart backend

# Reiniciar frontend
docker compose restart frontend

# Ver logs del backend
docker compose logs -f backend

# Ver logs del frontend
docker compose logs -f frontend

# Ejecutar tests
docker exec mundo-backend pytest

# Hacer commit
git add -A
git commit -m "Descripción del cambio"

# Push a GitHub
git push origin main
```

---

## 🎓 Ejemplo: Agregar un nuevo endpoint

### Paso 1: Edita el archivo

Abre: `backend/backend/routes/human_resources.py`

Agrega al final:

```python
@router.get("/custom-endpoint")
async def get_custom_data(db=Depends(get_db)):
    """
    Endpoint personalizado
    """
    result = db.custom_collection.find({})
    return {"data": list(result)}
```

### Paso 2: Guarda y reinicia

```bash
# En la terminal de VSCode
docker compose restart backend
```

### Paso 3: Prueba

Abre: http://localhost:8001/docs

Busca tu nuevo endpoint y pruébalo

---

**¡Listo para editar!**

