# configuracion/api/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from apps.tenants.models import Tenant
from ..models import TenantConfig
from ..services.config_service import ConfigService
from .serializers import TenantConfigSerializer

class TenantConfigAPIView(APIView):
    """Vista de API para configuración de tenant."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request, tenant_id=None):
        """Obtiene la configuración de un tenant."""
        # Determinar el tenant
        if tenant_id is not None and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
            
        # Obtener o crear la configuración
        config = ConfigService.get_tenant_config(tenant)
        serializer = TenantConfigSerializer(config)
        
        return Response(serializer.data)
    
    def put(self, request, tenant_id=None):
        """Actualiza la configuración de un tenant."""
        # Verificar permisos
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            return Response({
                'error': 'No tiene permisos para editar la configuración.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Determinar el tenant
        if tenant_id is not None and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
            
        # Procesar la solicitud
        result = ConfigService.update_tenant_config(
            tenant=tenant,
            user=request.user,
            data=request.data,
            files=request.FILES
        )
        
        if result['success']:
            # Obtener la configuración actualizada
            config = ConfigService.get_tenant_config(tenant)
            serializer = TenantConfigSerializer(config)
            return Response(serializer.data)
        else:
            return Response({
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, tenant_id=None):
        """Elimina el logo de un tenant."""
        # Verificar permisos
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            return Response({
                'error': 'No tiene permisos para editar la configuración.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Determinar el tenant
        if tenant_id is not None and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
            
        # Obtener la configuración
        config = ConfigService.get_tenant_config(tenant)
        
        # Eliminar el logo
        result = ConfigService.remove_tenant_logo(config)
        
        if result['success']:
            return Response({
                'message': result['message']
            })
        else:
            return Response({
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)