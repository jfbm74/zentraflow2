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
            
            # Obtener el valor del campo en los datos de prueba
            valor_campo = None
            
            if campo == 'ASUNTO':
                valor_campo = datos_prueba.get('asunto', '')
            elif campo == 'REMITENTE':
                valor_campo = datos_prueba.get('remitente', '')
            elif campo == 'DESTINATARIO':
                valor_campo = datos_prueba.get('destinatario', '')
            elif campo == 'CONTENIDO':
                valor_campo = datos_prueba.get('contenido', '')
            elif campo == 'ADJUNTO':
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
            
            # Evaluar la condición
            cumple = False
            
            if condicion == 'CONTIENE':
                cumple = valor.lower() in valor_campo.lower()
            elif condicion == 'NO_CONTIENE':
                cumple = valor.lower() not in valor_campo.lower()
            elif condicion == 'ES_IGUAL':
                cumple = valor.lower() == valor_campo.lower()
            elif condicion == 'EMPIEZA_CON':
                cumple = valor_campo.lower().startswith(valor.lower())
            elif condicion == 'TERMINA_CON':
                cumple = valor_campo.lower().endswith(valor.lower())
            elif condicion == 'COINCIDE_REGEX':
                # Intentar aplicar la expresión regular
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
            }.get(campo, campo)
            
            condicion_display = {
                'CONTIENE': 'contiene',
                'NO_CONTIENE': 'no contiene',
                'ES_IGUAL': 'es igual a',
                'EMPIEZA_CON': 'empieza con',
                'TERMINA_CON': 'termina con',
                'COINCIDE_REGEX': 'coincide con la expresión'
            }.get(condicion, condicion)
            
            mensaje = f'El {campo_display} "{valor_campo}" {condicion_display} "{valor}".'
            
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
        Evalúa un objeto Regla completo contra datos de prueba.
        
        Args:
            regla: Objeto ReglaFiltrado
            datos_prueba: Diccionario con datos de prueba
            
        Returns:
            dict: Resultado de la evaluación
        """
        try:
            if not regla.activa:
                return {
                    'cumple': False,
                    'mensaje': 'La regla está inactiva.',
                    'accion': None
                }
            
            # Evaluar la regla
            resultado = ReglaTestService.evaluar_regla(
                regla.campo,
                regla.condicion,
                regla.valor,
                datos_prueba
            )
            
            # Añadir la acción al resultado
            resultado['accion'] = regla.accion if resultado['cumple'] else None
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al evaluar regla completa: {str(e)}")
            return {
                'cumple': False,
                'mensaje': f'Error al evaluar la regla: {str(e)}',
                'accion': None
            }