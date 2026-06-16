# Guía de Desarrollo - MC-LarenS ERP

## Configuración del Ambiente de Desarrollo

### Requisitos
- Docker & Docker Compose
- Python 3.11+ (para desarrollo local)
- Node.js 18+ (para frontend development)
- Git

### Setup

```bash
# 1. Clonar repositorio
git clone https://github.com/Samuraimaid/erp3.git
cd erp3

# 2. Crear .env
cp .env.example .env

# 3. Iniciar stack
docker compose up -d

# 4. Restaurar BD
sleep 10
docker exec mclarens2-mongodb mongorestore /restore-backup

# 5. Verificar
docker compose ps
```

## Desarrollo del Backend

### Estructura

```
backend-source/
├── backend/
│   ├── api/v1/              # Rutas API
│   ├── core/                # Auth, seguridad
│   ├── services/            # Lógica de negocio
│   ├── models/              # Modelos Pydantic
│   ├── routes/              # Rutas específicas
│   ├── db/                  # Sesiones DB
│   ├── middlewares/         # Custom middleware
│   ├── data/                # Datos de seed
│   ├── tests/               # Tests unitarios
│   ├── templates/           # HTML templates
│   └── server.py            # Punto de entrada
├── requirements.txt         # Dependencias
└── entrypoint.sh           # Script de inicio
```

### Agregar Nueva Ruta API

**1. Crear archivo en `routes/`**

```python
# backend/routes/ejemplo.py
from fastapi import APIRouter, Depends
from backend.core.security import get_current_user

router = APIRouter(prefix="/ejemplo", tags=["ejemplo"])

@router.get("/")
async def listar_ejemplos(current_user = Depends(get_current_user)):
    """Listar todos los ejemplos"""
    return {"items": []}

@router.post("/")
async def crear_ejemplo(data: dict, current_user = Depends(get_current_user)):
    """Crear nuevo ejemplo"""
    return {"id": "123", "data": data}
```

**2. Registrar en `server.py`**

```python
from backend.routes.ejemplo import router as ejemplo_router
app.include_router(ejemplo_router, prefix="/api/v1")
```

### Agregar Modelo MongoDB

**1. Crear clase Pydantic**

```python
# backend/models/ejemplo.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EjemploBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class EjemploCreate(EjemploBase):
    pass

class EjemploUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class Ejemplo(EjemploBase):
    id: str = Field(alias="_id")
    created_at: datetime
    
    class Config:
        populate_by_name = True
```

**2. Usar en rutas**

```python
from backend.db.session import db
from backend.models.ejemplo import Ejemplo

@router.get("/{id}")
async def obtener_ejemplo(id: str):
    doc = await db.ejemplos.find_one({"_id": ObjectId(id)})
    return doc
```

### Ejecutar Tests

```bash
# Dentro del backend container
docker exec mundo-backend pytest -v

# O localmente
cd backend-source
pip install -r requirements.txt
pytest -v
```

### Debugging

```bash
# Ver logs en vivo
docker compose logs -f backend

# Conectar a Shell Python
docker exec -it mundo-backend python

# Inspeccionar BD
docker exec -it mclarens2-mongodb mongosh
use mc-larens2_mundo_accesorios_erp
db.users.find()
```

## Desarrollo del Frontend

### Estructura

```
frontend-build/
├── assets/              # Bundles compilados
├── index.html          # HTML principal
├── env.js              # Variables de entorno
├── manifest.json       # PWA manifest
├── sw.js               # Service Worker
└── tutorials/          # Tutoriales SVG
```

### Notas de Desarrollo

El frontend compilado está en `frontend-build/`. Para cambios en el código fuente, necesitarías:

1. Acceso al repositorio original del frontend (React/Vite source)
2. Ambiente Node.js 18+
3. Variables de entorno configuradas

### Modificar Configuración

```javascript
// env.js - Variables dinámicas en tiempo de ejecución
window.__ENV__ = {
  VITE_BACKEND_URL: '/api',
  VITE_AUTH_URL: '/api/auth/login',
  VITE_ATTENDANCE_KIOSK_SHORTCUT_PIN: '50005000'
};
```

### Build Custom del Frontend (si tienes código fuente)

```bash
# Construir imagen
docker build -f Dockerfile.frontend -t mundo-frontend:custom .

# Actualizar docker-compose.yml
# image: mundo-frontend:custom

docker compose up -d frontend
```

## Guía de Commits

### Formato

```
<tipo>(<scope>): <descripción>

<cuerpo>

<footer>
```

### Tipos
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato de código
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Tareas de mantenimiento

### Ejemplo

```
feat(api/ventas): agregar filtro por fecha

- Implementar parámetros query start_date y end_date
- Agregar validación de rango de fechas
- Añadir tests para el nuevo filtro

Closes #123
```

## CI/CD (GitHub Actions)

### Pruebas Automáticas

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - run: docker compose run backend pytest
```

## Deployment

### Build Producción del Backend

```bash
# Build
docker build -f Dockerfile.backend \
  -t myregistry/mc-larenserp-backend:1.0.0 \
  .

# Push
docker push myregistry/mc-larenserp-backend:1.0.0
```

### Actualizar docker-compose.yml

```yaml
backend:
  image: myregistry/mc-larenserp-backend:1.0.0
```

## Performance Tips

### Backend
- Usar indexes en MongoDB para queries frecuentes
- Implementar caching con Redis
- Paginar resultados grandes
- Usar select() en queries para limitar campos

### Frontend
- Lazy loading de componentes
- Code splitting con Vite
- Comprimir imágenes
- CDN para assets estáticos

## Recursos Útiles

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [MongoDB PyMongo](https://pymongo.readthedocs.io)
- [Pydantic](https://docs.pydantic.dev)
- [React](https://react.dev)
- [Docker](https://docs.docker.com)

## Contacto & Support

Para preguntas sobre desarrollo:
- Issues en GitHub
- Documentación en el repositorio
- Equipo de desarrollo
