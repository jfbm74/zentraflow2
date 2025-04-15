from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase, Client

from tenants.models import Tenant

# Obtener el modelo de usuario personalizado
ZentraflowUser = get_user_model()

class AuthenticationAPITests(APITestCase):
    """Pruebas para los endpoints de autenticación API."""

    def setUp(self):
        """Configuración inicial para las pruebas API."""
        self.tenant = Tenant.objects.create(name="Test Tenant API", domain="test-api.com")
        self.password = "StrongP@sswOrd123"
        self.user = ZentraflowUser.objects.create_user(
            email="testuser.api@test-api.com",
            tenant=self.tenant,
            password=self.password,
            first_name="Test",
            last_name="UserAPI"
        )
        self.login_url = reverse('token_obtain_pair')
        self.verify_url = reverse('token_verify')
        self.refresh_url = reverse('token_refresh')
        self.logout_url = reverse('api_logout') # Aunque el logout API actual no hace mucho

    def test_api_login_success(self):
        """Verifica el login exitoso vía API."""
        data = {
            "email": self.user.email,
            "password": self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user.email)

    def test_api_login_invalid_credentials(self):
        """Verifica el login fallido con credenciales incorrectas."""
        data = {
            "email": self.user.email,
            "password": "WrongPassword"
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error_code'], 'invalid_credentials')
        # Verificar que el contador de intentos fallidos aumenta
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_api_login_locked_account(self):
        """Verifica el login fallido con cuenta bloqueada."""
        # Simular 5 intentos fallidos para bloquear la cuenta
        for _ in range(5):
            self.client.post(self.login_url, {"email": self.user.email, "password": "WrongPassword"}, format='json')

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)

        # Intentar iniciar sesión con la cuenta bloqueada
        data = {
            "email": self.user.email,
            "password": self.password # Contraseña correcta, pero la cuenta está bloqueada
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error_code'], 'account_locked')

    def test_api_verify_token_valid(self):
        """Verifica que un token de acceso válido es aceptado."""
        login_data = {"email": self.user.email, "password": self.password}
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']

        # Usar el token para autenticar la solicitud de verificación
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        verify_response = self.client.get(self.verify_url) # Se usa GET en tu view

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['is_authenticated'])
        self.assertEqual(verify_response.data['user']['email'], self.user.email)

    def test_api_verify_token_invalid(self):
        """Verifica que un token inválido es rechazado."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        verify_response = self.client.get(self.verify_url) # Se usa GET en tu view
        # Esperamos un 401 Unauthorized porque JWTAuthentication lo rechazará
        self.assertEqual(verify_response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationWebTests(TestCase):
    """Pruebas para las vistas de autenticación web."""

    def setUp(self):
        """Configuración inicial para las pruebas web."""
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Test Tenant Web", domain="test-web.com")
        self.password = "StrongP@sswOrd456"
        self.user = ZentraflowUser.objects.create_user(
            email="testuser.web@test-web.com",
            tenant=self.tenant,
            password=self.password,
            first_name="Test",
            last_name="UserWeb"
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard')

    def test_web_login_page_loads(self):
        """Verifica que la página de login carga correctamente."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_web_login_success(self):
        """Verifica el login exitoso vía web y la redirección."""
        data = {
            "username": self.user.email, # El form usa 'username' para el email
            "password": self.password
        }
        response = self.client.post(self.login_url, data)

        # Verificar redirección al dashboard
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.dashboard_url)

        # Verificar que el usuario está autenticado en la sesión
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.id))

    def test_web_login_invalid_credentials(self):
        """Verifica el login web fallido con credenciales incorrectas."""
        data = {
            "username": self.user.email,
            "password": "WrongPassword"
        }
        response = self.client.post(self.login_url, data)

        # Debe permanecer en la página de login (status 200) y mostrar error
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'authentication/login.html')
        self.assertContains(response, "Credenciales inválidas") # Verifica el mensaje de error

        # Verificar que el usuario NO está autenticado
        self.assertFalse('_auth_user_id' in self.client.session)

        # Verificar que el contador de intentos fallidos aumenta
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_web_login_locked_account(self):
        """Verifica el login web fallido con cuenta bloqueada."""
        # Bloquear la cuenta
        self.user.is_locked = True
        self.user.save()

        data = {
            "username": self.user.email,
            "password": self.password # Contraseña correcta
        }
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'authentication/login.html')
        self.assertContains(response, "cuenta ha sido bloqueada") # Verifica el mensaje de error de bloqueo

        # Verificar que el usuario NO está autenticado
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_web_logout(self):
        """Verifica el logout web."""
        # Primero, iniciar sesión
        self.client.login(email=self.user.email, password=self.password)
        self.assertTrue('_auth_user_id' in self.client.session)

        # Luego, cerrar sesión
        response = self.client.get(self.logout_url)

        # Verificar redirección a la página de login
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.login_url)

        # Verificar que el usuario ya no está en la sesión
        self.assertFalse('_auth_user_id' in self.client.session)