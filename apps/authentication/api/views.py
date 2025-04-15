from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from authentication.services.auth_service import AuthenticationService
from authentication.services.password_service import PasswordService
from .serializers import LoginSerializer, UserSerializer, PasswordResetSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener token JWT."""
    def post(self, request, *args, **kwargs):
        result = AuthenticationService.authenticate_user(
            request, 
            request.data.get('email'), 
            request.data.get('password')
        )
        
        if result['success']:
            user = result['user']
            tokens = AuthenticationService.get_tokens_for_user(user)
            return Response({
                'tokens': tokens,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['message'],
                'error_code': result['error_code']
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """Vista para cerrar sesión (invalidar token JWT)."""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        try:
            # En una implementación real, se agregaría el token a una lista negra
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordResetAPIView(APIView):
    """Vista para solicitar restablecimiento de contraseña."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            result = PasswordService.reset_password(serializer.validated_data['email'])
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyTokenView(APIView):
    """Vista para verificar si el token JWT es válido."""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({
            'user': serializer.data,
            'is_authenticated': True
        })