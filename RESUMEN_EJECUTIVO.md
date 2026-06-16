# 📦 TU ERP ESTÁ EN GITHUB - LISTO PARA CLONAR

## ¿Qué subiste a GitHub?

Tu repositorio `https://github.com/Samuraimaid/erp3.git` contiene:

### ✅ CÓDIGO FUENTE (Completo)
- **`/backend-source`** → Código Python FastAPI (API del ERP)
- **`/backend-source-complete`** → Versión completa con todas las rutas
- **`/frontend-build`** → Frontend React compilado
- **`/mongodb-backup`** → Datos completos de MongoDB (todos los clientes, productos, etc.)

### ✅ CONFIGURACIÓN DOCKER
- **`docker-compose.yml`** → Define los 3 servicios (MongoDB, Backend, Frontend)
- **`Dockerfile.backend`** → Receta para construir la imagen del backend
- **`Dockerfile.frontend`** → Receta para construir la imagen del frontend
- **`nginx.conf`** → Configuración del reverse proxy

### ✅ DOCUMENTACIÓN
- **`README.md`** → Instrucciones básicas
- **`SETUP_COMPLETO.md`** → Guía detallada paso a paso
- **`setup-auto.bat`** → Script automatizado (Windows)
- **`ARCHITECTURE.md`** → Descripción de la arquitectura
- **`API.md`** → Documentación de endpoints
- **`DEVELOPMENT.md`** → Guía para desarrollo local
- **`.env.example`** → Variables de entorno (sin datos sensibles)

### ❌ NO CONTIENE (por seguridad/tamaño)
- Imágenes Docker precompiladas (se crean automáticamente)
- Credenciales reales (solo ejemplos)
- node_modules, __pycache__, etc.

---

## 🚀 EN OTRO PC: 3 FORMAS DE RESTAURAR

### OPCIÓN 1️⃣ - SCRIPT AUTOMÁTICO (Más fácil - Windows)
```powershell
# Descarga y ejecuta el script
cd C:\
git clone https://github.com/Samuraimaid/erp3.git temporal
cd temporal
.\setup-auto.bat

# El script hace todo automáticamente:
# ✓ Verifica Docker y Git
# ✓ Clona el repositorio
# ✓ Buildea imágenes
# ✓ Inicia servicios
# ✓ Restaura BD
```

### OPCIÓN 2️⃣ - COMANDOS MANUALES (Más control)
```powershell
# 1. Clonar
git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP
cd MC-LARENS-ERP

# 2. Copiar .env
Copy-Item .env.example .env

# 3. Buildear imágenes (toma 10-15 min)
docker compose build

# 4. Iniciar stack
docker compose up -d

# 5. Esperar 30 segundos
Start-Sleep -Seconds 30

# 6. Restaurar MongoDB
docker exec mclarens2-mongodb mongorestore /mongodb-backup

# 7. Acceder a http://localhost:3000
```

### OPCIÓN 3️⃣ - QUICK START (Una línea - para valientes)
```bash
git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP && \
cd MC-LARENS-ERP && \
docker compose up -d && \
sleep 30 && \
docker exec mclarens2-mongodb mongorestore /mongodb-backup && \
echo "✅ ERP corriendo en http://localhost:3000"
```

---

## 📊 QUÉ SE NECESITA EN EL PC DESTINO

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 2GB | 4GB+ |
| Disco | 5GB | 10GB+ |
| Docker | Latest | Latest |
| Git | 2.x | Latest |
| OS | Windows 10, macOS 10.14+, Linux | Windows 11, macOS 12+, Ubuntu 20.04+ |

---

## ✅ VERIFICACIÓN POST-SETUP

Una vez que ejecutes cualquiera de las opciones:

```powershell
# 1. Ver que todo está corriendo
docker compose ps

# Deberías ver:
# mclarens2-mongodb    | Up
# mundo-backend        | Up
# mundo-frontend       | Up
```

**En tu navegador:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8001/docs
- MongoDB: localhost:27017

**Credenciales de prueba:**
- Email: `xinon@local`
- PIN: `0101`
- PIN Login: `01011990`

---

## 🔄 FLUJO RECOMENDADO PARA OTRO PC

```
PC ORIGEN (donde está el ERP)
         ↓
    GitHub (respaldo + código)
         ↓
PC DESTINO (clona + restaura)
         ↓
     ✅ ERP corriendo
```

---

## 🎯 AHORA TÚ TIENES

✅ **Backup completo en GitHub** (seguro, versionado)
✅ **Código fuente públicamente accesible** (o privado si lo configuras)
✅ **Datos de MongoDB respaldados** (restaurables en cualquier PC)
✅ **Dockerfiles listos** (imágenes se crean automáticamente)
✅ **Documentación completa** (guías paso a paso)
✅ **Script automático** (setup en 1 click)

---

## 🔐 NOTAS DE SEGURIDAD

⚠️ Si el repositorio es **PRIVADO**:
- Solo tú y colaboradores pueden verlo
- Es seguro usar credenciales/endpoints reales

⚠️ Si el repositorio es **PÚBLICO**:
- Cualquiera en internet puede clonar tu código
- NO uses credenciales reales en `.env.example`
- Considera cambiar a Privado en GitHub Settings

---

## 📝 PRÓXIMAS ACCIONES

1. **En el otro PC:** Ejecuta una de las 3 opciones arriba
2. **Verifica:** Accede a http://localhost:3000
3. **Customiza:** Edita `.env` si necesitas cambiar puertos/URLs
4. **Backup local:** Haz `docker compose down` para pausar
5. **Comparte:** Dale el link de GitHub a otros que necesiten el ERP

---

**Tu ERP está listo para viajar. Clónalo donde necesites.** 🚀

