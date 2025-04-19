======================================================================
RFC-0002-03: Configuración del Servicio de Ingesta Programada
----------------------------------------------------------

### Descripción

Implementar el mecanismo base para ejecutar el servicio de ingesta según el intervalo configurado y gestionar su estado (activo/pausado).

### Requisitos Funcionales

1.  Crear un servicio programado que:
    -   Se ejecute automáticamente según el intervalo configurado
    -   Respete configuraciones específicas por tenant
    -   Actualice dinámicamente su programación cuando cambie el intervalo
    -   Permita pausar/reanudar el servicio sin reiniciar la aplicación
2.  Implementar indicadores de estado del servicio:
    -   Mostrar estado actual (activo/pausado)
    -   Indicar tiempo hasta la próxima ejecución
    -   Registrar última verificación realizada
3.  Desarrollar comandos de control manual:
    -   Botón "Verificar ahora" para ejecución inmediata
    -   Botón "Pausar servicio" para detener temporalmente

### Criterios de Aceptación

-   El servicio debe respetar exactamente el intervalo configurado
-   Los cambios de configuración deben aplicarse sin reiniciar la aplicación
-   El estado del servicio debe ser persistente (recordarse después de reinicios)
-   La interfaz debe reflejar correctamente el estado actual