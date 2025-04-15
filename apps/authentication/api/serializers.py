from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.tenants.models import Tenant  # Update this
from apps.authentication.models import ZentraflowUser  # Update this

class TenantSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Tenant."""
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain']

class UserSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ZentraflowUser."""
    tenant = TenantSerializer(read_only=True)
    
    class Meta:
        model = ZentraflowUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'tenant']
        read_only_fields = ['id', 'email', 'role', 'tenant']

class LoginSerializer(serializers.Serializer):
    """Serializador para la autenticación de usuarios."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            
            if not user:
                msg = 'Credenciales inválidas. Por favor, intente nuevamente.'
                raise serializers.ValidationError(msg, code='authorization')
            
            if user.is_locked:
                msg = 'Su cuenta ha sido bloqueada. Por favor, restablezca su contraseña.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Debe proporcionar email y contraseña.'
            raise serializers.ValidationError(msg, code='authorization')
        
        data['user'] = user
        return data

class PasswordResetSerializer(serializers.Serializer):
    """Serializador para restablecimiento de contraseña."""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = ZentraflowUser.objects.get(email=value)
        except ZentraflowUser.DoesNotExist:
            # No revelamos si el usuario existe o no por razones de seguridad
            pass
        
        return value