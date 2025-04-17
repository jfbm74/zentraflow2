/**
 * configuracion.js - Versión simplificada para solucionar problema de botones
 * Esta versión se enfoca solamente en los event listeners necesarios
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Script de configuración iniciado");
    
    // Obtener referencias a elementos del DOM
    const saveClientInfoBtn = document.getElementById('saveClientInfoBtn');
    const savePreferencesBtn = document.getElementById('savePreferencesBtn');
    const saveOAuthConfigBtn = document.getElementById('saveOAuthConfigBtn');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const errorAlert = document.getElementById('errorAlert');
    const successAlert = document.getElementById('successAlert');
    
    // Logs para verificar los elementos encontrados
    console.log("Elementos encontrados:");
    console.log("saveClientInfoBtn:", !!saveClientInfoBtn);
    console.log("savePreferencesBtn:", !!savePreferencesBtn);
    console.log("saveOAuthConfigBtn:", !!saveOAuthConfigBtn);
    console.log("removeLogoBtn:", !!removeLogoBtn);
    
    // Obtener CSRF token
    const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenElement) {
        console.error("Error: CSRF token no encontrado");
        return;
    }
    const csrfToken = csrfTokenElement.value;
    
    // Function para mostrar mensajes
    function showMessage(type, message) {
        const alert = type === 'success' ? successAlert : errorAlert;
        if (!alert) {
            alert(message);
            return;
        }
        
        const messageContainer = alert.querySelector('.alert-message');
        if (!messageContainer) {
            alert(message);
            return;
        }
        
        const strongElement = messageContainer.querySelector('strong');
        const strongText = strongElement ? strongElement.textContent : (type === 'success' ? '¡Éxito!' : 'Error:');
        messageContainer.innerHTML = `<strong>${strongText}</strong> ${message}`;
        alert.classList.add('show');
        
        setTimeout(() => {
            alert.classList.remove('show');
        }, 5000);
    }
    
    // Función principal para guardar configuración
    function saveConfig(button, extraData = {}) {
        console.log("Guardando configuración...", button.id);
        
        // Mostrar estado de carga
        button.disabled = true;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        
        try {
            // Crear FormData
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Añadir datos según la sección
            if (button.id === 'saveClientInfoBtn') {
                const clientName = document.getElementById('clientName');
                const clientNIT = document.getElementById('clientNIT');
                const timezone = document.getElementById('timezone');
                const dateFormat = document.getElementById('dateFormat');
                
                if (clientName) formData.append('name', clientName.value);
                if (clientNIT) formData.append('nit', clientNIT.value);
                if (timezone) formData.append('timezone', timezone.value);
                if (dateFormat) formData.append('date_format', dateFormat.value);
                
                // Añadir logo si hay archivo seleccionado
                if (logoUpload && logoUpload.files && logoUpload.files[0]) {
                    formData.append('logo', logoUpload.files[0]);
                }
            }
            
            // Añadir datos extra si se proporcionan
            for (const [key, value] of Object.entries(extraData)) {
                formData.append(key, value);
            }
            
            // Realizar petición
            fetch(window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en el servidor: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log("Respuesta recibida:", data);
                
                if (data.success) {
                    showMessage('success', data.message || 'Configuración guardada correctamente');
                    
                    // Si se subió un logo nuevo
                    if (button.id === 'saveClientInfoBtn' && logoUpload && logoUpload.files && logoUpload.files[0] && data.logo_url && logoPreview) {
                        logoPreview.src = data.logo_url + "?t=" + new Date().getTime();
                        logoUpload.value = '';
                    }
                } else {
                    showMessage('error', data.message || 'Error al guardar la configuración');
                }
            })
            .catch(error => {
                console.error("Error al guardar configuración:", error);
                showMessage('error', 'Error al guardar configuración: ' + error.message);
            })
            .finally(() => {
                // Restaurar botón
                button.disabled = false;
                button.innerHTML = originalHTML;
            });
        } catch (error) {
            console.error("Error al preparar la solicitud:", error);
            showMessage('error', 'Error al preparar la solicitud: ' + error.message);
            
            // Restaurar botón
            button.disabled = false;
            button.innerHTML = originalHTML;
        }
    }
    
    // Vista previa de logo al seleccionar archivo
    if (logoUpload && logoPreview) {
        logoUpload.addEventListener('change', function(event) {
            console.log("Archivo de logo seleccionado");
            const file = event.target.files[0];
            if (file) {
                // Verificar tamaño máximo (500KB)
                if (file.size > 500 * 1024) {
                    alert('El logo es demasiado grande. Máximo 500KB permitidos.');
                    logoUpload.value = ''; // Limpiar selección
                    return;
                }
                
                // Mostrar vista previa
                const reader = new FileReader();
                reader.onload = function(e) {
                    logoPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Eliminar logo
    if (removeLogoBtn && logoPreview) {
        removeLogoBtn.addEventListener('click', function(e) {
            console.log("Botón eliminar logo clickeado");
            e.preventDefault();
            
            if (confirm('¿Está seguro de que desea eliminar el logo?')) {
                // Configurar datos para eliminar logo
                const formData = new FormData();
                formData.append('action', 'remove_logo');
                formData.append('csrfmiddlewaretoken', csrfToken);
                
                // Mostrar estado de carga
                removeLogoBtn.disabled = true;
                removeLogoBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';
                
                // Realizar solicitud
                fetch(window.location.pathname, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Error en el servidor: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Actualizar vista previa
                        logoPreview.src = '/static/images/placeholder-logo.png';
                        alert('Logo eliminado correctamente.');
                    } else {
                        alert(data.message || 'No se pudo eliminar el logo.');
                    }
                })
                .catch(error => {
                    console.error('Error al eliminar logo:', error);
                    alert('Error de conexión al eliminar el logo.');
                })
                .finally(() => {
                    // Restaurar botón
                    removeLogoBtn.disabled = false;
                    removeLogoBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Eliminar';
                });
            }
        });
    }
    
    // Asignar event listeners a los botones principales
    
    // 1. Botón de Guardar Información del Cliente
    if (saveClientInfoBtn) {
        console.log("Asignando evento al botón saveClientInfoBtn");
        saveClientInfoBtn.addEventListener('click', function(e) {
            console.log("Botón saveClientInfoBtn clickeado");
            e.preventDefault();
            saveConfig(this);
        });
    } else {
        // Intento alternativo si no se encuentra por ID
        console.log("Buscando alternativa para saveClientInfoBtn");
        const btnSaveClientInfo = document.querySelector('.config-card-header button');
        if (btnSaveClientInfo && btnSaveClientInfo.textContent.includes('Guardar Información')) {
            console.log("Botón alternativo para guardar información encontrado");
            btnSaveClientInfo.addEventListener('click', function(e) {
                console.log("Botón alternativo para saveClientInfoBtn clickeado");
                e.preventDefault();
                saveConfig(this);
            });
        }
    }
    
    // 2. Botón de Guardar Preferencias
    if (savePreferencesBtn) {
        console.log("Asignando evento al botón savePreferencesBtn");
        savePreferencesBtn.addEventListener('click', function(e) {
            console.log("Botón savePreferencesBtn clickeado");
            e.preventDefault();
            saveConfig(this);
        });
    }
    
    // 3. Botón de Guardar Configuración OAuth
    if (saveOAuthConfigBtn) {
        console.log("Asignando evento al botón saveOAuthConfigBtn");
        saveOAuthConfigBtn.addEventListener('click', function(e) {
            console.log("Botón saveOAuthConfigBtn clickeado");
            e.preventDefault();
            saveConfig(this);
        });
    }
    
    // 4. Asignar eventos a botones que contengan "Guardar" en su texto
    document.querySelectorAll('button').forEach(button => {
        if ((button.textContent.includes('Guardar') || 
             button.innerHTML.includes('fa-save')) && 
            !button.hasAttribute('data-event-assigned')) {
            
            console.log(`Asignando evento a botón genérico: ${button.textContent.trim()}`);
            button.setAttribute('data-event-assigned', 'true');
            button.addEventListener('click', function(e) {
                console.log(`Botón genérico clickeado: ${this.textContent.trim()}`);
                e.preventDefault();
                saveConfig(this);
            });
        }
    });
    
    console.log("Inicialización de configuración completada");
});