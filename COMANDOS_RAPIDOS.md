# 📋 COMANDOS LISTOS PARA COPIAR - LEVANTAR STACK GITHUB SIN CONFLICTOS

## ⚡ OPCIÓN 1: Script automático (Recomendado)

Abre PowerShell y ejecuta:

```powershell
# Descarga el script
git clone https://github.com/Samuraimaid/erp3.git C:\temp-erp3
cd C:\temp-erp3

# Dale permisos de ejecución
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser

# Ejecuta
.\setup-no-conflicts.ps1

# Acepta si te pregunta sobre la ruta de instalación (presiona ENTER)
```

**El script hace automáticamente:**
- Verifica Docker y Git
- Clona el repositorio
- Copia .env
- Levanta los servicios en puertos sin conflictos
- Restaura MongoDB

---

## 📟 OPCIÓN 2: Comandos paso a paso (máximo control)

### Paso 1: Clonar
```powershell
cd C:\
git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP-Github
cd MC-LARENS-ERP-Github
```

### Paso 2: Copiar .env
```powershell
Copy-Item .env.example .env
```

### Paso 3: Levantar sin conflictos
```powershell
docker compose -f docker-compose.no-conflict.yml up -d
```

### Paso 4: Esperar MongoDB
```powershell
Start-Sleep -Seconds 30
```

### Paso 5: Restaurar datos
```powershell
docker exec mclarens2-mongodb-github mongorestore /mongodb-backup
```

### Paso 6: Verificar
```powershell
docker compose -f docker-compose.no-conflict.yml ps
```

---

## 🚀 OPCIÓN 3: Una sola línea (para expertos)

```powershell
cd C:\ && git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP-Github && cd MC-LARENS-ERP-Github && Copy-Item .env.example .env && docker compose -f docker-compose.no-conflict.yml up -d && Start-Sleep -Seconds 30 && docker exec mclarens2-mongodb-github mongorestore /mongodb-backup && docker compose -f docker-compose.no-conflict.yml ps
```

---

## ✅ Una vez completado

### Ver todos los stacks corriendo

```powershell
docker ps -a
```

**Deberías ver 9 contenedores:**

```
3 del Stack 1 (principal)
  - mundo-frontend:3000
  - mundo-backend:8001
  - mclarens2-mongodb:27017

3 del Stack 2 (backup)
  - mundo-frontend-bkp:3001
  - mundo-backend-bkp:8002
  - mclarens2-mongodb-bkp:27018

3 del Stack 3 (GitHub) ← NUEVO
  - mundo-frontend-github:3002
  - mundo-backend-github:8003
  - mclarens2-mongodb-github:27019
```

### Acceder en el navegador

```
Stack 1 (Principal):  http://localhost:3000
Stack 2 (Backup):     http://localhost:3001
Stack 3 (GitHub):     http://localhost:3002  ← NUEVO
```

### Ver logs del nuevo stack

```powershell
docker compose -f C:\MC-LARENS-ERP-Github\docker-compose.no-conflict.yml logs -f
```

### Detener solo el nuevo stack (sin afectar los otros)

```powershell
cd C:\MC-LARENS-ERP-Github
docker compose -f docker-compose.no-conflict.yml stop
```

### Reiniciar solo el nuevo stack

```powershell
cd C:\MC-LARENS-ERP-Github
docker compose -f docker-compose.no-conflict.yml start
```

### Eliminar solo el nuevo stack (CUIDADO: pierde datos)

```powershell
cd C:\MC-LARENS-ERP-Github
docker compose -f docker-compose.no-conflict.yml down -v
```

---

## 🔍 Verificación rápida

### Estado de los 3 stacks

```powershell
Write-Host "=== STACK 1 ===" 
docker compose -f C:\MC-LARENS_ERP2\docker-compose.yml ps

Write-Host "=== STACK 2 ==="
docker compose -f C:\Stack_1_MC-LARENS_ERP2\docker-compose.no-conflict.yml ps

Write-Host "=== STACK 3 (GitHub) ==="
docker compose -f C:\MC-LARENS-ERP-Github\docker-compose.no-conflict.yml ps
```

### Prueba de conectividad rápida

```powershell
# Stack 1
(Invoke-WebRequest http://localhost:3000 -ErrorAction SilentlyContinue).StatusCode

# Stack 2
(Invoke-WebRequest http://localhost:3001 -ErrorAction SilentlyContinue).StatusCode

# Stack 3 (GitHub)
(Invoke-WebRequest http://localhost:3002 -ErrorAction SilentlyContinue).StatusCode

# Deberías ver: 200 en los 3
```

### API de los 3 backends

```powershell
# Stack 1: http://localhost:8001/docs
# Stack 2: http://localhost:8002/docs
# Stack 3: http://localhost:8003/docs ← NUEVO
```

---

## 💾 Sincronizar cambios de GitHub

Si hay actualizaciones en el repositorio:

```powershell
cd C:\MC-LARENS-ERP-Github

# Traer cambios
git pull origin main

# Rebuild de imágenes (si cambió el código)
docker compose -f docker-compose.no-conflict.yml build

# Reiniciar
docker compose -f docker-compose.no-conflict.yml down
docker compose -f docker-compose.no-conflict.yml up -d
```

---

## ⚠️ Solución de problemas

### "Puerto ya en uso" para 3002, 8003 o 27019

Edita `docker-compose.no-conflict.yml` y cambia los puertos:

```yaml
ports:
  - "3003:80"      # Cambiar 3002 a 3003
  - "8004:8001"    # Cambiar 8003 a 8004
  - "27020:27017"  # Cambiar 27019 a 27020
```

Luego:
```powershell
docker compose -f docker-compose.no-conflict.yml down
docker compose -f docker-compose.no-conflict.yml up -d
```

### MongoDB no restaura datos

```powershell
# Ver logs
docker logs mclarens2-mongodb-github

# Espera más tiempo y reintenta
Start-Sleep -Seconds 60
docker exec mclarens2-mongodb-github mongorestore /mongodb-backup
```

### Backend no se conecta a MongoDB

```powershell
# Reinicia el backend
docker compose -f docker-compose.no-conflict.yml restart backend

# Ver logs
docker compose -f docker-compose.no-conflict.yml logs backend
```

---

## 📊 Resumen final

| Componente | Stack 1 | Stack 2 | Stack 3 (GitHub) |
|------------|---------|---------|------------------|
| Frontend | :3000 | :3001 | :3002 |
| Backend | :8001 | :8002 | :8003 |
| MongoDB | :27017 | :27018 | :27019 |
| Estado | En vivo | En vivo | Nuevo sin conflictos |

**Los 3 stacks corriendo juntos, completamente independientes.**

