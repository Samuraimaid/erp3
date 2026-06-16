#!/bin/bash
# setup.sh - Script de configuración e instalación del ERP

set -e

echo "=========================================="
echo "MC-LarenS ERP - Setup Script"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Verificar Docker
print_info "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    exit 1
fi
print_status "Docker encontrado: $(docker --version)"

# Verificar Docker Compose
print_info "Verificando Docker Compose..."
if ! docker compose --version &> /dev/null; then
    print_error "Docker Compose no está instalado"
    exit 1
fi
print_status "Docker Compose encontrado: $(docker compose --version)"

# Crear archivo .env si no existe
print_info "Configurando variables de entorno..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_status "Archivo .env creado desde .env.example"
else
    print_status "Archivo .env ya existe"
fi

# Crear carpetas de volúmenes locales (si es necesario)
print_info "Preparando volúmenes..."
mkdir -p mongodb-backup
mkdir -p logs
print_status "Directorios preparados"

# Detener contenedores previos
print_info "Limpiando contenedores anteriores..."
docker compose down --remove-orphans 2>/dev/null || true
print_status "Contenedores limpios"

# Pull de imágenes
print_info "Descargando imágenes Docker..."
docker compose pull
print_status "Imágenes descargadas"

# Iniciar servicios
print_info "Iniciando servicios..."
docker compose up -d
print_status "Servicios iniciados"

# Esperar a que MongoDB esté listo
print_info "Esperando a que MongoDB esté listo..."
for i in {1..30}; do
    if docker exec mclarens2-mongodb mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
        print_status "MongoDB listo"
        break
    fi
    echo -n "."
    sleep 1
done

# Restaurar base de datos
print_info "Restaurando base de datos..."
if [ -d "mongodb-backup" ] && [ "$(ls -A mongodb-backup)" ]; then
    docker exec mclarens2-mongodb mongorestore /restore-backup
    print_status "Base de datos restaurada"
else
    print_info "No hay backup para restaurar - usando BD vacía"
fi

# Verificar servicios
print_info "Verificando servicios..."
echo ""
docker compose ps

echo ""
echo "=========================================="
echo "Setup completado con éxito!"
echo "=========================================="
echo ""
echo "Servicios disponibles:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  API Docs: http://localhost:8001/docs"
echo "  MongoDB: localhost:27017"
echo ""
echo "Próximos pasos:"
echo "  1. Accede a http://localhost:3000"
echo "  2. Usa PIN: 0101 (por defecto)"
echo "  3. Cambia credenciales en .env"
echo ""
echo "Para ver logs:"
echo "  docker compose logs -f"
echo ""
