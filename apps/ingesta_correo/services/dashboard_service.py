from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
import logging

from apps.configuracion.models import EmailConfig
from ..models import CorreoIngesta, EstadisticaDiaria, LogActividad, ServicioIngesta

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_metrics_last_24h(tenant):
        """Obtiene métricas de las últimas 24 horas."""
        yesterday = timezone.now() - timedelta(days=1)
        correos = CorreoIngesta.objects.filter(
            servicio__tenant=tenant,
            fecha_recepcion__gte=yesterday
        )
        
        return {
            'correos_procesados': correos.filter(estado='PROCESADO').count(),
            'glosas_extraidas': correos.aggregate(total=Sum('glosas_extraidas'))['total'] or 0,
            'pendientes': correos.filter(estado='PENDIENTE').count(),
            'errores': correos.filter(estado='ERROR').count(),
        }
    
    @staticmethod
    def get_daily_trends(tenant, days=7):
        """Obtiene tendencias diarias para los últimos N días."""
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Obtener estadísticas diarias
        stats = EstadisticaDiaria.objects.filter(
            tenant=tenant,
            fecha__gte=start_date
        ).order_by('fecha')
        
        # Si no hay suficientes datos, completar con ceros
        existing_dates = {stat.fecha for stat in stats}
        
        result = []
        current_date = start_date
        end_date = timezone.now().date()
        
        while current_date <= end_date:
            if current_date in existing_dates:
                stat = next(s for s in stats if s.fecha == current_date)
                result.append({
                    'fecha': current_date.strftime('%Y-%m-%d'),
                    'correos_procesados': stat.correos_procesados,
                    'glosas_extraidas': stat.glosas_extraidas,
                    'pendientes': stat.pendientes,
                    'errores': stat.errores
                })
            else:
                result.append({
                    'fecha': current_date.strftime('%Y-%m-%d'),
                    'correos_procesados': 0,
                    'glosas_extraidas': 0,
                    'pendientes': 0,
                    'errores': 0
                })
            current_date += timedelta(days=1)
        
        return result
    
    @staticmethod
    def get_recent_activity(tenant, limit=5):
        """Obtiene la actividad reciente del sistema."""
        logger.debug(f"Obteniendo actividad reciente para tenant: {tenant.id}, límite: {limit}")
        logs = LogActividad.objects.filter(
            tenant=tenant
        ).order_by('-fecha_hora')[:limit]
        
        logger.debug(f"Actividad reciente obtenida: {logs.count()} registros")
        return logs
    
    @staticmethod
    def get_system_status(tenant):
        """Obtiene el estado actual del sistema de ingesta."""
        try:
            # Verificar servicio de ingesta
            servicio = ServicioIngesta.objects.filter(tenant=tenant).first()
            servicio_activo = servicio and servicio.activo if servicio else False
            
            # Verificar configuración de correo
            try:
                config = EmailConfig.objects.get(tenant=tenant)
                email_configured = True
                email_connected = config.connection_status == 'conectado'
                email_address = config.email_address
                
                logger.debug(f"Email - configurado: {email_configured}, conectado: {email_connected}")
                logger.debug(f"Email address: {email_address}")
                
                # Si el correo no está conectado, el servicio no debería estar activo
                if servicio_activo and not email_connected:
                    servicio.activo = False
                    servicio.save()
                    servicio_activo = False
                    
                    # Registrar en log
                    LogActividad.objects.create(
                        tenant=tenant,
                        evento='SERVICIO_DETENIDO',
                        detalles="Servicio de ingesta detenido automáticamente por estado inválido de conexión de correo",
                    )
                    logger.debug("Servicio desactivado automáticamente por conexión de correo inválida")
            except EmailConfig.DoesNotExist:
                email_configured = False
                email_connected = False
                email_address = None
                logger.debug("Configuración de correo no encontrada")
            
            # Obtener última ejecución
            ultima_ejecucion = None
            if servicio:
                ultima_ejecucion = servicio.historial.order_by('-fecha_inicio').first()
            
            # Construir respuesta
            response = {
                'servicio_activo': servicio_activo,
                'email_configured': email_configured,
                'email_connected': email_connected,
                'email_address': email_address,
                'ultima_ejecucion': {
                    'fecha': ultima_ejecucion.fecha_inicio if ultima_ejecucion else None,
                    'estado': ultima_ejecucion.estado if ultima_ejecucion else None,
                    'correos_procesados': ultima_ejecucion.correos_procesados if ultima_ejecucion else 0,
                    'glosas_extraidas': ultima_ejecucion.glosas_extraidas if ultima_ejecucion else 0,
                    'mensaje_error': ultima_ejecucion.mensaje_error if ultima_ejecucion else None
                } if ultima_ejecucion else None
            }
            
            logger.debug(f"Estado del sistema para tenant {tenant.id}: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error al obtener estado del sistema para tenant {tenant.id}: {str(e)}")
            return {
                'servicio_activo': False,
                'email_configured': False,
                'email_connected': False,
                'email_address': None,
                'ultima_ejecucion': None,
                'error': str(e)
            }