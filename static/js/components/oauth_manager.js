// static/js/components/oauth_manager.js
/**
 * oauth_manager.js - Maneja la integración OAuth 2.0 para cuentas de correo de Google
 * Parte del módulo de configuración de ZentraFlow
 */

class OAuthManager {
    constructor() {
        // Referencias a elementos DOM
        this.clientIdInput = document.getElementById('clientId');
        this.clientSecretInput = document.getElementById('clientSecret');
        this.emailMonitorInput = document.getElementById('emailMonitor');
        this.folderMonitorSelect = document.getElementById('folderMonitor');
        this.checkIntervalInput = document.getElementById('checkInterval');
        this.markAsReadSwitch = document.getElementById('markAsRead');
        this.authorizeBtn = document.getElementById('authorizeBtn');
        this.reauthorizeBtn = document.getElementById('reauthorizeBtn');
        this.revokeBtn = document.getElementById('revokeBtn');
        
        this.authStatusEl = document.getElementById('authStatus');
        this.lastAuthTimeEl = document.getElementById('lastAuthTime');
        
        // Estado
        this.authorized = false;
        this.tokenValid = false;
        this.emailAddress = null;
        this.lastAuthorized = null;

        // Inicializar
        this.init();
    }

    init() {
        // Añadir event listeners
        if (this.authorizeBtn) {
            this.authorizeBtn.addEventListener('click', this.startAuthFlow.bind(this));
        }
        
        if (this.reauthorizeBtn) {
            this.reauthorizeBtn.addEventListener('click', this.startAuthFlow.bind(this));
        }
        
        if (this.revokeBtn) {
            this.revokeBtn.addEventListener('click', this.revokeAccess.bind(this));
        }
        
        // Detectar cambios en los inputs que requieren reautorización
        if (this.clientIdInput) {
            this.clientIdInput.addEventListener('change', this.onCredentialsChanged.bind(this));
        }
        
        if (this.clientSecretInput) {
            this.clientSecretInput.addEventListener('change', this.onCredentialsChanged.bind(this));
        }
        
        // Detectar cambios en configuración que no requieren reautorización
        if (this.folderMonitorSelect) {
            this.folderMonitorSelect.addEventListener('change', this.saveSettings.bind(this));
        }
        
        if (this.checkIntervalInput) {
            this.checkIntervalInput.addEventListener('change', this.saveSettings.bind(this));
        }
        
        if (this.markAsReadSwitch) {
            this.markAsReadSwitch.addEventListener('change', this.saveSettings.bind(this));
        }
        
        // Verificar estado de autorización al cargar
        this.checkAuthStatus();
        
        // Registrar listener para mensajes de la ventana de autorización
        window.addEventListener('message', this.handleOAuthMessage.bind(this));
    }

    checkAuthStatus() {
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/status/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.authorized = data.authorized;
                    this.tokenValid = data.token_valid;
                    this.emailAddress = data.email_address;
                    this.lastAuthorized = data.last_authorized;
                    
                    this.updateUI();
                    
                    // Si hay valores guardados, actualizar los campos
                    if (data.folder_to_monitor && this.folderMonitorSelect) {
                        this.folderMonitorSelect.value = data.folder_to_monitor;
                    }
                    
                    if (data.check_interval && this.checkIntervalInput) {
                        this.checkIntervalInput.value = data.check_interval;
                    }
                    
                    if (this.markAsReadSwitch) {
                        this.markAsReadSwitch.checked = data.mark_as_read;
                    }
                    
                    if (this.emailAddress && this.emailMonitorInput) {
                        this.emailMonitorInput.value = this.emailAddress;
                    }
                }
            })
            .catch(error => {
                console.error('Error al verificar estado OAuth:', error);
                this.showMessage('error', 'Error al verificar el estado de autorización');
            });
    }

    updateUI() {
        // Actualizar elementos de UI según estado
        if (this.authStatusEl) {
            if (this.authorized && this.tokenValid) {
                this.authStatusEl.innerHTML = `
                    <span class="badge bg-success">
                        <i class="fas fa-check-circle"></i> Autorizado
                    </span>
                `;
            } else if (this.authorized && !this.tokenValid) {
                this.authStatusEl.innerHTML = `
                    <span class="badge bg-warning">
                        <i class="fas fa-exclamation-triangle"></i> Token expirado
                    </span>
                `;
            } else {
                this.authStatusEl.innerHTML = `
                    <span class="badge bg-danger">
                        <i class="fas fa-times-circle"></i> No autorizado
                    </span>
                `;
            }
        }
        
        // Actualizar último tiempo de autorización
        if (this.lastAuthTimeEl && this.lastAuthorized) {
            const date = new Date(this.lastAuthorized);
            this.lastAuthTimeEl.textContent = date.toLocaleString();
        }
        
        // Cambiar visibilidad de botones
        if (this.authorizeBtn) {
            this.authorizeBtn.style.display = this.authorized ? 'none' : 'inline-block';
        }
        
        if (this.reauthorizeBtn) {
            this.reauthorizeBtn.style.display = this.authorized ? 'inline-block' : 'none';
        }
        
        if (this.revokeBtn) {
            this.revokeBtn.style.display = this.authorized ? 'inline-block' : 'none';
        }
        
        // Deshabilitar input de email si ya está autorizado
        if (this.emailMonitorInput) {
            this.emailMonitorInput.disabled = this.authorized;
        }
    }

    startAuthFlow(event) {  // Añadir el parámetro event
        // Obtener valores actuales
        const clientId = this.clientIdInput ? this.clientIdInput.value.trim() : '';
        const clientSecret = this.clientSecretInput ? this.clientSecretInput.value.trim() : '';
        
        // Validar que tenemos la información necesaria
        if (!clientId || !clientSecret) {
            this.showMessage('error', 'Debes configurar Client ID y Client Secret para continuar');
            return;
        }
        
        // Mostrar estado de carga
        const button = event ? event.target : this.authorizeBtn || this.reauthorizeBtn;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Conectando...';
        
        // Guardar configuración primero
        this.saveSettings()
            .then(result => {
                if (!result.success) {
                    throw new Error(result.message || 'Error al guardar configuración');
                }
                
                // Obtener URL de autorización
                return this.getAuthorizationUrl();
            })
            .then(data => {
                if (!data.success || !data.auth_url) {
                    throw new Error(data.message || 'Error al obtener URL de autorización');
                }
                
                // Abrir ventana de autorización
                const width = 600;
                const height = 700;
                const left = (window.innerWidth - width) / 2;
                const top = (window.innerHeight - height) / 2;
                
                window.open(
                    data.auth_url,
                    'oauth_window',
                    `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes`
                );
            })
            .catch(error => {
                console.error('Error al iniciar flujo OAuth:', error);
                this.showMessage('error', error.message || 'Error al iniciar autorización');
            })
            .finally(() => {
                // Restaurar botón
                button.disabled = false;
                button.innerHTML = originalText;
            });
    }

    getAuthorizationUrl() {
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/authorize/';
        if (tenant_id) {
            url += `?tenant_id=${tenant_id}`;
        }
        
        return fetch(url)
            .then(response => response.json())
            .catch(error => {
                console.error('Error al obtener URL de autorización:', error);
                return { success: false, message: 'Error de conexión al servidor' };
            });
    }

    revokeAccess() {
        if (!confirm('¿Está seguro que desea revocar el acceso a esta cuenta de correo?')) {
            return;
        }
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/revoke/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        // Mostrar estado de carga
        const button = event.target;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Revocando...';
        
        // Obtener CSRF token para POST
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showMessage('success', 'Acceso revocado correctamente');
                this.authorized = false;
                this.tokenValid = false;
                this.updateUI();
                
                // Habilitar el input de email
                if (this.emailMonitorInput) {
                    this.emailMonitorInput.disabled = false;
                }
            } else {
                throw new Error(data.message || 'Error al revocar acceso');
            }
        })
        .catch(error => {
            console.error('Error al revocar acceso OAuth:', error);
            this.showMessage('error', error.message || 'Error al revocar acceso');
        })
        .finally(() => {
            // Restaurar botón
            button.disabled = false;
            button.innerHTML = originalText;
        });
    }

    
    onCredentialsChanged() {
        // Si se cambian las credenciales, mostrar mensaje de que se requiere reautorización
        if (this.authorized) {
            this.showMessage('warning', 'Has modificado las credenciales, necesitarás reautorizar la conexión');
        }
    }

    saveSettings() {
        // Recopilar datos actuales
        const formData = new FormData();
        
        if (this.clientIdInput) {
            formData.append('client_id', this.clientIdInput.value.trim());
        }
        
        if (this.clientSecretInput) {
            formData.append('client_secret', this.clientSecretInput.value.trim());
        }
        
        if (this.emailMonitorInput) {
            formData.append('email_address', this.emailMonitorInput.value.trim());
        }
        
        if (this.folderMonitorSelect) {
            formData.append('folder_to_monitor', this.folderMonitorSelect.value);
        }
        
        if (this.checkIntervalInput) {
            formData.append('check_interval', this.checkIntervalInput.value);
        }
        
        if (this.markAsReadSwitch) {
            formData.append('mark_as_read', this.markAsReadSwitch.checked);
        }
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/settings/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        // Obtener CSRF token para POST
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        return fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error al guardar configuración OAuth:', error);
            return { success: false, message: 'Error de conexión al servidor' };
        });
    }

    handleOAuthMessage(event) {
        // Verificar origen del mensaje (seguridad)
        if (event.origin !== window.location.origin) {
            return;
        }
        
        // Verificar que sea un mensaje de OAuth
        const data = event.data;
        if (data && data.type === 'oauth_result') {
            if (data.success) {
                this.showMessage('success', '¡Autorización completada con éxito!');
                // Recargar estado de autorización
                this.checkAuthStatus();
            } else {
                this.showMessage('error', `Error en la autorización: ${data.message}`);
            }
        }
    }

    showMessage(type, message) {
        // Mostrar mensaje usando alertas existentes
        const alertId = type === 'error' ? 'errorAlert' : 'successAlert';
        const alertEl = document.getElementById(alertId);
        
        if (alertEl) {
            const messageContainer = alertEl.querySelector('.alert-message');
            if (messageContainer) {
                const strongEl = messageContainer.querySelector('strong');
                const strongText = strongEl ? strongEl.textContent : (type === 'error' ? 'Error:' : '¡Éxito!');
                messageContainer.innerHTML = `<strong>${strongText}</strong> ${message}`;
                alertEl.classList.add('show');
                
                // Ocultar después de 5 segundos
                setTimeout(() => {
                    alertEl.classList.remove('show');
                }, 5000);
            } else {
                alert(`${type === 'error' ? 'Error' : 'Éxito'}: ${message}`);
            }
        } else {
            alert(`${type === 'error' ? 'Error' : 'Éxito'}: ${message}`);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
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
});