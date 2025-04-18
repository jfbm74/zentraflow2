from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta

from apps.configuracion.models import EmailOAuthCredentials
from ..models import CorreoIngesta, EstadisticaDiaria, LogActividad, ServicioIngesta

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
    def get_system_status(tenant):
        """Obtiene el estado actual del sistema de ingesta."""
        # Verificar si el servicio está activo
        try:
            servicio = ServicioIngesta.objects.get(tenant=tenant)
            servicio_activo = servicio.activo
            ultima_verificacion = servicio.ultima_verificacion
        except ServicioIngesta.DoesNotExist:
            servicio_activo = False
            ultima_verificacion = None
        
        # Verificar si hay errores recientes (últimas 24 horas)
        yesterday = timezone.now() - timedelta(days=1)
        errores_recientes = LogActividad.objects.filter(
            tenant=tenant,
            fecha_hora__gte=yesterday,
            evento='ERROR_PROCESAMIENTO'
        ).count()
        
        # Verificar último correo procesado
        ultimo_correo = CorreoIngesta.objects.filter(
            servicio__tenant=tenant,
            estado='PROCESADO'
        ).order_by('-fecha_procesamiento').first()
        
        return {
            'servicio_activo': servicio_activo,
            'ultima_verificacion': ultima_verificacion,
            'ultimo_correo_procesado': ultimo_correo.fecha_procesamiento if ultimo_correo else None,
            'errores_recientes': errores_recientes,
            'estado_general': 'error' if errores_recientes > 5 else 
                              'warning' if errores_recientes > 0 else 
                              'inactive' if not servicio_activo else 
                              'success'
        }
    
    @staticmethod
    def get_recent_activity(tenant, limit=5):
        """Obtiene la actividad reciente del sistema."""
        logs = LogActividad.objects.filter(
            tenant=tenant
        ).order_by('-fecha_hora')[:limit]
        
        return logs
    
    @staticmethod
    def get_system_status(tenant):
        """Obtiene el estado actual del sistema de ingesta."""
        # Verificar si el servicio está activo
        try:
            servicio, created = ServicioIngesta.objects.get_or_create(tenant=tenant)
            servicio_activo = servicio.activo
            ultima_verificacion = servicio.ultima_verificacion
        except ServicioIngesta.DoesNotExist:
            servicio_activo = False
            ultima_verificacion = None
        
        # Verificar configuración de OAuth
        try:
            credentials = EmailOAuthCredentials.objects.get(tenant=tenant)
            oauth_configured = credentials.client_id and credentials.client_secret
            oauth_authorized = credentials.authorized
            oauth_token_valid = credentials.is_token_valid()
            email_address = credentials.email_address
            
            # Si OAuth no está autorizado, el servicio no debería estar activo
            if servicio_activo and (not oauth_authorized or not oauth_token_valid):
                servicio.activo = False
                servicio.save()
                servicio_activo = False
                
                # Registrar en log
                LogActividad.objects.create(
                    tenant=tenant,
                    evento='SERVICIO_DETENIDO',
                    detalles="Servicio de ingesta detenido automáticamente por estado inválido de credenciales OAuth",
                )
        except EmailOAuthCredentials.DoesNotExist:
            oauth_configured = False
            oauth_authorized = False
            oauth_token_valid = False
            email_address = None
    
