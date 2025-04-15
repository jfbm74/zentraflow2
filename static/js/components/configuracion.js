// configuracion.js - Funcionalidad para la página de configuración del cliente

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');
    const tenantSelect = document.getElementById('tenant-select');
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    
    // Configurar selector de tenant (para Super Admin)
    if (tenantSelect) {
        tenantSelect.addEventListener('change', function() {
            const tenantId = this.value;
            if (tenantId) {
                window.location.href = `/configuracion/${tenantId}/`;
            } else {
                window.location.href = '/configuracion/';
            }
        });
    }
    
    // Previsualización de logo al seleccionar archivo
    if (logoUpload) {
        logoUpload.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    logoPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Eliminar logo
    if (removeLogoBtn) {
        removeLogoBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('¿Está seguro de eliminar el logo?')) {
                // Obtener el CSRF token del meta tag
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // Crear los datos para enviar
                const formData = new FormData();
                formData.append('action', 'remove_logo');
                
                // Realizar la solicitud AJAX
                fetch(window.location.pathname, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Restablecer la vista previa a la imagen predeterminada
                        logoPreview.src = '/static/images/placeholder-logo.png';
                        
                        // Mostrar alerta de éxito
                        showAlert('success', data.message);
                    } else {
                        // Mostrar mensaje de error
                        showAlert('error', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('error', 'Error al procesar la solicitud');
                });
            }
        });
    }
    
    // Guardar configuración
    const saveConfig = function(e) {
        e.preventDefault();
        
        // Obtener el CSRF token del meta tag
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Obtener valores del formulario
        const clientName = document.getElementById('clientName').value;
        const clientNIT = document.getElementById('clientNIT').value;
        const timezone = document.getElementById('timezone').value;
        const dateFormat = document.getElementById('dateFormat').value;
        const logoFile = logoUpload.files[0]; // Puede ser undefined si no se seleccionó archivo
        
        // Crear los datos para enviar
        const formData = new FormData();
        formData.append('name', clientName);
        formData.append('nit', clientNIT);
        formData.append('timezone', timezone);
        formData.append('date_format', dateFormat);
        
        // Añadir logo solo si se seleccionó un archivo
        if (logoFile) {
            formData.append('logo', logoFile);
        }
        
        // Realizar la solicitud AJAX
        fetch(window.location.pathname, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mostrar alerta de éxito
                showAlert('success', data.message);
            } else {
                // Mostrar mensaje de error
                showAlert('error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('error', 'Error al procesar la solicitud');
        });
    };
    
    // Asignar evento al botón de guardar
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveConfig);
    }
    
    // Función para mostrar alertas
    function showAlert(type, message) {
        // Ocultar ambas alertas primero
        successAlert.classList.remove('show');
        errorAlert.classList.remove('show');
        
        // Seleccionar la alerta correcta
        const alertElement = type === 'success' ? successAlert : errorAlert;
        
        // Actualizar mensaje
        const messageElement = alertElement.querySelector('.alert-message');
        if (messageElement) {
            if (type === 'success') {
                messageElement.innerHTML = `<strong>¡Éxito!</strong> ${message}`;
            } else {
                messageElement.innerHTML = `<strong>Error:</strong> ${message}`;
            }
        }
        
        // Mostrar alerta
        alertElement.classList.add('show');
        
        // Ocultar después de 5 segundos
        setTimeout(() => {
            alertElement.classList.remove('show');
        }, 5000);
    }
    
    // Inicializar selectores de pestañas Bootstrap
    const triggerTabList = [].slice.call(document.querySelectorAll('#configTabs button'));
    triggerTabList.forEach(function (triggerEl) {
        const tabTrigger = new bootstrap.Tab(triggerEl);
        
        triggerEl.addEventListener('click', function (event) {
            event.preventDefault();
            tabTrigger.show();
        });
    });
});