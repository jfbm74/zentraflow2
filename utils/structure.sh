#!/bin/bash

# Script para crear la estructura de directorios y archivos para Zentraflow
# Excluye la creación de archivos/directorios dentro de 'zentraflow/'

echo "Creando estructura de directorios y archivos para Zentraflow..."

# Crear directorio de aplicaciones
mkdir -p apps/core/migrations
mkdir -p apps/tenants/migrations
mkdir -p apps/authentication/migrations
mkdir -p apps/authentication/services
mkdir -p apps/authentication/api
mkdir -p apps/authentication/web

# Crear archivos Python en apps/core
touch apps/core/__init__.py
touch apps/core/apps.py
touch apps/core/exceptions.py
touch apps/core/middleware.py
touch apps/core/utils.py

# Crear archivos Python en apps/tenants
touch apps/tenants/__init__.py
touch apps/tenants/admin.py
touch apps/tenants/apps.py
touch apps/tenants/models.py
touch apps/tenants/middleware.py
touch apps/tenants/selectors.py
touch apps/tenants/services.py
touch apps/tenants/migrations/__init__.py

# Crear archivos Python en apps/authentication
touch apps/authentication/__init__.py
touch apps/authentication/admin.py
touch apps/authentication/apps.py
touch apps/authentication/models.py
touch apps/authentication/migrations/__init__.py

# Crear archivos en authentication/services
touch apps/authentication/services/__init__.py
touch apps/authentication/services/auth_service.py
touch apps/authentication/services/password_service.py

# Crear archivos en authentication/api
touch apps/authentication/api/__init__.py
touch apps/authentication/api/serializers.py
touch apps/authentication/api/views.py
touch apps/authentication/api/urls.py

# Crear archivos en authentication/web
touch apps/authentication/web/__init__.py
touch apps/authentication/web/forms.py
touch apps/authentication/web/views.py
touch apps/authentication/web/urls.py

# Crear directorios para archivos estáticos
mkdir -p static/css/authentication
mkdir -p static/js/authentication
mkdir -p static/images

# Crear archivos estáticos
touch static/css/authentication/login.css
touch static/js/authentication/main.js
touch static/images/favicon.ico

# Crear directorios para plantillas
mkdir -p templates/authentication

# Crear archivos de plantillas
touch templates/base.html
touch templates/authentication/login.html
touch templates/authentication/password_reset.html
touch templates/authentication/password_reset_done.html

# Crear directorio de pruebas
mkdir -p tests/test_tenants
mkdir -p tests/test_authentication

# Crear archivos de pruebas
touch tests/__init__.py
touch tests/test_tenants/__init__.py
touch tests/test_authentication/__init__.py

# Crear directorio de requisitos
mkdir -p requirements

# Crear archivos de requisitos
touch requirements/base.txt
touch requirements/development.txt
touch requirements/production.txt

echo "Estructura de directorios y archivos creada con éxito!"