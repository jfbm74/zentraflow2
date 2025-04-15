from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.views.generic import View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from .forms import LoginForm, PasswordResetForm
from apps.authentication.services.auth_service import AuthenticationService  # Update this
from apps.authentication.services.password_service import PasswordService  # Update this

class LoginView(View):
    """Vista para el formulario de login."""
    template_name = 'authentication/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard')
    
    def get(self, request):
        """Renderizar el formulario de login."""
        if request.user.is_authenticated:
            return redirect(self.success_url)
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """Procesar el formulario de login."""
        email = request.POST.get('username')  # En el form es 'username' por compatibilidad con AuthenticationForm
        password = request.POST.get('password')
        
        result = AuthenticationService.authenticate_user(request, email, password)
        
        if result['success']:
            # Autenticación exitosa
            login(request, result['user'])
            next_url = request.GET.get('next', self.success_url)
            return redirect(next_url)
        else:
            # Autenticación fallida
            form = self.form_class()
            return render(request, self.template_name, {
                'form': form,
                'error': result['message']
            })

class LogoutView(View):
    """Vista para cerrar sesión."""
    def get(self, request):
        logout(request)
        return redirect('login')

class PasswordResetView(View):
    """Vista para solicitar restablecimiento de contraseña."""
    template_name = 'authentication/password_reset.html'
    form_class = PasswordResetForm
    
    def get(self, request):
        """Renderizar el formulario de restablecimiento de contraseña."""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    @method_decorator(csrf_protect)
    def post(self, request):
        """Procesar el formulario de restablecimiento de contraseña."""
        form = self.form_class(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            result = PasswordService.reset_password(email)
            
            # Para el MVP, mostrar la nueva contraseña en pantalla
            # En producción, esto enviaría un correo electrónico
            if 'password' in result:
                return render(request, 'authentication/password_reset_done.html', {
                    'new_password': result['password']
                })
            else:
                return render(request, 'authentication/password_reset_done.html', {
                    'message': result['message']
                })
            
        return render(request, self.template_name, {'form': form})