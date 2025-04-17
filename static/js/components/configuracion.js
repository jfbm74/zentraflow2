/**
 * Configuracion.js - Maneja todas las interacciones del usuario en la página de configuración
 * Versión corregida para solucionar el error de innerHTML
 */
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    const tenantSelect = document.getElementById('tenant-select');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const errorAlert = document.getElementById('errorAlert');
    const successAlert = document.getElementById('successAlert');
    
    // Verificar elementos críticos
    if (!saveConfigBtn) {
        console.error('Error: Botón de guardar no encontrado');
        return;
    }
    
    // Obtener el CSRF token del DOM (es fundamental para el envío)
    const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenElement) {
        console.error('Error: Token CSRF no encontrado en la página');
        return;
    }
    const csrfToken = csrfTokenElement.value;
    
    // Cambiar tenant (solo para Admin)
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
    
    // Vista previa de logo al seleccionar archivo
    if (logoUpload && logoPreview) {
        logoUpload.addEventListener('change', function(event) {
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
    
    // Guardar configuración (función principal)
    saveConfigBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Mostrar estado de carga
        saveConfigBtn.disabled = true;
        saveConfigBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        
        try {
            // Crear FormData para envío de datos incluyendo archivos
            const formData = new FormData();
            
            // Añadir CSRF token
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Recopilar y añadir datos del formulario si existen los elementos
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
            
            // Realizar solicitud AJAX con Fetch API
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
                // Determinar si la operación fue exitosa
                if (data.success) {
                    // Mostrar mensaje de éxito
                    if (successAlert) {
                        const messageContainer = successAlert.querySelector('.alert-message');
                        if (messageContainer) {
                            // Solo modificar el contenido si el elemento existe
                            const strongElement = messageContainer.querySelector('strong');
                            const strongText = strongElement ? strongElement.textContent : '¡Éxito!';
                            messageContainer.innerHTML = `<strong>${strongText}</strong> ${data.message || 'Configuración guardada correctamente.'}`;
                            successAlert.classList.add('show');
                            
                            // Ocultar después de 5 segundos
                            setTimeout(() => {
                                successAlert.classList.remove('show');
                            }, 5000);
                        } else {
                            // Fallback si no se encuentra el contenedor de mensaje
                            alert('Configuración guardada correctamente.');
                        }
                    } else {
                        // Fallback si no se encuentra la alerta de éxito
                        alert('Configuración guardada correctamente.');
                    }
                    
                    // Si se subió un logo nuevo y tenemos URL y elemento para actualizar
                    if (logoUpload && logoUpload.files && logoUpload.files[0] && data.logo_url && logoPreview) {
                        // Actualizar imagen con timestamp para evitar caché
                        logoPreview.src = data.logo_url + "?t=" + new Date().getTime();
                        // Limpiar input de archivo
                        logoUpload.value = '';
                    }
                } else {
                    // Mostrar mensaje de error
                    if (errorAlert) {
                        const messageContainer = errorAlert.querySelector('.alert-message');
                        if (messageContainer) {
                            // Solo modificar el contenido si el elemento existe
                            const strongElement = messageContainer.querySelector('strong');
                            const strongText = strongElement ? strongElement.textContent : 'Error:';
                            messageContainer.innerHTML = `<strong>${strongText}</strong> ${data.message || 'Error al guardar la configuración.'}`;
                            errorAlert.classList.add('show');
                            
                            // Ocultar después de 5 segundos
                            setTimeout(() => {
                                errorAlert.classList.remove('show');
                            }, 5000);
                        } else {
                            // Fallback si no se encuentra el contenedor de mensaje
                            alert('Error: ' + (data.message || 'Error al guardar la configuración.'));
                        }
                    } else {
                        // Fallback si no se encuentra la alerta de error
                        alert('Error: ' + (data.message || 'Error al guardar la configuración.'));
                    }
                }
            })
            .catch(error => {
                console.error('Error al guardar configuración:', error);
                // Mostrar mensaje usando alert como fallback si los elementos no existen
                alert('Error al guardar configuración: ' + error.message);
            })
            .finally(() => {
                // Restaurar botón siempre
                saveConfigBtn.disabled = false;
                saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
            });
        } catch (err) {
            // Capturar cualquier error durante la preparación
            console.error('Error al preparar la solicitud:', err);
            alert('Error al preparar la solicitud: ' + err.message);
            
            // Restaurar botón
            saveConfigBtn.disabled = false;
            saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
        }
    });
    
    // Función para manejar componentes adicionales como modales, etc.
    function initializeOtherComponents() {
        // Cambiar método de autenticación para correo
        const authMethod = document.getElementById('authMethod');
        if (authMethod) {
            const oauthCredentials = document.getElementById('oauthCredentials');
            const serviceCredentials = document.getElementById('serviceCredentials');
            
            if (oauthCredentials && serviceCredentials) {
                authMethod.addEventListener('change', function() {
                    if (this.value === 'oauth') {
                        oauthCredentials.style.display = 'block';
                        serviceCredentials.style.display = 'none';
                    } else {
                        oauthCredentials.style.display = 'none';
                        serviceCredentials.style.display = 'block';
                    }
                });
            }
        }
        
        // Toggle para mostrar/ocultar contraseñas
        const togglePasswordBtns = document.querySelectorAll('.toggle-password');
        togglePasswordBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.closest('.input-group').querySelector('input');
                if (input) {
                    if (input.type === 'password') {
                        input.type = 'text';
                        this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                    } else {
                        input.type = 'password';
                        this.innerHTML = '<i class="fas fa-eye"></i>';
                    }
                }
            });
        });
        
        // Selección de idioma
        const languageOptions = document.querySelectorAll('.language-option');
        languageOptions.forEach(option => {
            option.addEventListener('click', function() {
                languageOptions.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
            });
        });
    }
    
    // Inicializar otros componentes
    initializeOtherComponents();
});

// Añadir al archivo js/components/configuracion.js

// Compatibilidad con el gestor OAuth
document.addEventListener('DOMContentLoaded', function() {
    // Asegurarse de que los cambios en la pestaña de correo se guarden
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    
    if (saveConfigBtn) {
        const originalClick = saveConfigBtn.onclick;
        
        saveConfigBtn.onclick = function(e) {
            // Si estamos en la pestaña de correo, guardar configuración OAuth primero
            const correoTabActive = document.getElementById('correo') && 
                                  document.getElementById('correo').classList.contains('active');
            
            if (correoTabActive && window.oauthManager) {
                e.preventDefault();
                
                // Mostrar estado de carga
                saveConfigBtn.disabled = true;
                saveConfigBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
                
                // Guardar configuración OAuth
                window.oauthManager.saveSettings()
                    .then(result => {
                        if (result.success) {
                            console.log('Configuración OAuth guardada con éxito');
                            
                            // Mostrar mensaje de éxito
                            const successAlert = document.getElementById('successAlert');
                            if (successAlert) {
                                const messageContainer = successAlert.querySelector('.alert-message');
                                if (messageContainer) {
                                    messageContainer.innerHTML = '<strong>¡Éxito!</strong> Configuración de correo guardada correctamente.';
                                    successAlert.classList.add('show');
                                    
                                    setTimeout(() => {
                                        successAlert.classList.remove('show');
                                    }, 5000);
                                }
                            }
                            
                            // Ejecutar la función original de guardado si existe
                            if (typeof originalClick === 'function') {
                                originalClick.call(saveConfigBtn, e);
                            } else {
                                // Restaurar botón
                                saveConfigBtn.disabled = false;
                                saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
                            }
                        } else {
                            throw new Error(result.message || 'Error al guardar configuración OAuth');
                        }
                    })
                    .catch(error => {
                        console.error('Error al guardar configuración OAuth:', error);
                        
                        // Restaurar botón
                        saveConfigBtn.disabled = false;
                        saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
                        
                        // Mostrar error
                        const errorAlert = document.getElementById('errorAlert');
                        if (errorAlert) {
                            const messageContainer = errorAlert.querySelector('.alert-message');
                            if (messageContainer) {
                                messageContainer.innerHTML = `<strong>Error:</strong> ${error.message || 'Error al guardar configuración OAuth'}`;
                                errorAlert.classList.add('show');
                                
                                setTimeout(() => {
                                    errorAlert.classList.remove('show');
                                }, 5000);
                            }
                        }
                    });
            } else if (typeof originalClick === 'function') {
                // Si no estamos en la pestaña de correo o no hay oauthManager, ejecutar la función original
                originalClick.call(saveConfigBtn, e);
            }
        };
    }
});