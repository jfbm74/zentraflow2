// Ruta: static/js/components/configuracion.js
document.addEventListener('DOMContentLoaded', function() {
    // Referencia al token CSRF
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Referencia a elementos del DOM
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    const errorAlert = document.getElementById('errorAlert');
    const successAlert = document.getElementById('successAlert');
    const tenantSelect = document.getElementById('tenant-select');
    
    // Inicializar tenantId
    let tenantId = '';
    if (tenantSelect) {
        tenantId = tenantSelect.value;
    }
    
    // Cambio de tenant (solo para superadmin)
    if (tenantSelect) {
        tenantSelect.addEventListener('change', function() {
            if (this.value) {
                window.location.href = `/configuracion/${this.value}/`;
            } else {
                window.location.href = '/configuracion/';
            }
        });
    }
    
    // Previsualización de logo al seleccionar archivo
    if (logoUpload) {
        logoUpload.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                
                // Verificar tamaño del archivo (max 500KB)
                if (file.size > 500 * 1024) {
                    showAlert(errorAlert, 'El archivo es demasiado grande. El tamaño máximo permitido es 500KB.');
                    this.value = '';
                    return;
                }
                
                // Mostrar previsualización
                const reader = new FileReader();
                reader.onload = function(e) {
                    logoPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
                
                console.log('Archivo seleccionado:', file.name, 'Tamaño:', file.size, 'bytes');
            }
        });
    }
    
    // Eliminar logo
    if (removeLogoBtn) {
        removeLogoBtn.addEventListener('click', function() {
            const url = tenantId ? `/configuracion/${tenantId}/` : '/configuracion/';
            
            // Crear FormData para el envío
            const formData = new FormData();
            formData.append('action', 'remove_logo');
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Realizar petición AJAX
            fetch(url, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Resetear la previsualización a la imagen por defecto
                    logoPreview.src = '/static/images/placeholder-logo.png';
                    showAlert(successAlert, data.message);
                } else {
                    showAlert(errorAlert, data.message);
                }
            })
            .catch(error => {
                console.error('Error al eliminar logo:', error);
                showAlert(errorAlert, 'Error al eliminar logo: ' + error.message);
            });
        });
    }
    
    // Función para actualizar la vista con el nuevo logo
    function updateLogoPreview(logoUrl) {
        const logoPreview = document.getElementById('logoPreview');
        if (logoPreview) {
            // Añadir timestamp para evitar caché
            logoPreview.src = logoUrl + "?t=" + new Date().getTime();
        }
    }
    
    // Guardar configuración
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', function() {
            const url = tenantId ? `/configuracion/${tenantId}/` : '/configuracion/';
            
            // Recopilar datos del formulario
            const formData = new FormData();
            
            // Añadir token CSRF
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Datos básicos
            formData.append('name', document.getElementById('clientName').value);
            formData.append('nit', document.getElementById('clientNIT').value);
            formData.append('timezone', document.getElementById('timezone').value);
            formData.append('date_format', document.getElementById('dateFormat').value);
            
            // Archivo de logo (si se ha seleccionado uno nuevo)
            if (logoUpload.files && logoUpload.files[0]) {
                formData.append('logo', logoUpload.files[0]);
                console.log('Enviando logo:', logoUpload.files[0].name);
            }
            
            // Mostrar loading state
            saveConfigBtn.disabled = true;
            saveConfigBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
            
            // Realizar petición AJAX
            fetch(url, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(successAlert, data.message);
                    // Si hay una URL de logo en la respuesta, actualizar la vista
                    if (data.logo_url) {
                        updateLogoPreview(data.logo_url);
                    }
                } else {
                    showAlert(errorAlert, data.message || 'Error al guardar la configuración');
                }
            })
            .catch(error => {
                console.error('Error al guardar configuración:', error);
                showAlert(errorAlert, 'Error al guardar configuración: ' + error.message);
            })
            .finally(() => {
                // Restaurar botón
                saveConfigBtn.disabled = false;
                saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
            });
        });
    }
    
    // Función para mostrar alertas
    function showAlert(alertElement, message) {
        if (alertElement) {
            // Actualizar mensaje
            const messageContainer = alertElement.querySelector('.alert-message');
            if (messageContainer) {
                // Mantener el título strong y añadir el mensaje
                const strongTag = messageContainer.querySelector('strong');
                if (strongTag) {
                    messageContainer.innerHTML = '';
                    messageContainer.appendChild(strongTag);
                    messageContainer.innerHTML += ' ' + message;
                } else {
                    messageContainer.textContent = message;
                }
            }
            
            // Mostrar alerta
            alertElement.classList.add('show');
            
            // Ocultar después de 5 segundos
            setTimeout(() => {
                alertElement.classList.remove('show');
            }, 5000);
        }
    }
    
    // Cambio entre métodos de autenticación para correo
    const authMethod = document.getElementById('authMethod');
    const oauthCredentials = document.getElementById('oauthCredentials');
    const serviceCredentials = document.getElementById('serviceCredentials');
    
    if (authMethod && oauthCredentials && serviceCredentials) {
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
    
    // Toggle para mostrar/ocultar contraseñas
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                input.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
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
    
    // Modales y botones adicionales
    setupModalHandlers();
    
    function setupModalHandlers() {
        // Modal de reglas de filtro
        const addFilterBtn = document.querySelector('.add-filter-btn');
        if (addFilterBtn && document.getElementById('filterRuleModal')) {
            const filterRuleModal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
            const saveFilterBtn = document.getElementById('saveFilterBtn');
            
            addFilterBtn.addEventListener('click', function() {
                // Limpiar campos del modal
                document.getElementById('filterType').value = 'from';
                document.getElementById('filterValue').value = '';
                filterRuleModal.show();
            });
            
            if (saveFilterBtn) {
                saveFilterBtn.addEventListener('click', function() {
                    const type = document.getElementById('filterType').value;
                    const value = document.getElementById('filterValue').value;
                    
                    // Crear nuevo elemento de regla de filtro
                    const filterRule = document.createElement('div');
                    filterRule.className = 'filter-rule';
                    filterRule.innerHTML = `
                        <div class="filter-type">${getFilterTypeLabel(type)}:</div>
                        <div class="filter-value">${value}</div>
                        <div class="filter-actions">
                            <button class="filter-edit"><i class="fas fa-edit"></i></button>
                            <button class="filter-delete"><i class="fas fa-times"></i></button>
                        </div>
                    `;
                    
                    // Añadir a la lista
                    const emailFilterRules = document.querySelector('.email-filter-rules');
                    if (emailFilterRules) {
                        emailFilterRules.insertBefore(filterRule, addFilterBtn);
                        
                        // Añadir listeners a los botones
                        const deleteBtn = filterRule.querySelector('.filter-delete');
                        if (deleteBtn) {
                            deleteBtn.addEventListener('click', function() {
                                filterRule.remove();
                            });
                        }
                    }
                    
                    filterRuleModal.hide();
                });
            }
        }
        
        function getFilterTypeLabel(type) {
            const labels = {
                'from': 'De',
                'subject': 'Asunto',
                'body': 'Contenido',
                'has-attachment': 'Tiene Adjunto'
            };
            return labels[type] || type;
        }
        
        // Modal para rango IP
        const addIpBtn = document.querySelector('.add-ip-btn');
        if (addIpBtn && document.getElementById('ipRangeModal')) {
            const ipRangeModal = new bootstrap.Modal(document.getElementById('ipRangeModal'));
            const saveIpBtn = document.getElementById('saveIpBtn');
            
            addIpBtn.addEventListener('click', function() {
                // Limpiar campos del modal
                document.getElementById('ipRange').value = '';
                document.getElementById('ipDescription').value = '';
                ipRangeModal.show();
            });
            
            if (saveIpBtn) {
                saveIpBtn.addEventListener('click', function() {
                    const range = document.getElementById('ipRange').value;
                    
                    // Crear nuevo elemento de rango IP
                    const ipRange = document.createElement('div');
                    ipRange.className = 'ip-range';
                    ipRange.innerHTML = `
                        <div class="ip-value">${range}</div>
                        <div class="ip-actions">
                            <button class="ip-edit"><i class="fas fa-edit"></i></button>
                            <button class="ip-delete"><i class="fas fa-times"></i></button>
                        </div>
                    `;
                    
                    // Añadir a la lista
                    const ipRestrictions = document.querySelector('.ip-restrictions');
                    if (ipRestrictions) {
                        ipRestrictions.appendChild(ipRange);
                        
                        // Añadir listeners a los botones
                        const deleteBtn = ipRange.querySelector('.ip-delete');
                        if (deleteBtn) {
                            deleteBtn.addEventListener('click', function() {
                                ipRange.remove();
                            });
                        }
                    }
                    
                    ipRangeModal.hide();
                });
            }
        }
        
        // Modal para reautorizar OAuth
        const reauthorizeBtn = document.getElementById('reauthorizeBtn');
        if (reauthorizeBtn && document.getElementById('reauthorizeModal')) {
            const reauthorizeModal = new bootstrap.Modal(document.getElementById('reauthorizeModal'));
            const confirmReauthorizeBtn = document.getElementById('confirmReauthorizeBtn');
            
            reauthorizeBtn.addEventListener('click', function() {
                reauthorizeModal.show();
            });
            
            if (confirmReauthorizeBtn) {
                confirmReauthorizeBtn.addEventListener('click', function() {
                    // Simular proceso de reautorización
                    reauthorizeModal.hide();
                    // Aquí iría la lógica para reautorizar
                    showAlert(successAlert, 'La cuenta ha sido reautorizada correctamente.');
                });
            }
        }
    }
});