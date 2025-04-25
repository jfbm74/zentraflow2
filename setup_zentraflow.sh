#!/bin/bash

echo "===== Configurando entorno para ZentraFlow ====="

# Colores para mejorar la legibilidad
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar si Python está instalado
echo -e "${YELLOW}Verificando instalación de Python...${NC}"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python está instalado: ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}✗ Python no está instalado. Por favor instala Python 3.8+${NC}"
    exit 1
fi

# Verificar si pip está instalado
echo -e "${YELLOW}Verificando instalación de pip...${NC}"
if command -v pip3 >/dev/null 2>&1; then
    PIP_VERSION=$(pip3 --version)
    echo -e "${GREEN}✓ pip está instalado: ${PIP_VERSION}${NC}"
else
    echo -e "${RED}✗ pip no está instalado. Instalando pip...${NC}"
    python3 -m ensurepip --upgrade
fi

# Verificar si está activo un entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}No se detectó entorno virtual activo${NC}"
    
    # Verificar si existe el directorio venv
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Entorno virtual 'venv' encontrado. Activando...${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}Creando nuevo entorno virtual 'venv'...${NC}"
        python3 -m venv venv
        source venv/bin/activate
    fi
else
    echo -e "${GREEN}✓ Entorno virtual activo: $VIRTUAL_ENV${NC}"
fi

# Instalar dependencias de Django
echo -e "${YELLOW}Instalando dependencias de Django...${NC}"
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers

# Instalar Celery y dependencias
echo -e "${YELLOW}Instalando Celery y dependencias...${NC}"
pip install celery redis

# Detectar sistema operativo
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo -e "${YELLOW}Sistema detectado: macOS${NC}"
    
    # Verificar si Homebrew está instalado
    if command -v brew >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Homebrew está instalado${NC}"
    else
        echo -e "${YELLOW}Instalando Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Verificar si Redis está instalado
    if brew list redis &>/dev/null; then
        echo -e "${GREEN}✓ Redis está instalado${NC}"
    else
        echo -e "${YELLOW}Instalando Redis...${NC}"
        brew install redis
    fi
    
    # Iniciar servicio Redis
    echo -e "${YELLOW}Iniciando servicio Redis...${NC}"
    brew services start redis
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo -e "${YELLOW}Sistema detectado: Linux${NC}"
    
    # Verificar si Redis está instalado (para Ubuntu/Debian)
    if command -v redis-server >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis está instalado${NC}"
    else
        echo -e "${YELLOW}Instalando Redis...${NC}"
        sudo apt-get update
        sudo apt-get install -y redis-server
    fi
    
    # Iniciar servicio Redis
    echo -e "${YELLOW}Iniciando servicio Redis...${NC}"
    sudo systemctl start redis
    sudo systemctl enable redis
    
else
    echo -e "${RED}Sistema operativo no soportado. Por favor instala Redis manualmente${NC}"
fi

# Verificar estructura del proyecto
echo -e "${YELLOW}Verificando estructura del proyecto...${NC}"

# Verificar si existe el directorio zentraflow
if [ ! -d "zentraflow" ]; then
    echo -e "${RED}✗ No se encontró el directorio 'zentraflow'${NC}"
    exit 1
fi

# Verificar archivos clave
if [ ! -f "zentraflow/celery.py" ]; then
    echo -e "${RED}✗ No se encontró 'zentraflow/celery.py'${NC}"
    echo -e "${YELLOW}Creando archivo 'zentraflow/celery.py'...${NC}"
    
    # Crear archivo celery.py
    cat > zentraflow/celery.py << 'EOF'
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configurar variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentraflow.settings')

app = Celery('zentraflow')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
EOF
    
    echo -e "${GREEN}✓ Archivo 'zentraflow/celery.py' creado${NC}"
fi

# Verificar __init__.py en el paquete zentraflow
if [ ! -f "zentraflow/__init__.py" ]; then
    echo -e "${RED}✗ No se encontró 'zentraflow/__init__.py'${NC}"
    echo -e "${YELLOW}Creando archivo 'zentraflow/__init__.py'...${NC}"
    
    # Crear archivo __init__.py
    cat > zentraflow/__init__.py << 'EOF'
from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app

__all__ = ['celery_app']
EOF
    
    echo -e "${GREEN}✓ Archivo 'zentraflow/__init__.py' creado${NC}"
fi

# Verificar configuración de Celery en settings.py
if grep -q "CELERY_BROKER_URL" zentraflow/settings.py; then
    echo -e "${GREEN}✓ Configuración de Celery encontrada en settings.py${NC}"
else
    echo -e "${YELLOW}Agregando configuración de Celery a settings.py...${NC}"
    
    # Agregar configuración de Celery a settings.py
    cat >> zentraflow/settings.py << 'EOF'

# Configuración de Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Programación de tareas de Celery
CELERY_BEAT_SCHEDULE = {
    'sync-oauth-status': {
        'task': 'apps.ingesta_correo.tasks.sync_oauth_and_service_status',
        'schedule': 60.0 * 30,  # Ejecutar cada 30 minutos
    },
}
EOF
    
    echo -e "${GREEN}✓ Configuración de Celery agregada a settings.py${NC}"
fi

# Verificar tasks.py en apps/ingesta_correo
if [ ! -d "apps/ingesta_correo" ]; then
    echo -e "${RED}✗ No se encontró el directorio 'apps/ingesta_correo'${NC}"
    exit 1
fi

if [ ! -f "apps/ingesta_correo/tasks.py" ]; then
    echo -e "${RED}✗ No se encontró 'apps/ingesta_correo/tasks.py'${NC}"
    echo -e "${YELLOW}Creando archivo 'apps/ingesta_correo/tasks.py'...${NC}"
    
    # Crear archivo tasks.py
    cat > apps/ingesta_correo/tasks.py << 'EOF'
from celery import shared_task
from apps.configuracion.services.oauth_verification_service import OAuthVerificationService
from apps.tenants.models import Tenant

@shared_task
def sync_oauth_and_service_status():
    """Tarea programada para sincronizar el estado de OAuth y el servicio de ingesta."""
    print("Iniciando sincronización de OAuth...")
    for tenant in Tenant.objects.filter(is_active=True):
        # Verificar y actualizar el estado
        result = OAuthVerificationService.verify_connection(tenant)
        print(f"Tenant {tenant.id} ({tenant.name}): {'Éxito' if result.get('success') else 'Error'}")
    return "Sincronización OAuth completada"
EOF
    
    echo -e "${GREEN}✓ Archivo 'apps/ingesta_correo/tasks.py' creado${NC}"
fi

# Crear un script para iniciar todos los servicios
echo -e "${YELLOW}Creando script de inicio...${NC}"

cat > start_zentraflow.sh << 'EOF'
#!/bin/bash

echo "===== Iniciando servicios de ZentraFlow ====="

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Entorno virtual activado"
else
    echo "✗ No se encontró el entorno virtual 'venv'"
    exit 1
fi

# Verificar si Redis está funcionando
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping | grep -q "PONG"; then
        echo "✓ Redis está funcionando"
    else
        echo "✗ Redis no está respondiendo. Intentando iniciar..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services restart redis
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl restart redis
        fi
    fi
fi

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate

# Iniciar Celery worker en segundo plano
echo "Iniciando Celery worker..."
celery -A zentraflow worker --loglevel=info --concurrency=1 --uid=$(id -u) > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "✓ Celery worker iniciado (PID: $WORKER_PID)"

# Iniciar Celery beat en segundo plano
echo "Iniciando Celery beat..."
celery -A zentraflow beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "✓ Celery beat iniciado (PID: $BEAT_PID)"

# Iniciar servidor Django
echo "Iniciando servidor Django..."
python manage.py runserver

# Este código solo se ejecuta si el servidor Django se detiene
echo "Deteniendo servicios de Celery..."
kill $WORKER_PID $BEAT_PID
echo "✓ Servicios detenidos"
EOF

chmod +x start_zentraflow.sh

# Crear directorio de logs
mkdir -p logs

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Configuración completada${NC}"
echo -e "${GREEN}Para iniciar la aplicación, ejecuta:${NC}"
echo -e "${YELLOW}./start_zentraflow.sh${NC}"
echo -e "${GREEN}==========================================${NC}"