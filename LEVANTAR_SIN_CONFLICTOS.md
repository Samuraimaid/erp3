# 🚀 LEVANTAR ERP DESDE GITHUB SIN CONFLICTOS

## Estado actual de puertos

| Stack | Frontend | Backend | MongoDB |
|-------|----------|---------|---------|
| Stack 1 (Principal) | 3000 | 8001 | 27017 |
| Stack 2 (Backup) | 3001 | 8002 | 27018 |
| **Stack 3 (GitHub)** | **3002** | **8003** | **27019** |

---

## PASO 1: Clonar el repositorio GitHub

```powershell
# Ir a la carpeta donde guardar
cd C:\

# Clonar
git clone https://github.com/Samuraimaid/erp3.git MC-LARENS-ERP-GitHub

# Entrar a la carpeta
cd MC-LARENS-ERP-Github
```

---

## PASO 2: Copiar .env

```powershell
Copy-Item .env.example .env
```

---

## PASO 3: Usar el docker-compose sin conflictos

```powershell
# Este archivo usa puertos diferentes (3002, 8003, 27019)
# para no chocar con los stacks actuales

# Levantar usando el compose alternativo
docker compose -f docker-compose.no-conflict.yml up -d
```

---

## PASO 4: Esperar a que MongoDB esté listo

```powershell
Start-Sleep -Seconds 30

# Verificar que los 3 contenedores estén corriendo
docker compose -f docker-compose.no-conflict.yml ps

# Deberías ver:
# mclarens2-mongodb-github    | Up
# mundo-backend-github        | Up
# mundo-frontend-github       | Up
```

---

## PASO 5: Restaurar la base de datos

```powershell
# Restaurar todos los datos desde el backup de GitHub
docker exec mclarens2-mongodb-github mongorestore /mongodb-backup

# Esto tarda 1-5 minutos según la cantidad de datos
```

---

## PASO 6: Verificar que funciona

```powershell
# Ver logs
docker compose -f docker-compose.no-conflict.yml logs -f

# En navegador (abre nuevas pestañas):
# - Frontend: http://localhost:3002
# - Backend API: http://localhost:8003/docs
# - MongoDB: localhost:27019

# Test de conexión
curl http://localhost:8003/docs
```

---

## ✅ Resumen: Los 3 stacks corriendo en paralelo

```
Navegador                    Docker
================            ================
localhost:3000   ←→   Stack 1 Frontend (principal)
localhost:8001   ←→   Stack 1 Backend
localhost:27017  ←→   Stack 1 MongoDB

localhost:3001   ←→   Stack 2 Frontend (backup)
localhost:8002   ←→   Stack 2 Backend
localhost:27018  ←→   Stack 2 MongoDB

localhost:3002   ←→   Stack 3 Frontend (GitHub) ✨ NUEVO
localhost:8003   ←→   Stack 3 Backend
localhost:27019  ←→   Stack 3 MongoDB
```

**Todos corriendo al mismo tiempo sin conflictos.**

---

## 🔧 Comandos útiles para el Stack GitHub

```powershell
# Ver estado
docker compose -f docker-compose.no-conflict.yml ps

# Ver logs
docker compose -f docker-compose.no-conflict.yml logs -f backend

# Reiniciar un servicio
docker compose -f docker-compose.no-conflict.yml restart backend

# Detener el stack (sin eliminar datos)
docker compose -f docker-compose.no-conflict.yml stop

# Volver a iniciar
docker compose -f docker-compose.no-conflict.yml start

# Detener y eliminar todo (CUIDADO: pierde datos)
docker compose -f docker-compose.no-conflict.yml down -v

# Ver volúmenes del stack GitHub
docker volume ls | grep github
```

---

## 🔐 Credenciales

Todas usan las mismas credenciales de prueba:

```
Email: xinon@local
PIN: 0101
PIN Login: 01011990
```

---

## 📊 Ver todos los contenedores de los 3 stacks

```powershell
docker ps -a

# Verás 9 contenedores en total:
# - 3 del Stack 1 (principal)
# - 3 del Stack 2 (backup)
# - 3 del Stack 3 (GitHub) ← nuevos
```

---

## 🛠️ Si necesitas cambiar puertos

Edita `docker-compose.no-conflict.yml`:

```yaml
# Cambiar puertos (primer número es el puerto del host)
ports:
  - "3002:80"      # Frontend
  - "8003:8001"    # Backend
  - "27019:27017"  # MongoDB
```

Luego reinicia:
```powershell
docker compose -f docker-compose.no-conflict.yml down
docker compose -f docker-compose.no-conflict.yml up -d
```

---

## ⚠️ Importante

- Los 3 stacks **comparten la misma red de Docker** (si lo necesitas cambiar, edita la sección `networks` en el compose)
- Las bases de datos son **independientes** (cada una en su volumen)
- Las imágenes Docker se **comparten** entre stacks (misma imagen, múltiples contenedores)

---

## ✔️ Checklist

- [ ] Repositorio clonado en `C:\MC-LARENS-ERP-Github`
- [ ] `.env` copiado
- [ ] Stack levantado con `-f docker-compose.no-conflict.yml`
- [ ] MongoDB restaurado
- [ ] Frontend accesible en http://localhost:3002
- [ ] Backend accesible en http://localhost:8003
- [ ] Los 3 stacks corriendo juntos sin conflictos

