from .models import ConfiguracionTenant, ReglaFiltracionCorreo, RangoIP, HistorialSincronizacion

class ConfiguracionService:
    """Servicio para manejar la configuración de clientes."""
    
    @staticmethod
    def get_configuracion(tenant):
        """Obtener la configuración para un tenant dado."""
        configuracion, created = ConfiguracionTenant.objects.get_or_create(tenant=tenant)
        return configuracion
    
    @staticmethod
    def guardar_configuracion_general(tenant, datos, usuario):
        """Guardar la configuración general del cliente."""
        configuracion = ConfiguracionService.get_configuracion(tenant)
        
        # Actualizar campos
        configuracion.zona_horaria = datos.get('zona_horaria', 'America/Bogota')
        configuracion.formato_fecha = datos.get('formato_fecha', 'DD/MM/YYYY')
        configuracion.idioma = datos.get('idioma', 'es')
        
        # Módulos habilitados
        configuracion.modulo_ingesta = datos.get('modulo_ingesta', True)
        configuracion.modulo_extraccion = datos.get('modulo_extraccion', True)
        configuracion.modulo_flujo = datos.get('modulo_flujo', True)
        configuracion.modulo_pdf = datos.get('modulo_pdf', True)
        
        # Logo (si se proporcionó)
        if 'logo' in datos and datos['logo']:
            configuracion.logo = datos['logo']
        
        # Si se solicitó eliminar el logo
        if datos.get('eliminar_logo', False):
            configuracion.logo = None
        
        # Actualizar el tenant si es necesario
        if 'clientName' in datos and tenant.name != datos['clientName']:
            tenant.name = datos['clientName']
            tenant.save()
            
        if 'clientNIT' in datos:
            tenant.nit = datos['clientNIT']
            tenant.save()
        
        configuracion.actualizado_por = usuario
        configuracion.save()
        
        return configuracion
        
    @staticmethod
    def guardar_configuracion_correo(tenant, datos, usuario):
        """Guardar la configuración de ingesta de correo."""
        configuracion = ConfiguracionService.get_configuracion(tenant)
        
        configuracion.ingesta_habilitada = datos.get('ingesta_habilitada', True)
        configuracion.correo_monitoreo = datos.get('correo_monitoreo')
        configuracion.metodo_autenticacion = datos.get('metodo_autenticacion', 'oauth')
        
        # Solo actualizar client_secret si no es el valor enmascarado
        if 'client_id' in datos:
            configuracion.client_id = datos['client_id']
        
        if 'client_secret' in datos and datos['client_secret'] != '********':
            configuracion.client_secret = datos['client_secret']
            
        configuracion.carpeta_monitoreo = datos.get('carpeta_monitoreo', 'INBOX')
        configuracion.intervalo_verificacion = datos.get('intervalo_verificacion', 5)
        configuracion.marcar_leidos = datos.get('marcar_leidos', True)
        
        configuracion.actualizado_por = usuario
        configuracion.save()
        
        return configuracion
    
    @staticmethod
    def guardar_reglas_filtro(configuracion, reglas):
        """Guardar las reglas de filtrado de correo."""
        # Eliminar reglas existentes
        configuracion.reglas_filtro.all().delete()
        
        # Crear nuevas reglas
        for regla in reglas:
            ReglaFiltracionCorreo.objects.create(
                configuracion=configuracion,
                tipo=regla['tipo'],
                valor=regla['valor']
            )
    
    @staticmethod
    def guardar_configuracion_seguridad(tenant, datos, usuario):
        """Guardar la configuración de seguridad."""
        configuracion = ConfiguracionService.get_configuracion(tenant)
        
        configuracion.req_mayusculas = datos.get('req_mayusculas', True)
        configuracion.req_numeros = datos.get('req_numeros', True)
        configuracion.req_especiales = datos.get('req_especiales', True)
        configuracion.longitud_min_password = datos.get('longitud_min_password', 8)
        configuracion.intentos_bloqueo = datos.get('intentos_bloqueo', 5)
        configuracion.desbloqueo_automatico = datos.get('desbloqueo_automatico', True)
        configuracion.metodo_2fa = datos.get('metodo_2fa', 'disabled')
        
        configuracion.actualizado_por = usuario
        configuracion.save()
        
        return configuracion
    
    @staticmethod
    def guardar_rangos_ip(configuracion, rangos):
        """Guardar los rangos de IP permitidos."""
        # Eliminar rangos existentes
        configuracion.rangos_ip.all().delete()
        
        # Crear nuevos rangos
        for rango in rangos:
            RangoIP.objects.create(
                configuracion=configuracion,
                rango=rango['rango'],
                descripcion=rango.get('descripcion', '')
            )
    
    @staticmethod
    def registrar_sincronizacion(configuracion, estatus, mensaje, correos_procesados=0, glosas_nuevas=0):
        """Registrar una operación de sincronización en el historial."""
        return HistorialSincronizacion.objects.create(
            configuracion=configuracion,
            estatus=estatus,
            mensaje=mensaje,
            correos_procesados=correos_procesados,
            glosas_nuevas=glosas_nuevas
        )
    
    @staticmethod
    def obtener_historial_sincronizacion(configuracion, limite=10):
        """Obtener el historial de sincronización reciente."""
        return configuracion.historial_sincronizacion.all().order_by('-fecha')[:limite]