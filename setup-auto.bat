@echo off
REM ============================================================
REM AUTO-SETUP: MC-LARENS ERP en Docker
REM ============================================================
REM Este script clona el repositorio, buildea las imágenes,
REM inicia el stack y restaura los datos de MongoDB

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   MC-LARENS ERP - AUTO SETUP
echo ============================================================
echo.

REM PASO 1: Verificar Docker
echo [1/6] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no está instalado o no está en PATH
    echo Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo OK: Docker instalado

REM PASO 2: Verificar Git
echo [2/6] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no está instalado o no está en PATH
    echo Descarga Git desde: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo OK: Git instalado

REM PASO 3: Clonar repositorio
echo.
echo [3/6] Clonando repositorio...
set /p REPO_PATH="Ingresa la ruta donde guardar el proyecto (ej: C:\MC-LARENS-ERP): "
if exist "!REPO_PATH!" (
    echo ERROR: La carpeta ya existe
    pause
    exit /b 1
)

git clone https://github.com/Samuraimaid/erp3.git "!REPO_PATH!"
if errorlevel 1 (
    echo ERROR: No se pudo clonar el repositorio
    pause
    exit /b 1
)
echo OK: Repositorio clonado

REM PASO 4: Entrar al directorio y copiar .env
echo.
echo [4/6] Configurando variables de entorno...
cd /d "!REPO_PATH!"

if not exist ".env" (
    copy .env.example .env >nul
    echo OK: .env creado desde .env.example
) else (
    echo OK: .env ya existe
)

REM PASO 5: Buildear imágenes
echo.
echo [5/6] Construyendo imágenes Docker (esto puede tardar 10-15 minutos)...
docker compose build
if errorlevel 1 (
    echo ERROR: Falló al construir las imágenes
    pause
    exit /b 1
)
echo OK: Imágenes construidas

REM PASO 6: Iniciar servicios y restaurar DB
echo.
echo [6/6] Iniciando servicios...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Falló al iniciar los servicios
    pause
    exit /b 1
)
echo OK: Servicios iniciados

echo.
echo Esperando a que MongoDB esté listo (30 segundos)...
timeout /t 30 /nobreak

echo.
echo Restaurando base de datos...
docker exec mclarens2-mongodb mongorestore /mongodb-backup
if errorlevel 1 (
    echo ADVERTENCIA: Hubo un problema al restaurar MongoDB
    echo Intenta manualmente: docker exec mclarens2-mongodb mongorestore /mongodb-backup
) else (
    echo OK: Base de datos restaurada
)

echo.
echo ============================================================
echo   ✅ SETUP COMPLETADO!
echo ============================================================
echo.
echo 🌐 Accede a los servicios:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8001
echo    - MongoDB: localhost:27017
echo.
echo 📊 Ver estado:
echo    - docker compose ps
echo.
echo 🔓 Credenciales de prueba:
echo    - Email: xinon@local
echo    - PIN: 0101
echo    - PIN Login: 01011990
echo.
echo 📝 Más información en: !REPO_PATH!\SETUP_COMPLETO.md
echo.
echo Para detener: docker compose down
echo Para reiniciar: docker compose restart
echo.
pause
