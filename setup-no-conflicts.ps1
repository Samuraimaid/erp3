# ============================================================
# SCRIPT: Auto-setup ERP desde GitHub SIN CONFLICTOS
# ============================================================
# Uso: .\setup-no-conflicts.ps1
# ============================================================

param(
    [string]$InstallPath = "C:\MC-LARENS-ERP-Github"
)

Write-Host ""
Write-Host "============================================================"
Write-Host "   MC-LARENS ERP - SETUP SIN CONFLICTOS (GitHub)"
Write-Host "============================================================"
Write-Host ""

# PASO 1: Verificar Docker
Write-Host "[1/7] Verificando Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "OK: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker no está instalado" -ForegroundColor Red
    Write-Host "Descarga desde: https://www.docker.com/products/docker-desktop"
    exit 1
}

# PASO 2: Verificar Git
Write-Host "[2/7] Verificando Git..." -ForegroundColor Cyan
try {
    $gitVersion = git --version
    Write-Host "OK: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git no está instalado" -ForegroundColor Red
    Write-Host "Descarga desde: https://git-scm.com/download/win"
    exit 1
}

# PASO 3: Verificar stacks actuales
Write-Host "[3/7] Verificando stacks actuales..." -ForegroundColor Cyan
$containers = docker ps -a --format "{{.Names}}"
$stacksRunning = @()
if ($containers -match "mundo-backend$") { $stacksRunning += "Stack 1 (principal)" }
if ($containers -match "mundo-backend-bkp") { $stacksRunning += "Stack 2 (backup)" }

if ($stacksRunning.Count -gt 0) {
    Write-Host "OK: Detectados stacks actuales:" -ForegroundColor Green
    $stacksRunning | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
    Write-Host "    El nuevo stack usará puertos 3002, 8003, 27019 para evitar conflictos" -ForegroundColor Yellow
} else {
    Write-Host "INFO: No se detectaron stacks corriendo" -ForegroundColor Yellow
}

# PASO 4: Clonar repositorio
Write-Host "[4/7] Clonando repositorio GitHub..." -ForegroundColor Cyan
if (Test-Path $InstallPath) {
    Write-Host "ADVERTENCIA: $InstallPath ya existe" -ForegroundColor Yellow
    $continuar = Read-Host "¿Continuar de todas formas? (s/n)"
    if ($continuar -ne "s") {
        exit 0
    }
} else {
    git clone https://github.com/Samuraimaid/erp3.git $InstallPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: No se pudo clonar el repositorio" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Repositorio clonado en $InstallPath" -ForegroundColor Green
}

# PASO 5: Copiar .env
Write-Host "[5/7] Configurando variables de entorno..." -ForegroundColor Cyan
$envFile = Join-Path $InstallPath ".env"
$envExampleFile = Join-Path $InstallPath ".env.example"

if (Test-Path $envFile) {
    Write-Host "OK: .env ya existe" -ForegroundColor Green
} else {
    if (Test-Path $envExampleFile) {
        Copy-Item $envExampleFile $envFile
        Write-Host "OK: .env creado desde .env.example" -ForegroundColor Green
    } else {
        Write-Host "ADVERTENCIA: No se encontró .env.example" -ForegroundColor Yellow
    }
}

# PASO 6: Levantar stack sin conflictos
Write-Host "[6/7] Iniciando stack en puertos sin conflictos..." -ForegroundColor Cyan
Write-Host "    Frontend: http://localhost:3002" -ForegroundColor Yellow
Write-Host "    Backend:  http://localhost:8003" -ForegroundColor Yellow
Write-Host "    MongoDB:  localhost:27019" -ForegroundColor Yellow
Write-Host ""

Push-Location $InstallPath
try {
    docker compose -f docker-compose.no-conflict.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Falló al levantar los servicios" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Servicios iniciados" -ForegroundColor Green
} finally {
    Pop-Location
}

# PASO 7: Restaurar MongoDB
Write-Host "[7/7] Esperando MongoDB (30 segundos)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "Restaurando base de datos..." -ForegroundColor Cyan
try {
    docker exec mclarens2-mongodb-github mongorestore /mongodb-backup 2>&1 | Out-Null
    Write-Host "OK: Base de datos restaurada" -ForegroundColor Green
} catch {
    Write-Host "ADVERTENCIA: Hubo un problema restaurando MongoDB" -ForegroundColor Yellow
    Write-Host "Intenta manualmente: docker exec mclarens2-mongodb-github mongorestore /mongodb-backup"
}

# Verificación final
Write-Host ""
Write-Host "============================================================"
Write-Host "   ✅ SETUP COMPLETADO SIN CONFLICTOS!"
Write-Host "============================================================"
Write-Host ""

$ps = docker compose -f "$InstallPath\docker-compose.no-conflict.yml" ps --format "table {{.Names}}\t{{.Status}}"
Write-Host "Estado de servicios:" -ForegroundColor Cyan
Write-Host $ps
Write-Host ""

Write-Host "🌐 Accede a:" -ForegroundColor Green
Write-Host "    Frontend:  http://localhost:3002"
Write-Host "    Backend:   http://localhost:8003/docs"
Write-Host "    MongoDB:   localhost:27019"
Write-Host ""

Write-Host "🔓 Credenciales:" -ForegroundColor Green
Write-Host "    Email: xinon@local"
Write-Host "    PIN: 0101"
Write-Host "    PIN Login: 01011990"
Write-Host ""

Write-Host "📊 Ver todos los stacks:" -ForegroundColor Green
Write-Host "    docker ps -a"
Write-Host ""

Write-Host "📝 Más info:" -ForegroundColor Green
Write-Host "    $InstallPath\LEVANTAR_SIN_CONFLICTOS.md"
Write-Host ""

Write-Host "💡 Comandos útiles:" -ForegroundColor Green
Write-Host "    docker compose -f $InstallPath\docker-compose.no-conflict.yml ps"
Write-Host "    docker compose -f $InstallPath\docker-compose.no-conflict.yml logs -f"
Write-Host "    docker compose -f $InstallPath\docker-compose.no-conflict.yml down"
Write-Host ""

Read-Host "Presiona ENTER para cerrar"
