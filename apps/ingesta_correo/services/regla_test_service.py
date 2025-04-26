# apps/ingesta_correo/services/regla_test_service.py
"""
Servicio para probar reglas de filtrado con ejemplos.
Permite evaluar si un correo cumple con una regla antes de guardarla.
"""

import re
import logging

logger = logging.getLogger(__name__)

class ReglaTestService:
    """Servicio para probar reglas de filtrado de correos."""
    
    @staticmethod
    def evaluar_regla(campo, condicion, valor, datos_prueba):
        """
        Evalúa si los datos de prueba cumplen con la regla especificada.
        
        Args:
            campo: Campo a evaluar (ASUNTO, REMITENTE, etc.)
            condicion: Condición a aplicar (CONTIENE, NO_CONTIENE, etc.)
            valor: Valor para la condición
            datos_prueba: Diccionario con datos de prueba
            
        Returns:
            dict: Resultado de la evaluación con 'cumple' y 'mensaje'
        """
        try:
            # Validar parámetros
            if not campo or not condicion or valor is None:
                return {
                    'cumple': False,
                    'mensaje': 'Parámetros incompletos para evaluar la regla.'
                }
            
            # Convertir campo a mayúsculas para evitar problemas con capitalización
            campo_upper = campo.upper()
            
            # Obtener el valor del campo en los datos de prueba
            valor_campo = None
            
            if campo_upper == 'ASUNTO':
                valor_campo = datos_prueba.get('asunto', '')
            elif campo_upper == 'REMITENTE':
                valor_campo = datos_prueba.get('remitente', '')
            elif campo_upper == 'DESTINATARIO':
                valor_campo = datos_prueba.get('destinatario', '')
            elif campo_upper == 'CONTENIDO':
                valor_campo = datos_prueba.get('contenido', '')
            elif campo_upper == 'ADJUNTO':
                valor_campo = datos_prueba.get('adjunto', '')
            else:
                return {
                    'cumple': False,
                    'mensaje': f'Campo "{campo}" no reconocido.'
                }
            
            # Si el valor del campo no existe en los datos de prueba
            if valor_campo is None:
                return {
                    'cumple': False,
                    'mensaje': f'No se proporcionó valor para el campo "{campo}".'
                }
            
            # Convertir a string para la comparación
            if not isinstance(valor_campo, str):
                valor_campo = str(valor_campo)
            
            # Convertir condición a mayúsculas para evitar problemas con capitalización
            condicion_upper = condicion.upper()
            
            # Convertir a minúsculas para comparaciones insensibles a mayúsculas/minúsculas
            valor_campo_lower = valor_campo.lower()
            valor_lower = valor.lower()
            
            # Evaluar la condición
            cumple = False
            
            if condicion_upper == 'CONTIENE':
                # Buscar la cadena ignorando mayúsculas/minúsculas
                cumple = valor_lower in valor_campo_lower
            elif condicion_upper == 'NO_CONTIENE':
                # Verificar que la cadena no está presente, ignorando mayúsculas/minúsculas
                cumple = valor_lower not in valor_campo_lower
            elif condicion_upper == 'ES_IGUAL':
                # Comparación ignorando mayúsculas/minúsculas
                cumple = valor_lower == valor_campo_lower
            elif condicion_upper == 'EMPIEZA_CON':
                # Verificar inicio ignorando mayúsculas/minúsculas
                cumple = valor_campo_lower.startswith(valor_lower)
            elif condicion_upper == 'TERMINA_CON':
                # Verificar final ignorando mayúsculas/minúsculas
                cumple = valor_campo_lower.endswith(valor_lower)
            elif condicion_upper == 'COINCIDE_REGEX':
                # Aplicar expresión regular con bandera de ignorar mayúsculas/minúsculas
                try:
                    regex = re.compile(valor, re.IGNORECASE)
                    cumple = bool(regex.search(valor_campo))
                except re.error as e:
                    return {
                        'cumple': False,
                        'mensaje': f'Error en la expresión regular: {str(e)}'
                    }
            else:
                return {
                    'cumple': False,
                    'mensaje': f'Condición "{condicion}" no reconocida.'
                }
            
            # Construir mensaje descriptivo
            campo_display = {
                'ASUNTO': 'asunto',
                'REMITENTE': 'remitente',
                'DESTINATARIO': 'destinatario',
                'CONTENIDO': 'contenido',
                'ADJUNTO': 'nombre de adjunto'
            }.get(campo_upper, campo)
            
            condicion_display = {
                'CONTIENE': 'contiene',
                'NO_CONTIENE': 'no contiene',
                'ES_IGUAL': 'es igual a',
                'EMPIEZA_CON': 'empieza con',
                'TERMINA_CON': 'termina con',
                'COINCIDE_REGEX': 'coincide con la expresión'
            }.get(condicion_upper, condicion)
            
            mensaje = f'El {campo_display} "{valor_campo}" {condicion_display} "{valor}" (comparación insensible a mayúsculas/minúsculas).'
            
            return {
                'cumple': cumple,
                'mensaje': mensaje
            }
            
        except Exception as e:
            logger.error(f"Error al evaluar regla: {str(e)}")
            return {
                'cumple': False,
                'mensaje': f'Error al evaluar la regla: {str(e)}'
            }
    
    @staticmethod
    def evaluar_regla_completa(regla, datos_prueba):
        """
        Evalúa una regla completa contra datos de prueba.
        
        Args:
            regla: Objeto ReglaFiltrado a evaluar
            datos_prueba: Diccionario con datos de prueba
            
        Returns:
            dict: Resultado de la evaluación
        """
        return ReglaTestService.evaluar_regla(
            regla.campo,
            regla.condicion,
            regla.valor,
            datos_prueba
        )