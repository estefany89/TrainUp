#!/bin/bash

################################################################################
# Script de Despliegue Automatizado - TrainUp Gym
# 
# Este script automatiza el despliegue completo de la aplicación incluyendo:
# - Verificación de requisitos
# - Construcción de imágenes Docker
# - Inicialización de contenedores
# - Carga de datos iniciales (opcional)
# - Creación de superusuario
#
# Uso: ./deploy.sh [opciones]
#   --with-data    : Cargar datos de demostración
#   --skip-build   : Saltar construcción de imágenes
#   --help         : Mostrar ayuda
################################################################################

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOAD_DATA=false
SKIP_BUILD=false

################################################################################
# Funciones auxiliares
################################################################################

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 está instalado"
        return 0
    else
        print_error "$1 no está instalado"
        return 1
    fi
}

show_help() {
    cat << EOF
Uso: ./deploy.sh [opciones]

Opciones:
  --with-data      Cargar datos de demostración en la base de datos
  --skip-build     Saltar la construcción de imágenes Docker
  --help           Mostrar esta ayuda

Ejemplos:
  ./deploy.sh                    # Despliegue básico
  ./deploy.sh --with-data        # Despliegue con datos de demo
  ./deploy.sh --skip-build       # Usar imágenes existentes

EOF
    exit 0
}

################################################################################
# Parsear argumentos
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-data)
            LOAD_DATA=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            ;;
    esac
done

################################################################################
# PASO 1: Verificar requisitos
################################################################################

print_header "PASO 1: Verificando Requisitos"

REQUIREMENTS_OK=true

if ! check_command docker; then
    REQUIREMENTS_OK=false
fi

if ! check_command "docker compose" && ! check_command "docker-compose"; then
    print_error "docker compose no está instalado"
    REQUIREMENTS_OK=false
else
    print_success "docker compose está instalado"
fi

# Verificar que Docker esté corriendo
if ! docker info &> /dev/null; then
    print_error "Docker no está corriendo. Inicia Docker y vuelve a intentar."
    REQUIREMENTS_OK=false
else
    print_success "Docker está corriendo"
fi

if [ "$REQUIREMENTS_OK" = false ]; then
    print_error "Faltan requisitos. Por favor, instala las dependencias necesarias."
    exit 1
fi

################################################################################
# PASO 2: Verificar archivos necesarios
################################################################################

print_header "PASO 2: Verificando Archivos"

cd "$SCRIPT_DIR"

if [ ! -f "docker-compose.yml" ]; then
    print_error "No se encuentra docker-compose.yml"
    exit 1
fi
print_success "docker-compose.yml encontrado"

if [ ! -f "Dockerfile" ]; then
    print_error "No se encuentra Dockerfile"
    exit 1
fi
print_success "Dockerfile encontrado"

if [ ! -f ".env" ]; then
    print_warning ".env no encontrado. Creando desde .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Revisa y edita el archivo .env con tus configuraciones"
        read -p "Presiona Enter cuando hayas configurado .env..."
    else
        print_error ".env.example no encontrado"
        exit 1
    fi
else
    print_success ".env encontrado"
fi

if [ ! -f "gimnasio_project/db.sqlite3" ] && [ "$LOAD_DATA" = true ]; then
    print_warning "No se encontró db.sqlite3. No se podrán cargar datos iniciales."
    LOAD_DATA=false
fi

################################################################################
# PASO 3: Detener contenedores existentes
################################################################################

print_header "PASO 3: Limpiando Contenedores Anteriores"

if docker compose ps | grep -q "Up"; then
    print_info "Deteniendo contenedores existentes..."
    docker compose down
    print_success "Contenedores detenidos"
else
    print_info "No hay contenedores corriendo"
fi

################################################################################
# PASO 4: Construir imágenes
################################################################################

if [ "$SKIP_BUILD" = false ]; then
    print_header "PASO 4: Construyendo Imágenes Docker"
    
    print_info "Esto puede tardar varios minutos la primera vez..."
    
    if docker compose build; then
        print_success "Imágenes construidas exitosamente"
    else
        print_error "Error al construir imágenes"
        exit 1
    fi
else
    print_header "PASO 4: Saltando Construcción de Imágenes"
    print_info "Usando imágenes existentes"
fi

################################################################################
# PASO 5: Exportar datos de SQLite (si existe)
################################################################################

if [ "$LOAD_DATA" = true ] && [ -f "gimnasio_project/db.sqlite3" ]; then
    print_header "PASO 5: Exportando Datos de SQLite"
    
    print_info "Exportando datos desde db.sqlite3..."
    
    # Verificar si Python está disponible
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python no está instalado"
        LOAD_DATA=false
    fi
    
    if [ "$LOAD_DATA" = true ]; then
        cd gimnasio_project
        
        # Exportar datos
        $PYTHON_CMD manage.py dumpdata \
            --natural-foreign \
            --natural-primary \
            -e contenttypes \
            -e auth.Permission \
            --indent 2 \
            -o initial_data.json
        
        if [ -f "initial_data.json" ]; then
            print_success "Datos exportados a initial_data.json"
        else
            print_error "Error al exportar datos"
            LOAD_DATA=false
        fi
        
        cd ..
    fi
fi

################################################################################
# PASO 6: Iniciar contenedores
################################################################################

print_header "PASO 6: Iniciando Contenedores"

print_info "Iniciando servicios..."

if docker compose up -d; then
    print_success "Contenedores iniciados"
else
    print_error "Error al iniciar contenedores"
    exit 1
fi

# Esperar a que los servicios estén listos
print_info "Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado
if docker compose ps | grep -q "healthy"; then
    print_success "Servicios iniciados correctamente"
else
    print_warning "Algunos servicios pueden no estar completamente listos"
    docker compose ps
fi

################################################################################
# PASO 7: Cargar datos iniciales (si se solicitó)
################################################################################

if [ "$LOAD_DATA" = true ] && [ -f "gimnasio_project/initial_data.json" ]; then
    print_header "PASO 7: Cargando Datos Iniciales"
    
    # Copiar archivo al contenedor
    print_info "Copiando datos al contenedor..."
    docker cp gimnasio_project/initial_data.json trainup_web:/app/initial_data.json
    
    # Cargar datos
    print_info "Cargando datos en PostgreSQL..."
    if docker compose exec -T web python manage.py loaddata initial_data.json 2>&1 | grep -q "Installed"; then
        print_success "Datos cargados exitosamente"
    else
        print_warning "Puede haber habido problemas al cargar datos. Revisa los logs:"
        print_info "docker compose logs web"
    fi
else
    print_header "PASO 7: Saltando Carga de Datos"
    print_info "No se cargarán datos iniciales"
fi

################################################################################
# PASO 8: Crear superusuario
################################################################################

print_header "PASO 8: Configuración de Usuario Administrador"

if [ "$LOAD_DATA" = true ]; then
    print_info "Los datos cargados ya incluyen usuarios"
    print_warning "Usuarios disponibles:"
    echo "  - admin"
    echo "  - administrador"
    print_info "Las contraseñas originales se mantienen"
else
    print_info "Creando superusuario..."
    echo ""
    echo -e "${YELLOW}Por favor, ingresa los datos del administrador:${NC}"
    
    docker compose exec web python manage.py createsuperuser
    
    if [ $? -eq 0 ]; then
        print_success "Superusuario creado exitosamente"
    else
        print_warning "El superusuario no fue creado. Puedes crearlo más tarde con:"
        echo "  docker compose exec web python manage.py createsuperuser"
    fi
fi

################################################################################
# PASO 9: Información final
################################################################################

print_header "🎉 DESPLIEGUE COMPLETADO"

echo -e "${GREEN}TrainUp está ahora corriendo!${NC}\n"

print_info "Servicios disponibles:"
echo "  🌐 Aplicación web:    http://localhost"
echo "  🔧 Django directo:    http://localhost:8000"
echo "  🗄️  PostgreSQL:        localhost:5432"
echo ""

print_info "Comandos útiles:"
echo "  Ver logs:              docker compose logs -f"
echo "  Detener servicios:     docker compose stop"
echo "  Reiniciar servicios:   docker compose restart"
echo "  Detener y limpiar:     docker compose down"
echo ""

# Verificar acceso
print_info "Verificando acceso a la aplicación..."
sleep 3

if curl -s http://localhost > /dev/null 2>&1; then
    print_success "✅ La aplicación responde correctamente"
    echo ""
    echo -e "${GREEN}🚀 Abre tu navegador en: http://localhost${NC}"
else
    print_warning "⚠️  No se pudo verificar el acceso. Verifica los logs:"
    echo "  docker compose logs web"
fi

echo ""
print_info "Para más información, consulta DEPLOYMENT.md"
echo ""

################################################################################
# Finalizar
################################################################################

exit 0
