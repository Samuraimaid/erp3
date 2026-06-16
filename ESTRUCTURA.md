# Estructura del Proyecto MC-LarenS ERP

```
erp-stack-backup/
├── backend-source/                 # Código fuente del Backend (FastAPI)
│   ├── app/                        # Aplicación auxiliar
│   ├── backend/                    # Módulo principal del backend
│   │   ├── server.py              # Punto de entrada FastAPI
│   │   └── ...                    # Otros módulos
│   ├── requirements.txt            # Dependencias Python
│   └── .gitignore
│
├── frontend-build/                 # Build compilado del Frontend (React)
│   ├── assets/                    # Assets compilados
│   ├── index.html
│   ├── env.js
│   └── ...
│
├── mongodb-backup/                 # Backup de la base de datos
│   ├── admin/
│   ├── mc-larens2_mundo_accesorios_erp/  # Colecciones principales
│   └── prelude.json
│
├── docker-compose.yml              # Configuración de servicios Docker
├── Dockerfile.backend              # Build del backend desde código
├── Dockerfile.frontend             # Build del frontend desde archivos
├── nginx.conf                      # Configuración de Nginx
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore                      # Archivos ignorados en Git
├── README.md                       # Documentación principal
├── restore.sh                      # Script de restauración
├── backup.sh                       # Script de backup
└── ESTRUCTURA.md                   # Este archivo
```

## Descripción de Carpetas

### backend-source/
Código fuente completo del backend en Python (FastAPI). Incluye:
- Modelos de datos
- Rutas API
- Lógica de negocio
- Servicios e integraciones

### frontend-build/
Frontend compilado (producción). Contiene:
- JavaScript/CSS compilado
- Assets (imágenes, iconos)
- HTML estático
- Se sirve mediante Nginx

### mongodb-backup/
Dump completo de MongoDB restaurable con `mongorestore`:
- Todas las colecciones de la BD
- Índices y configuración
- Datos de producción

## Flujo de Restauración

1. **Clonar repositorio**
   ```bash
   git clone https://github.com/Samuraimaid/erp3.git
   cd erp3
   ```

2. **Iniciar contenedores**
   ```bash
   docker compose up -d
   ```

3. **Restaurar base de datos**
   ```bash
   sleep 10
   docker exec mclarens2-mongodb mongorestore /restore-backup
   ```

4. **Verificar**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - MongoDB: localhost:27017

## Reconstruir Imágenes desde Código

```bash
# Backend
docker build -f Dockerfile.backend -t mc-larenserp20-backend:rebuild .

# Frontend
docker build -f Dockerfile.frontend -t mundo-frontend:rebuild .
```

Luego actualizar `docker-compose.yml` con los nuevos tags.
