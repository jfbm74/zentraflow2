ZentraFlow
==========

ZentraFlow es una plataforma multi-tenant para automatizar la ingesta y procesamiento de correos electrónicos. La aplicación permite a los usuarios configurar conexiones OAuth con servicios de correo (como Gmail), monitorear carpetas específicas y procesar automáticamente los mensajes entrantes para extraer información relevante.

Características principales
---------------------------

*   🔐 **Autenticación y autorización** basada en roles y tenants
    
*   📧 **Ingesta automatizada de correos** mediante OAuth 2.0
    
*   📊 **Dashboard** para monitorización en tiempo real
    
*   🔄 **Sincronización automática** y renovación de tokens OAuth
    
*   🔍 **Procesamiento inteligente** de correos y adjuntos
    
*   📝 **Extracción de glosas** de los mensajes procesados
    
*   🚀 **Arquitectura escalable** basada en tareas asíncronas
    

Requisitos previos
------------------

*   Python 3.8+
    
*   Redis (para Celery)
    
*   Acceso a una cuenta de correo compatible con OAuth 2.0 (Gmail)
    

Instalación
-----------

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/zentraflow.git
cd zentraflow
```

### 2. Crear un entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

```bash
python manage.py migrate
```

### 5. Crear un superusuario

```bash
python manage.py createsuperuser
```

### 6. Iniciar los servicios

```bash
# Iniciar Redis (requerido para Celery)
brew services start redis  # En macOS con Homebrew
# sudo systemctl start redis  # En Linux

# Iniciar Celery worker
celery -A zentraflow worker --loglevel=info

# Iniciar Celery beat (para tareas programadas)
celery -A zentraflow beat --loglevel=info

# En otra terminal, iniciar el servidor Django
python manage.py runserver
```

También puedes usar el script `start_zentraflow.sh` para iniciar todos los servicios de forma automática.

Configuración
-------------

### Configuración de OAuth para Gmail

1.  Accede a la [Consola de Google Cloud](https://console.cloud.google.com/)
    
2.  Crea un nuevo proyecto o selecciona uno existente
    
3.  Activa las APIs de Gmail
    
4.  Configura las credenciales OAuth 2.0
    
5.  Añade los URI de redirección autorizados (por defecto: http://localhost:8000/configuracion/oauth/callback/)
    
6.  Copia el ID de cliente y el Secret en la configuración de ZentraFlow
    

### Configuración en ZentraFlow

1.  Accede al panel de administración (/admin/)
    
2.  Crea un nuevo tenant (cliente)
    
3.  Configura las credenciales OAuth en la sección de Configuración
    
4.  Autoriza la aplicación siguiendo el flujo OAuth
    
5.  Configura las carpetas de correo a monitorear y la frecuencia de verificación
    

Estructura del proyecto
-----------------------

```
zentraflow/
├── apps/
│   ├── authentication/   # Gestión de usuarios y autenticación
│   ├── configuracion/   # Configuración del sistema y OAuth
│   ├── core/            # Componentes compartidos
│   ├── ingesta_correo/  # Ingesta y procesamiento de correos
│   └── tenants/         # Gestión de clientes multi-tenant
├── static/
│   ├── css/            # Estilos CSS
│   ├── js/             # Scripts JavaScript
│   └── images/         # Imágenes y recursos gráficos
├── templates/          # Plantillas HTML
├── zentraflow/         # Configuración del proyecto Django
│   ├── celery.py      # Configuración de Celery
│   ├── settings.py     # Configuración de Django
│   └── urls.py        # Definición de rutas
├── manage.py
└── README.md
```

Tareas programadas
------------------

ZentraFlow utiliza Celery para ejecutar tareas programadas, como la sincronización y renovación de tokens OAuth. La tarea principal es sync\_oauth\_and\_service\_status, que se ejecuta cada 30 minutos para verificar y refrescar los tokens OAuth cuando sea necesario.

Flujo de trabajo
----------------

1.  **Configuración**: El administrador configura las credenciales OAuth para el tenant
    
2.  **Autorización**: Se autoriza el acceso a la cuenta de correo mediante OAuth
    
3.  **Monitoreo**: El sistema monitorea la carpeta de correo configurada
    
4.  **Procesamiento**: Los nuevos correos son procesados y se extraen las glosas
    
5.  **Renovación automática**: El sistema mantiene los tokens OAuth actualizados
    

Solución de problemas
---------------------

### Problemas con Celery

```bash
# Verificar que Redis está funcionando
redis-cli ping  # Debería responder PONG

# Verificar logs de Celery
cat logs/celery_worker.log
cat logs/celery_beat.log

# Reiniciar servicios
brew services restart redis  # En macOS
celery -A zentraflow worker --loglevel=info
celery -A zentraflow beat --loglevel=info
```

### Problemas de OAuth

Si los tokens OAuth no se renuevan automáticamente:

1.  Verificar que la tarea de Celery esté ejecutándose correctamente
    
2.  Comprobar que las credenciales OAuth sean válidas
    
3.  Verificar la configuración en la sección de Configuración de ZentraFlow
    
4.  Revisar los logs para identificar errores específicos
    

Licencia
--------

Copyright © 2025 ZentraFlow. Todos los derechos reservados.

Contacto
--------

Para soporte o consultas, contacte a: [support@zentraflow.com](mailto:support@zentraflow.com)