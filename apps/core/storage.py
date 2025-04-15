from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import uuid

class TenantFileSystemStorage(FileSystemStorage):
    """
    Sistema de almacenamiento personalizado para archivos de tenants.
    
    Características:
    - Organiza archivos por tenant_id
    - Genera nombres de archivo únicos para evitar colisiones
    - Mantiene la extensión original del archivo
    """
    
    def __init__(self, base_path='tenants', *args, **kwargs):
        self.base_path = base_path
        super().__init__(*args, **kwargs)
    
    def get_tenant_path(self, tenant_id):
        """Construye la ruta base para un tenant específico."""
        return os.path.join(self.base_path, f'tenant_{tenant_id}')
    
    def get_valid_name(self, name):
        """
        Devuelve un nombre de archivo válido, conservando la extensión original
        pero generando un UUID para el nombre base.
        """
        # Obtener la extensión del archivo
        ext = os.path.splitext(name)[1]
        # Generar un nombre único usando UUID
        unique_name = f'{uuid.uuid4().hex}{ext}'
        return unique_name
    
    def get_available_name(self, name, max_length=None):
        """
        Obtiene un nombre disponible para el archivo.
        Si ya existe un archivo con el mismo nombre, se genera un nuevo nombre único.
        """
        name = self.get_valid_name(name)
        return super().get_available_name(name, max_length)
    
    def _save(self, name, content):
    """
    Guarda el archivo en el sistema de archivos.
    El parámetro 'name' ya debe incluir la ruta del tenant.
    """
    # Asegúrese de que exista el directorio
    directory = os.path.dirname(os.path.join(self.location, name))
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"Directorio creado: {directory}")
        except Exception as e:
            print(f"Error al crear directorio {directory}: {e}")
    
    # Guardar el archivo
    result = super()._save(name, content)
    
    # Verificar si se guardó correctamente
    full_path = os.path.join(self.location, result)
    if os.path.exists(full_path):
        print(f"Archivo guardado correctamente en: {full_path}")
    else:
        print(f"ADVERTENCIA: El archivo no se guardó en: {full_path}")
    
    return result
    
    def url(self, name):
        """
        Sobrescribe el método url para proporcionar la URL correcta al archivo.
        """
        return super().url(name)