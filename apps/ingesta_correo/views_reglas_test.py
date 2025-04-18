# apps/ingesta_correo/views_reglas_test.py
"""
Vistas para probar las reglas de filtrado.
Permite evaluar si un correo cumple con una regla antes de guardarla.
"""

import json
import logging
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from apps.ingesta_correo.models import ReglaFiltrado
from apps.ingesta_correo.services.regla_test_service import ReglaTestService

logger = logging.getLogger(__name__)

class TestReglaView(LoginRequiredMixin, View):
    """Vista para probar si un correo cumple con una regla."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """
        Evalúa si los datos de prueba cumplen con una regla.
        
        Args:
            request: Solicitud HTTP con datos de prueba y regla
            
        Returns:
            JsonResponse con el resultado de la evaluación
        """
        try:
            # Obtener datos del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de datos inválido. Se esperaba JSON.'
                }, status=400)
            
            # Extraer datos de prueba y regla
            datos_prueba = data.get('datos_prueba', {})
            regla_data = data.get('regla', {})
            
            # Validar que hay datos suficientes
            if not datos_prueba:
                return JsonResponse({
                    'success': False,
                    'message': 'No se proporcionaron datos de prueba.'
                }, status=400)
            
            if not regla_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No se proporcionaron datos de la regla.'
                }, status=400)
            
            # Extraer los parámetros de la regla
            campo = regla_data.get('campo')
            condicion = regla_data.get('condicion')
            valor = regla_data.get('valor')
            
            if not campo or not condicion or valor is None:
                return JsonResponse({
                    'success': False,
                    'message': 'La regla debe tener campo, condición y valor.'
                }, status=400)
            
            # Evaluar la regla
            resultado = ReglaTestService.evaluar_regla(campo, condicion, valor, datos_prueba)
            
            # Construir respuesta
            return JsonResponse({
                'success': True,
                'resultado': {
                    'cumple': resultado['cumple'],
                    'mensaje': resultado['mensaje'],
                    'accion': regla_data.get('accion') if resultado['cumple'] else None
                }
            })
            
        except Exception as e:
            logger.error(f"Error al probar regla: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al probar la regla: {str(e)}'
            }, status=500)

class TestReglaExistenteView(LoginRequiredMixin, View):
    """Vista para probar una regla existente con datos de prueba."""
    
    @method_decorator(csrf_protect)
    def post(self, request, regla_id):
        """
        Evalúa si los datos de prueba cumplen con una regla existente.
        
        Args:
            request: Solicitud HTTP con datos de prueba
            regla_id: ID de la regla a probar
            
        Returns:
            JsonResponse con el resultado de la evaluación
        """
        try:
            # Obtener la regla
            try:
                regla = ReglaFiltrado.objects.get(id=regla_id)
            except ReglaFiltrado.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'La regla no existe.'
                }, status=404)
            
            # Verificar que el usuario pertenece al mismo tenant que la regla
            if request.user.tenant != regla.servicio.tenant and not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'message': 'No tiene permisos para probar esta regla.'
                }, status=403)
            
            # Obtener datos del cuerpo de la solicitud
            try:
                data = json.loads(request.body)
                datos_prueba = data.get('datos_prueba', {})
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de datos inválido. Se esperaba JSON.'
                }, status=400)
            
            # Validar que hay datos suficientes
            if not datos_prueba:
                return JsonResponse({
                    'success': False,
                    'message': 'No se proporcionaron datos de prueba.'
                }, status=400)
            
            # Evaluar la regla
            resultado = ReglaTestService.evaluar_regla_completa(regla, datos_prueba)
            
            # Construir respuesta
            return JsonResponse({
                'success': True,
                'resultado': {
                    'cumple': resultado['cumple'],
                    'mensaje': resultado['mensaje'],
                    'accion': resultado['accion']
                }
            })
            
        except Exception as e:
            logger.error(f"Error al probar regla existente: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al probar la regla: {str(e)}'
            }, status=500)