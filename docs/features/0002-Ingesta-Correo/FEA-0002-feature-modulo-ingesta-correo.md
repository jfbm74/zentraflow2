Feature — Módulo de Ingesta de Correo
-------------------------------------

**ID:** FEA‑ING‑CORREO‑001  **Versión:** 1.0  **Autor:** Juan Bustamante  **Fecha:** 17‑abr‑2025

### 1. Propósito

Dotar a ZentraFlow de un módulo autónomo que conecte cuentas de correo, aplique reglas de filtrado y registre la actividad para alimentar el proceso de gestión de glosas. El objetivo es reemplazar tareas manuales de clasificación, minimizar errores y proveer trazabilidad en tiempo real.

### 2. Problema a resolver

*   La recepción de glosas vía e‑mail es manual y propensa a fallos.
    
*   No existe visibilidad centralizada del estado del servicio ni de los errores de ingesta.
    
*   Los registros históricos crecen sin control y degradan la base de datos.
    

### 3. Valor de negocio / beneficios

Beneficio                                           Impacto 
Automatización de clasificación de glosas           Reduce ≈ 90 % el tiempo operativo del personal de facturación.Visibilidad en tiempo real                          Mejora la detección de fallos y la toma de decisiones.
Escalabilidad multi‑tenant                          Acelera la incorporación de nuevas clínicas sin código adicional.

### 4. Alcance (Scope)

*   **Conexión de cuentas** IMAP/OAuth2 con intervalo configurable.
    
*   **Reglas de filtrado** (campo, operador, valor, acción, prioridad).
    
*   **Procesamiento de adjuntos** y persistencia en almacenamiento lógico (S3‑like).
    
*   **Dashboard** con estado, estadísticas diarias y control Start/Stop/Verify.
    
*   **Actividad** paginada con filtros de fecha, remitente, regla, estado.
    
*   **API REST** para logs y configuración.
    
*   **Retención** y archivado automático > 90 días.
    
*   **Roles y permisos** (Lectura, Operador, Administrador).
    
*   **Notificaciones** por error o token próximo a expirar.
    

### 5. Fuera de alcance (Out of scope)

*   Procesamiento semántico de PDF (lo cubrirá el módulo “Extracción de Glosas”).
    
*   Integración con sistemas de billing externos (se definirá en otra feature).
    

### 6. Stakeholders

*   **Usuarios finales:** Personal de facturación, Equipo de Calidad.
    
*   **Operaciones TI:** SRE, DevOps.
    
*   **Negocio:** Dirección Administrativa de la clínica, Dirección de ZentraTek.
    

### 7. Historias de usuario clave

Como (un) usuario final, quiero: ver el estado de la ingesta de mi cuenta de correo de clínica saber si los correos están siendo procesados correctamente y si los correos están siendo procesados correctamente, para poder saber cuándo se procesan y cuánto tiempo tarda en hacerlo.Tambien quiero  crear y probar una nueva regla de filtrado y automatizar las glosas de un nuevo aseguradorUS‑003Administradorpausar o reanudar el serviciorealizar mantenimientos sin perder correos. asi mismo buscar eventos por remitente y rango de fechasinvestigar incidentes rápidamente para encontrar incidentes rápidamente y recibir alertas cuando la tasa de errores supere 5 % y reaccionar antes de que afecte al cliente

### 8. Flujo de usuario (Happy Path)

1.  Usuario accede al menú **Ingesta de Correo** (pre‑autenticado).
    
2.  Ve un dashboard con:
    
    *   Estado = Activo, último heartbeat y cuenta asociada.
        
    *   Métricas del día (correos procesados, glosas extraídas, errores).
        
3.  Hace clic en **Reglas** → agrega una regla y la prueba con un asunto de ejemplo.
    
4.  La regla se aplica a los siguientes correos; la tabla de actividad refleja los eventos.
    
5.  Si ocurre un error, el usuario recibe un toast notification y puede abrir detalles.
    

### 9. Diseño de UX / UI

*   Layout responsive con **header** de estado y **tres pestañas**: Configuración, Reglas, Registros.
    
*   Tabla de reglas editable inline con drag‑and‑drop de prioridad.
    
*   Tabla de actividad con paginación server‑side y filtros laterales.
    
*   Colores semafóricos: verde (Activo), amarillo (Pausado), rojo (Error).
    
    

### 10. Requisitos funcionales (RF)

ID          Requisito                                                                               Prioridad   
RF‑01       El sistema debe conectar múltiples cuentas de correo por tenant.                        Alta
RF‑02       Debe existir un cron/worker que recupere correos cada _n_ minutos.                      Alta
RF‑03       Las reglas deben evaluarse en orden de prioridad y soportar operadores _contiene_, _igual_, _regex_.Alta
RF‑04       El usuario debe filtrar logs por fecha, remitente, estado y texto libre.                Media
RF‑05       Debe existir exportación CSV que respete los filtros activos.                           Media
RF‑06       Los registros se deben archivar/compactar después de 90 días.                           Media

### 11. Requisitos no funcionales (RNF)

ID          Descripción                                             Métrica
RNF‑01      Latencia de respuesta de API de logs                    ≤ 200 ms (P95)
RNF‑02      Disponibilidad del servicio de ingesta                  ≥ 99,5 % mensual
RNF‑03      Cobertura de pruebas                                    ≥ 90 % líneas en servicios críticos


### 12. Aceptación / Definición de “Done”

*   Todas las historias tienen pruebas end‑to‑end en CI.
        

### 13. Métricas y KPIs

*   % Correos procesados sin error.
    
*   Tiempo medio entre recepción de correo y extracción de adjunto.
    
*   Uso de CPU/memoria del worker de ingesta.
    

### 14. Riesgos y mitigaciones

RiesgoImpactoMitigaciónExceso de logs → BD lentaAltoParticionado + archivado + índicesToken OAuth vencidoMedioAlerta preventiva 72 h antesCambios en políticas IMAP del proveedorMedioCliente abstracto + fallback a Gmail API

### 15. Dependencias

*   Servicio Celery + Redis (ya disponible para otros módulos).
    
*   Repositorio multitenant y middleware existente.
    
*   Configuración de credenciales OAuth en Google Cloud Console.