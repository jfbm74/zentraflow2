"""
Utilidades para la gestión de tenants (inquilinos) en el sistema
"""
from django.contrib.auth import get_user_model

def get_tenant_for_user(user):
    """
    Obtiene el tenant (inquilino) al que pertenece un usuario.
    
    Args:
        user: Objeto usuario autenticado
        
    Returns:
        Objeto Tenant asociado al usuario o None
    """
    if not user or not user.is_authenticated:
        return None
    
    # Obtener el tenant directamente del usuario
    return user.tenant 