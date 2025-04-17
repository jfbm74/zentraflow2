# RFC-0001: Ingesta de Correos desde Cuenta de Glosas (Google Workspace)

## Objetivo
Implementar un módulo que monitoree periódicamente una cuenta de correo electrónico (gestionada en Google Workspace) para detectar, filtrar y procesar automáticamente mensajes relacionados con glosas médicas, enviando los adjuntos relevantes al módulo de extracción de datos.

## Alcance
Este RFC cubre:
- Configuración del servicio de ingesta
- Conexión con la cuenta de correo mediante **Gmail API**
- Registro de actividad (log de eventos)
- Interfaz de administración del módulo

## Diseño Técnico

### Tecnologías y Librerías
- **Protocolo de correo**: **Gmail API**
- **Lenguaje**: Python
- **Framework sugerido**: Django + celery/apscheduler (para tareas recurrentes)
- **Librerías sugeridas**: **`google-auth`**, **`google-auth-oauthlib`**, **`googleapiclient.discovery`**, `python-dotenv`, `pandas` (para pre-procesamiento ligero si aplica)

### Funcionalidades

#### 1. Autenticación y Conexión a la cuenta de correo
- Uso de **Gmail API** con **OAuth 2.0** (configurado en **Google Cloud Platform - GCP**)
- Gestión segura de credenciales por cliente (Client ID, Client Secret, y probablemente Refresh Tokens almacenados de forma segura, o mediante Cuentas de Servicio si aplica delegación a nivel de dominio).
- Token de acceso renovable automáticamente usando el refresh token o el mecanismo de cuenta de servicio.

#### 2. Verificación periódica (cada 5 minutos)
- Verificar nuevos correos en la carpeta designada (ej. INBOX).
- Utilizar **`users().messages().list()`** de Gmail API con parámetros de consulta (`q`) para filtrar:
  - `is:unread` (o estrategia equivalente basada en etiquetas/marcado).
  - `after:{timestamp}` (basado en el último chequeo exitoso).
- Recuperar IDs de mensajes (`messageId`).
- Para cada `messageId`, usar **`users().messages().get()`** para obtener metadatos (Remitente, Asunto, Fecha) y verificar presencia de adjuntos.

#### 3. Reglas de Filtrado Configurables
Cada correo (basado en sus metadatos) se evalúa contra un conjunto de reglas (`ReglaFiltrado`) definidas por el usuario para el cliente específico:
- Condiciones por:
  - **Remitente** (contiene)
  - **Asunto** (contiene, coincide, regex opcional - post MVP)
- Acciones:
  - **Procesar** (se descargan adjuntos y se envía a módulo de extracción)
  - **Ignorar** (se marca como leído/procesado y se omite)
- Estado de la regla: Activa / Inactiva
- **Necesario:** Definir prioridad o lógica de aplicación si múltiples reglas coinciden.

#### 4. Registro de Actividad
- Guardar eventos en tabla/log (`CorreoIngestado`):
  - Correo recibido: `message_id_google`, `remitente`, `asunto`, `fecha_recepcion`, `cliente_id`.
  - Resultado del filtrado: `estado` ('pendiente', 'ignorado', 'error'), `regla_aplicada`.
  - Información de adjuntos: `adjuntos_detectados` (contador).
  - Resultado de la descarga/handoff: Éxito/fallo (puede actualizar el estado).

#### 5. Interfaz Administrativa Web
- Visualizar configuración actual de la cuenta de correo monitoreada para el cliente.
- Botón de "Verificar ahora" (dispara tarea de verificación manual).
- Tabla con historial de actividad (`CorreoIngestado`) reciente para el cliente.
- Editor de reglas de filtrado (`ReglaFiltrado`) para el cliente (CRUD).

## Endpoints / Rutas Propuestas (Backend API para Frontend)
- `GET /ingesta-correo` → Panel principal (renderiza `ingesta_correo.html`)
- `POST /ingesta-correo/verificar` → Ejecutar ingesta manual (dispara tarea Celery/APScheduler)
- `GET /ingesta-correo/logs` → API para consultar logs/`CorreoIngestado` recientes (para la tabla del historial)
- `GET /api/ingesta-correo/reglas` → API para obtener las reglas del cliente.
- `POST /api/ingesta-correo/reglas` → API para crear una nueva regla.
- `PUT /api/ingesta-correo/reglas/<int:id_regla>` → API para actualizar una regla.
- `DELETE /api/ingesta-correo/reglas/<int:id_regla>` → API para eliminar una regla.
- `PATCH /api/ingesta-correo/reglas/<int:id_regla>/toggle` → API para activar/desactivar una regla.

## Modelos de Datos
### CorreoIngestado
- `id`: UUID / Integer primary key
- `cliente_id`: ForeignKey(Cliente.id)
- `message_id_google`: String (ID único del mensaje en Gmail)
- `remitente`: String
- `asunto`: String
- `fecha_recepcion`: Datetime
- `estado`: ['pendiente', 'procesado', 'ignorado', 'error_filtrado', 'error_descarga', 'error_handoff'] (Más granularidad)
- `adjuntos_detectados`: Integer
- `regla_aplicada_id`: ForeignKey(ReglaFiltrado.id) (opcional)
- `detalles_error`: Text (opcional)
- `fecha_procesamiento`: Datetime (opcional)

### ReglaFiltrado
- `id`: UUID / Integer primary key
- `cliente_id`: ForeignKey(Cliente.id)
- `nombre`: String
- `condicion_tipo`: ['remitente', 'asunto']
- `condicion_operador`: ['contiene', 'no_contiene', 'igual_a'] (Considerar case-insensitivity)
- `condicion_valor`: String
- `accion`: ['procesar', 'ignorar']
- `prioridad`: Integer (para orden de aplicación)
- `estado`: ['activa', 'inactiva']

## Seguridad
- **Credenciales de API de Google** (Client ID/Secret, Refresh Tokens, o claves de Cuenta de Servicio) deben protegerse adecuadamente (variables de entorno, secrets manager, BD cifrada asociada al cliente).
- **Permisos OAuth 2.0** solicitados deben ser los mínimos necesarios (principio de menor privilegio). Generalmente `gmail.readonly` para leer/filtrar, y potencialmente `gmail.modify` si se desea marcar correos como leídos o moverlos.
- Validación contra spam/malware (a futuro, podría integrarse con herramientas externas o APIs de seguridad).

## Dependencias
- Módulo de Extracción de Datos (RFC-0002)
- **Configuración previa del proyecto en GCP, habilitación de Gmail API y obtención de credenciales OAuth 2.0 por cliente.**
- Configuración de Celery/APScheduler para tareas recurrentes.

## Historial y Auditoría
- Tabla `CorreoIngestado` sirve como log principal.
- Logs de aplicación (`logging`) deben registrar detalles técnicos y errores.
- Log descargable desde el frontend (consultando `CorreoIngestado`).

## Estado Esperado del MVP
✅ Autenticación y lectura de correo vía **Gmail API**.
✅ Aplicación de reglas simples (basadas en remitente/asunto, sin orden complejo).
✅ Registro básico de eventos en `CorreoIngestado`.
✅ Panel web funcional (visualización de config, historial básico, CRUD simple de reglas).
❌ Flujo OAuth 2.0 completo para que el cliente autorice (puede requerir configuración manual inicial en MVP).
❌ Filtros avanzados por regex, cuerpo, etc. (etapa futura).
❌ Antivirus/Malware scanning (etapa futura).
❌ Gestión avanzada de prioridad de reglas (etapa futura).