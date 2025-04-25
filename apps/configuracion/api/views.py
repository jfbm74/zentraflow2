# configuracion/api/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from apps.tenants.models import Tenant
from ..models import TenantConfig, EmailConfig
from ..services.config_service import ConfigService
from ..services.email_config_service import EmailConfigService
from .serializers import TenantConfigSerializer, EmailConfigSerializer

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

class EmailConfigAPIView(APIView):
    """Vista de API para configuración de correo electrónico."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, tenant_id=None):
        """Obtiene la configuración de correo de un tenant."""
        # Determinar el tenant
        if tenant_id is not None and (request.user.is_superuser or request.user.role == 'ADMIN'):
            tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)
        else:
            tenant = request.user.tenant
            
        # Obtener o crear la configuración
        config = EmailConfigService.get_email_config(tenant)
        serializer = EmailConfigSerializer(config)
        
        return Response(serializer.data)
    
    def post(self, request, tenant_id=None):
        """Actualiza la configuración de correo de un tenant."""
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
            
        # Procesar la solicitud según la acción
        action = request.data.get('action', 'save_email_config')
        
        if action == 'test_connection':
            # Probar conexión sin guardar
            result = EmailConfigService.test_connection(request.data)
            return Response(result)
        
        else:  # save_email_config por defecto
            # Actualizar la configuración
            result = EmailConfigService.update_email_config(
                tenant=tenant,
                data=request.data,
                user=request.user
            )
            
            if result['success']:
                # Obtener la configuración actualizada
                config = EmailConfigService.get_email_config(tenant)
                serializer = EmailConfigSerializer(config)
                
                response_data = {
                    'success': True,
                    'message': result['message'],
                    'config': serializer.data
                }
                
                # Incluir estado de conexión si está presente en el resultado
                if 'connection_status' in result:
                    response_data['connection_status'] = result['connection_status']
                if 'connection_message' in result:
                    response_data['connection_message'] = result['connection_message']
                
                return Response(response_data)
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)