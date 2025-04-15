import secrets
import string
from authentication.models import ZentraflowUser

class PasswordService:
    """Servicio para manejar operaciones relacionadas con contraseñas."""
    
    @staticmethod
    def reset_password(email):
        """
        Restablece la contraseña para el usuario con el email proporcionado.
        Para el MVP, genera una contraseña aleatoria y la devuelve.
        """
        try:
            user = ZentraflowUser.objects.get(email=email)
            
            # Generar contraseña aleatoria (para MVP)
            new_password = PasswordService.generate_secure_password()
            
            # Actualizar contraseña del usuario
            user.set_password(new_password)
            user.is_locked = False
            user.failed_login_attempts = 0
            user.save()
            
            # En MVP mostramos la contraseña en pantalla
            # En producción, enviaríamos un correo electrónico
            return {
                'success': True,
                'password': new_password
            }
            
        except ZentraflowUser.DoesNotExist:
            # Por seguridad, no revelamos si el usuario existe o no
            return {
                'success': True,
                'message': 'Si su correo electrónico está registrado en nuestro sistema, recibirá instrucciones para restablecer su contraseña.'
            }
    
    @staticmethod
    def generate_secure_password(length=12):
        """Genera una contraseña segura aleatoria."""
        # Definir los conjuntos de caracteres
        uppercase_letters = string.ascii_uppercase
        lowercase_letters = string.ascii_lowercase
        digits = string.digits
        special_chars = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        
        # Asegurarse de que la contraseña contiene al menos uno de cada tipo
        password = [
            secrets.choice(uppercase_letters),
            secrets.choice(lowercase_letters),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # Completar el resto de la contraseña
        all_chars = uppercase_letters + lowercase_letters + digits + special_chars
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Mezclar los caracteres
        secrets.SystemRandom().shuffle(password)
        
        # Convertir la lista a string
        return ''.join(password)