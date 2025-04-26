from apps.ingesta_correo.services.regla_test_service import ReglaTestService

class ReglaTestAPIView(APIView):
    """
    Vista API para probar reglas de filtrado.
    Permite evaluar una regla con datos de prueba para verificar si se cumple.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        Prueba una regla de filtrado con datos proporcionados.
        
        Puede probar una regla existente usando su ID o una regla temporal
        definida en la solicitud.
        """
        try:
            data = request.data
            tenant = get_tenant(request)
            result = {}
            
            # Extraer parámetros
            campo = data.get('campo')
            condicion = data.get('condicion')
            valor = data.get('valor')
            valor_prueba = data.get('valor_prueba')
            regla_id = data.get('regla_id')
            
            # Validar parámetros básicos
            if not campo or not condicion:
                return Response(
                    {'error': 'Faltan parámetros requeridos (campo y/o condición)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Si es una regla existente, obtenerla
            if regla_id:
                try:
                    regla = ReglaFiltrado.objects.get(id=regla_id, tenant=tenant)
                    # Usar valores de la regla si no se especificaron
                    campo = campo or regla.campo
                    condicion = condicion or regla.condicion
                    valor = valor or regla.valor
                except ReglaFiltrado.DoesNotExist:
                    return Response(
                        {'error': 'Regla no encontrada'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Obtener el servicio de prueba
            servicio_test = ReglaTestService()
            
            # Evaluar la regla
            resultado = servicio_test.evaluar_regla(
                campo=campo,
                condicion=condicion,
                valor=valor,
                datos_prueba=valor_prueba
            )
            
            # Añadir información contextual
            resultado['campo'] = campo
            resultado['condicion'] = condicion
            resultado['valor'] = valor
            resultado['valor_prueba'] = valor_prueba
            
            # Añadir información de la regla si existe
            if regla_id:
                resultado['regla_id'] = regla_id
                resultado['regla_nombre'] = regla.nombre
            
            return Response(resultado)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error al probar regla: {error_message}")
            return Response(
                {'error': error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 