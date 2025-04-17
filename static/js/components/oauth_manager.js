// static/js/components/oauth_manager.js
/**
 * oauth_manager.js - Maneja la integración OAuth 2.0 para cuentas de correo de Google
 * Versión mejorada para diagnóstico de problemas de guardado
 */

class OAuthManager {
    constructor() {
        console.log('[OAuthManager] Inicializando OAuthManager');
        
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
        this.saveOAuthConfigBtn = document.getElementById('saveOAuthConfigBtn');
        this.ingestaEnabledSwitch = document.getElementById('ingestaEnabled');
        
        this.authStatusEl = document.getElementById('authStatus');
        this.lastAuthTimeEl = document.getElementById('lastAuthTime');
        
        // Registro de elementos encontrados/no encontrados para debugging
        console.log('[OAuthManager] Elementos encontrados:');
        console.log('clientIdInput:', !!this.clientIdInput);
        console.log('clientSecretInput:', !!this.clientSecretInput);
        console.log('emailMonitorInput:', !!this.emailMonitorInput);
        console.log('folderMonitorSelect:', !!this.folderMonitorSelect);
        console.log('checkIntervalInput:', !!this.checkIntervalInput);
        console.log('markAsReadSwitch:', !!this.markAsReadSwitch);
        console.log('authorizeBtn:', !!this.authorizeBtn);
        console.log('reauthorizeBtn:', !!this.reauthorizeBtn);
        console.log('revokeBtn:', !!this.revokeBtn);
        console.log('saveOAuthConfigBtn:', !!this.saveOAuthConfigBtn);
        console.log('ingestaEnabledSwitch:', !!this.ingestaEnabledSwitch);
        console.log('authStatusEl:', !!this.authStatusEl);
        console.log('lastAuthTimeEl:', !!this.lastAuthTimeEl);
        
        // Estado
        this.authorized = false;
        this.tokenValid = false;
        this.emailAddress = null;
        this.lastAuthorized = null;

        // Inicializar
        this.init();
    }

    /**
     * Método para enviar logs al servidor (simplificado por ahora)
     */
    logToServer(message) {
        console.log('[SERVER LOG]', message);
        // Implementación de envío real omitida para simplificar
    }

    init() {
        console.log('[OAuthManager] Iniciando configuración de event listeners');
        
        // Añadir event listeners para botones de autorización
        if (this.authorizeBtn) {
            this.authorizeBtn.addEventListener('click', this.startAuthFlow.bind(this));
        }
        
        if (this.reauthorizeBtn) {
            this.reauthorizeBtn.addEventListener('click', this.startAuthFlow.bind(this));
        }
        
        if (this.revokeBtn) {
            this.revokeBtn.addEventListener('click', this.revokeAccess.bind(this));
        }
        
        // PARTE CRÍTICA: Botón para guardar configuración OAuth
        if (this.saveOAuthConfigBtn) {
            console.log('[OAuthManager] Añadiendo event listener a saveOAuthConfigBtn');
            
            this.saveOAuthConfigBtn.addEventListener('click', (e) => {
                console.log('[OAuthManager] Botón saveOAuthConfigBtn clickeado', e);
                e.preventDefault();
                this.saveSettingsAndShowMessage(e);
            });
        } else {
            console.error('[OAuthManager] No se encontró el botón saveOAuthConfigBtn');
            
            // Intento alternativo: querySelector en lugar de getElementById
            const saveBtn = document.querySelector('button#saveOAuthConfigBtn');
            if (saveBtn) {
                console.log('[OAuthManager] Encontrado saveOAuthConfigBtn mediante querySelector');
                this.saveOAuthConfigBtn = saveBtn;
                
                saveBtn.addEventListener('click', (e) => {
                    console.log('[OAuthManager] Botón saveOAuthConfigBtn (alternativo) clickeado', e);
                    e.preventDefault();
                    this.saveSettingsAndShowMessage(e);
                });
            } else {
                console.error('[OAuthManager] No se pudo encontrar el botón saveOAuthConfigBtn por ningún método');
                
                // Último recurso: encontrar cualquier botón de guardar en la pestaña de correo
                this.setupFallbackButtons();
            }
        }
        
        // Detectar cambios en campos del formulario
        if (this.clientIdInput) this.clientIdInput.addEventListener('change', this.onCredentialsChanged.bind(this));
        if (this.clientSecretInput) this.clientSecretInput.addEventListener('change', this.onCredentialsChanged.bind(this));
        if (this.folderMonitorSelect) this.folderMonitorSelect.addEventListener('change', this.onConfigChanged.bind(this));
        if (this.checkIntervalInput) this.checkIntervalInput.addEventListener('change', this.onConfigChanged.bind(this));
        if (this.markAsReadSwitch) this.markAsReadSwitch.addEventListener('change', this.onConfigChanged.bind(this));
        if (this.ingestaEnabledSwitch) this.ingestaEnabledSwitch.addEventListener('change', this.onConfigChanged.bind(this));
        
        // Verificar estado de autorización al cargar
        this.checkAuthStatus();
        
        // Registrar listener para mensajes de la ventana de autorización
        window.addEventListener('message', this.handleOAuthMessage.bind(this));
        
        // Delegación de eventos para capturar clics en botones de guardar
        document.addEventListener('click', (e) => {
            // Solo procesar clics en la pestaña de correo
            const correoTab = document.getElementById('correo');
            if (!correoTab || !correoTab.contains(e.target)) return;
            
            // Verificar si es un botón de guardar
            const button = e.target.closest('button');
            if (button && 
                (button.textContent.includes('Guardar') || 
                 button.innerHTML.includes('fa-save') || 
                 button.id === 'saveOAuthConfigBtn')) {
                
                console.log('[OAuthManager] Botón de guardar detectado mediante delegación:', button);
                
                // Evitar duplicación si ya es nuestro botón principal
                if (button !== this.saveOAuthConfigBtn) {
                    e.preventDefault();
                    this.saveSettingsAndShowMessage(e);
                }
            }
        });
    }

    setupFallbackButtons() {
        console.log('[OAuthManager] Configurando botones de respaldo');
        
        // Buscar todos los botones en la pestaña de correo
        const correoTab = document.getElementById('correo');
        if (!correoTab) {
            console.error('[OAuthManager] No se encontró la pestaña de correo');
            return;
        }
        
        const buttons = correoTab.querySelectorAll('button');
        console.log('[OAuthManager] Botones encontrados en la pestaña correo:', buttons.length);
        
        buttons.forEach((button, index) => {
            console.log(`[OAuthManager] Botón ${index}:`, button.outerHTML);
            
            // Si parece ser un botón de guardar, añadir nuestro listener
            if (button.textContent.includes('Guardar') || 
                button.innerHTML.includes('fa-save') || 
                button.classList.contains('btn-primary')) {
                
                console.log('[OAuthManager] Añadiendo listener de respaldo a:', button);
                
                button.addEventListener('click', (e) => {
                    console.log('[OAuthManager] Botón de respaldo clickeado:', e.target);
                    e.preventDefault();
                    this.saveSettingsAndShowMessage(e);
                });
            }
        });
    }
    
    checkAuthStatus() {
        console.log('[OAuthManager] Verificando estado de autorización OAuth');
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        console.log('[OAuthManager] ID de tenant extraído de la URL:', tenant_id || 'ninguno');
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/status/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        console.log('[OAuthManager] URL para verificar estado OAuth:', url);
        
        fetch(url)
            .then(response => {
                console.log('[OAuthManager] Respuesta de estado OAuth recibida, status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('[OAuthManager] Datos de estado OAuth:', data);
                
                if (data.success) {
                    this.authorized = data.authorized;
                    this.tokenValid = data.token_valid;
                    this.emailAddress = data.email_address;
                    this.lastAuthorized = data.last_authorized;
                    
                    console.log('[OAuthManager] Estado OAuth actualizado:', {
                        authorized: this.authorized,
                        tokenValid: this.tokenValid,
                        emailAddress: this.emailAddress,
                        lastAuthorized: this.lastAuthorized
                    });
                    
                    this.updateUI();
                    
                    // Si hay valores guardados, actualizar los campos
                    if (data.folder_to_monitor && this.folderMonitorSelect) {
                        console.log('[OAuthManager] Estableciendo folder_to_monitor:', data.folder_to_monitor);
                        this.folderMonitorSelect.value = data.folder_to_monitor;
                    }
                    
                    if (data.check_interval && this.checkIntervalInput) {
                        console.log('[OAuthManager] Estableciendo check_interval:', data.check_interval);
                        this.checkIntervalInput.value = data.check_interval;
                    }
                    
                    if (this.markAsReadSwitch && data.hasOwnProperty('mark_as_read')) {
                        console.log('[OAuthManager] Estableciendo mark_as_read:', data.mark_as_read);
                        this.markAsReadSwitch.checked = data.mark_as_read;
                    }
                    
                    if (this.emailAddress && this.emailMonitorInput) {
                        console.log('[OAuthManager] Estableciendo email_address:', this.emailAddress);
                        this.emailMonitorInput.value = this.emailAddress;
                    }
                    
                    if (this.ingestaEnabledSwitch && data.hasOwnProperty('ingesta_enabled')) {
                        console.log('[OAuthManager] Estableciendo ingesta_enabled:', data.ingesta_enabled);
                        this.ingestaEnabledSwitch.checked = data.ingesta_enabled;
                    }
                }
            })
            .catch(error => {
                console.error('[OAuthManager] Error al verificar estado OAuth:', error);
                this.showMessage('error', 'Error al verificar el estado de autorización');
            });
    }

    updateUI() {
        console.log('[OAuthManager] Actualizando UI según estado OAuth');
        
        // Actualizar elementos de UI según estado
        if (this.authStatusEl) {
            if (this.authorized && this.tokenValid) {
                console.log('[OAuthManager] Mostrando estado: Autorizado');
                this.authStatusEl.innerHTML = `
                    <span class="badge bg-success">
                        <i class="fas fa-check-circle"></i> Autorizado
                    </span>
                `;
            } else if (this.authorized && !this.tokenValid) {
                console.log('[OAuthManager] Mostrando estado: Token expirado');
                this.authStatusEl.innerHTML = `
                    <span class="badge bg-warning">
                        <i class="fas fa-exclamation-triangle"></i> Token expirado
                    </span>
                `;
            } else {
                console.log('[OAuthManager] Mostrando estado: No autorizado');
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
            console.log('[OAuthManager] Mostrando última autorización:', date.toLocaleString());
            this.lastAuthTimeEl.textContent = date.toLocaleString();
        }
        
        // Cambiar visibilidad de botones
        if (this.authorizeBtn) {
            console.log('[OAuthManager] Configurando visibilidad de authorizeBtn:', !this.authorized);
            this.authorizeBtn.style.display = this.authorized ? 'none' : 'inline-block';
        }
        
        if (this.reauthorizeBtn) {
            console.log('[OAuthManager] Configurando visibilidad de reauthorizeBtn:', this.authorized);
            this.reauthorizeBtn.style.display = this.authorized ? 'inline-block' : 'none';
        }
        
        if (this.revokeBtn) {
            console.log('[OAuthManager] Configurando visibilidad de revokeBtn:', this.authorized);
            this.revokeBtn.style.display = this.authorized ? 'inline-block' : 'none';
        }
        
        // Deshabilitar input de email si ya está autorizado
        if (this.emailMonitorInput) {
            console.log('[OAuthManager] Configurando disabled de emailMonitorInput:', this.authorized);
            this.emailMonitorInput.disabled = this.authorized;
        }
    }
    
    startAuthFlow(event) {
        console.log('[OAuthManager] Iniciando flujo de autorización OAuth');
        
        // Obtener valores actuales
        const clientId = this.clientIdInput ? this.clientIdInput.value.trim() : '';
        const clientSecret = this.clientSecretInput ? this.clientSecretInput.value.trim() : '';
        
        console.log('[OAuthManager] Client ID disponible:', !!clientId);
        console.log('[OAuthManager] Client Secret disponible:', !!clientSecret);
        
        // Validar que tenemos la información necesaria
        if (!clientId || !clientSecret) {
            console.warn('[OAuthManager] Faltan credenciales OAuth');
            this.showMessage('error', 'Debes configurar Client ID y Client Secret para continuar');
            return;
        }
        
        // Mostrar estado de carga
        const button = event ? event.target : this.authorizeBtn || this.reauthorizeBtn;
        if (!button) {
            console.error('[OAuthManager] No se pudo determinar el botón que inició la acción');
            return;
        }
        
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Conectando...';
        console.log('[OAuthManager] Botón de autorización deshabilitado y mostrando estado de carga');
        
        // Guardar configuración primero
        this.saveSettings()
            .then(result => {
                console.log('[OAuthManager] Resultado de guardar configuración:', result);
                
                if (!result.success) {
                    throw new Error(result.message || 'Error al guardar configuración');
                }
                
                // Obtener URL de autorización
                console.log('[OAuthManager] Solicitando URL de autorización');
                return this.getAuthorizationUrl();
            })
            .then(data => {
                console.log('[OAuthManager] Respuesta de URL de autorización:', data);
                
                if (!data.success || !data.auth_url) {
                    throw new Error(data.message || 'Error al obtener URL de autorización');
                }
                
                // Abrir ventana de autorización
                const width = 600;
                const height = 700;
                const left = (window.innerWidth - width) / 2;
                const top = (window.innerHeight - height) / 2;
                
                console.log('[OAuthManager] Abriendo ventana de autorización OAuth');
                window.open(
                    data.auth_url,
                    'oauth_window',
                    `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes`
                );
            })
            .catch(error => {
                console.error('[OAuthManager] Error al iniciar flujo OAuth:', error);
                this.showMessage('error', error.message || 'Error al iniciar autorización');
            })
            .finally(() => {
                // Restaurar botón
                button.disabled = false;
                button.innerHTML = originalText;
                console.log('[OAuthManager] Botón de autorización restaurado');
            });
    }

    getAuthorizationUrl() {
        console.log('[OAuthManager] Obteniendo URL de autorización');
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        console.log('[OAuthManager] ID de tenant para URL de autorización:', tenant_id || 'ninguno');
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/authorize/';
        if (tenant_id) {
            url += `?tenant_id=${tenant_id}`;
        }
        
        console.log('[OAuthManager] Solicitando URL de autorización a:', url);
        
        return fetch(url)
            .then(response => {
                console.log('[OAuthManager] Respuesta de URL de autorización recibida, status:', response.status);
                return response.json();
            })
            .catch(error => {
                console.error('[OAuthManager] Error al obtener URL de autorización:', error);
                return { success: false, message: 'Error de conexión al servidor' };
            });
    }

    revokeAccess(event) {
        console.log('[OAuthManager] Iniciando revocación de acceso OAuth');
        
        if (!confirm('¿Está seguro que desea revocar el acceso a esta cuenta de correo?')) {
            console.log('[OAuthManager] Revocación cancelada por el usuario');
            return;
        }
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        console.log('[OAuthManager] ID de tenant para revocación:', tenant_id || 'ninguno');
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/revoke/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        console.log('[OAuthManager] URL para revocar acceso:', url);
        
        // Mostrar estado de carga
        const button = event.target;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Revocando...';
        console.log('[OAuthManager] Botón de revocación deshabilitado y mostrando estado de carga');
        
        // Obtener CSRF token para POST
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        if (!csrftoken) {
            console.error('[OAuthManager] No se encontró token CSRF');
            this.showMessage('error', 'Error de seguridad: token CSRF no encontrado');
            return;
        }
        
        console.log('[OAuthManager] Token CSRF encontrado');
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('[OAuthManager] Respuesta de revocación recibida, status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('[OAuthManager] Datos de respuesta de revocación:', data);
            
            if (data.success) {
                this.showMessage('success', 'Acceso revocado correctamente');
                this.authorized = false;
                this.tokenValid = false;
                this.updateUI();
                
                // Habilitar el input de email
                if (this.emailMonitorInput) {
                    console.log('[OAuthManager] Habilitando input de email después de revocar');
                    this.emailMonitorInput.disabled = false;
                }
            } else {
                throw new Error(data.message || 'Error al revocar acceso');
            }
        })
        .catch(error => {
            console.error('[OAuthManager] Error al revocar acceso OAuth:', error);
            this.showMessage('error', error.message || 'Error al revocar acceso');
        })
        .finally(() => {
            // Restaurar botón
            button.disabled = false;
            button.innerHTML = originalText;
            console.log('[OAuthManager] Botón de revocación restaurado');
        });
    }

    onCredentialsChanged() {
        console.log('[OAuthManager] Credenciales OAuth modificadas');
        
        // Si se cambian las credenciales, mostrar mensaje de que se requiere reautorización
        if (this.authorized) {
            console.log('[OAuthManager] Se requiere reautorización después de cambiar credenciales');
            this.showMessage('warning', 'Has modificado las credenciales, necesitarás reautorizar la conexión');
        }
    }

    onConfigChanged() {
        console.log('[OAuthManager] Configuración OAuth modificada');
        
        // Informar al usuario que los cambios requieren guardado
        const saveBtn = this.saveOAuthConfigBtn;
        if (saveBtn) {
            console.log('[OAuthManager] Actualizando estilo del botón para indicar cambios pendientes');
            
            // Visual feedback que hay cambios pendientes
            saveBtn.classList.add('btn-warning');
            saveBtn.classList.remove('btn-primary');
            
            // Si después de 1.5s no se restaura automáticamente, restauramos nosotros
            setTimeout(() => {
                if (saveBtn.classList.contains('btn-warning')) {
                    console.log('[OAuthManager] Restaurando estilo del botón después de timeout');
                    saveBtn.classList.remove('btn-warning');
                    saveBtn.classList.add('btn-primary');
                }
            }, 1500);
        }
    }

    saveSettings() {
        console.log('[OAuthManager] Guardando configuración OAuth');
        
        // Recopilar datos actuales
        const formData = new FormData();
        
        // CRÍTICO: Añadir TODOS los campos relevantes
        if (this.clientIdInput) {
            formData.append('client_id', this.clientIdInput.value.trim());
            console.log('[OAuthManager] Guardando client_id:', this.clientIdInput.value.trim());
        }
        
        if (this.clientSecretInput) {
            formData.append('client_secret', this.clientSecretInput.value.trim());
            console.log('[OAuthManager] Guardando client_secret: [OCULTO]');
        }
        
        if (this.emailMonitorInput) {
            formData.append('email_address', this.emailMonitorInput.value.trim());
            console.log('[OAuthManager] Guardando email_address:', this.emailMonitorInput.value.trim());
        }
        
        // IMPORTANTE: Estos son los campos que podrían no estar guardándose
        if (this.folderMonitorSelect) {
            formData.append('folder_to_monitor', this.folderMonitorSelect.value);
            console.log('[OAuthManager] Guardando folder_to_monitor:', this.folderMonitorSelect.value);
        }
        
        if (this.checkIntervalInput) {
            formData.append('check_interval', this.checkIntervalInput.value);
            console.log('[OAuthManager] Guardando check_interval:', this.checkIntervalInput.value);
        }
        
        if (this.markAsReadSwitch) {
            formData.append('mark_as_read', this.markAsReadSwitch.checked);
            console.log('[OAuthManager] Guardando mark_as_read:', this.markAsReadSwitch.checked);
        }
        
        if (this.ingestaEnabledSwitch) {
            formData.append('ingesta_enabled', this.ingestaEnabledSwitch.checked);
            console.log('[OAuthManager] Guardando ingesta_enabled:', this.ingestaEnabledSwitch.checked);
        }
        
        // Listar todos los campos del FormData para debugging
        console.log('[OAuthManager] Campos en el FormData:');
        for (let pair of formData.entries()) {
            if (pair[0] === 'client_secret') {
                console.log(pair[0] + ': [OCULTO]');
            } else {
                console.log(pair[0] + ':', pair[1]);
            }
        }
        
        // Obtener tenant_id de la URL
        const path = window.location.pathname;
        const matches = path.match(/\/configuracion\/(\d+)\//);
        const tenant_id = matches ? matches[1] : '';
        
        console.log('[OAuthManager] ID de tenant para guardar configuración:', tenant_id || 'ninguno');
        
        // Construir URL para la solicitud
        let url = '/configuracion/oauth/settings/';
        if (tenant_id) {
            url += `${tenant_id}/`;
        }
        
        console.log('[OAuthManager] URL para guardar configuración:', url);
        
        // Obtener CSRF token para POST
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]');
        
        if (!csrftoken) {
            console.error('[OAuthManager] No se encontró token CSRF');
            return Promise.reject(new Error('Error de seguridad: token CSRF no encontrado'));
        }
        
        console.log('[OAuthManager] Token CSRF encontrado, enviando solicitud...');
        
        // REALIZAR SOLICITUD FETCH
        return fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken.value
            },
            body: formData
        })
        .then(response => {
            console.log('[OAuthManager] Respuesta recibida, status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('[OAuthManager] Datos de respuesta:', data);
            return data;
        })
        .catch(error => {
            console.error('[OAuthManager] Error al guardar configuración OAuth:', error);
            return { success: false, message: 'Error de conexión al servidor: ' + error.message };
        });
    }

    saveSettingsAndShowMessage(event) {
        console.log('[OAuthManager] Guardando configuración OAuth y mostrando mensaje');
        
        if (event) {
            event.preventDefault();
            console.log('[OAuthManager] Evento preventDefault llamado');
        }
        
        // Inspeccionar el estado actual de los campos
        if (this.folderMonitorSelect) {
            console.log('[OAuthManager] Valor actual de folderMonitorSelect:', this.folderMonitorSelect.value);
        }
        if (this.checkIntervalInput) {
            console.log('[OAuthManager] Valor actual de checkIntervalInput:', this.checkIntervalInput.value);
        }
        if (this.markAsReadSwitch) {
            console.log('[OAuthManager] Valor actual de markAsReadSwitch:', this.markAsReadSwitch.checked);
        }
        if (this.ingestaEnabledSwitch) {
            console.log('[OAuthManager] Valor actual de ingestaEnabledSwitch:', this.ingestaEnabledSwitch.checked);
        }
        
        // Mostrar estado de carga en el botón
        const button = event && event.target ? (event.target.closest('button') || event.target) : this.saveOAuthConfigBtn;
        
        if (!button) {
            console.warn('[OAuthManager] No se pudo determinar el botón de guardado, continuando sin actualizar UI');
        } else {
            console.log('[OAuthManager] Botón de guardado identificado:', button.id || 'sin-id');
            
            const originalText = button.innerHTML;
            const originalClass = button.className;
            
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
            console.log('[OAuthManager] Botón de guardado deshabilitado y mostrando estado de carga');
            
            // Restaurar botón después de la operación
            const restoreButton = () => {
                button.disabled = false;
                button.innerHTML = originalText;
                button.className = originalClass;
                console.log('[OAuthManager] Botón de guardado restaurado');
            };
            
            this.saveSettings()
                .then(result => {
                    console.log('[OAuthManager] Resultado de guardar configuración:', result);
                    
                if (result.success) {
                    this.showMessage('success', 'Configuración de ingesta de correo guardada correctamente');
                    return result;
                } else {
                    throw new Error(result.message || 'Error al guardar configuración');
                }
            })
            .catch(error => {
                console.error('[OAuthManager] Error al guardar configuración OAuth:', error);
                this.showMessage('error', error.message || 'Error al guardar configuración');
                throw error;
            })
            .finally(() => {
                restoreButton();
            });
        return;
    }
    
    // Si no encontramos botón, igual continuamos con el guardado
    return this.saveSettings()
        .then(result => {
            console.log('[OAuthManager] Resultado de guardar configuración:', result);
            
            if (result.success)
                if (result.success) {
                    this.showMessage('success', 'Configuración de ingesta de correo guardada correctamente');
                    // Refrescar el estado para mostrar los valores actualizados
                    setTimeout(() => {
                        this.checkAuthStatus();
                    }, 500);
                    return result;
                } else {
                    throw new Error(result.message || 'Error al guardar configuración');
                }
            })
            .catch(error => {
                console.error('[OAuthManager] Error al guardar configuración OAuth:', error);
                this.showMessage('error', error.message || 'Error al guardar configuración');
                throw error;
            });
    }

    showMessage(type, message) {
        console.log(`[OAuthManager] Mostrando mensaje ${type}:`, message);
        
        // Mostrar mensaje usando alertas existentes
        const alertId = type === 'error' ? 'errorAlert' : (type === 'warning' ? 'warningAlert' : 'successAlert');
        const alertEl = document.getElementById(alertId);
        
        if (alertEl) {
            console.log('[OAuthManager] Alerta encontrada:', alertId);
            const messageContainer = alertEl.querySelector('.alert-message');
            if (messageContainer) {
                console.log('[OAuthManager] Contenedor de mensaje encontrado');
                const strongEl = messageContainer.querySelector('strong');
                let strongText = '';
                
                if (strongEl) {
                    strongText = strongEl.textContent;
                    console.log('[OAuthManager] Texto fuerte encontrado:', strongText);
                } else {
                    if (type === 'error') strongText = 'Error:';
                    else if (type === 'warning') strongText = 'Advertencia:';
                    else strongText = '¡Éxito!';
                    console.log('[OAuthManager] Usando texto fuerte predeterminado:', strongText);
                }
                
                messageContainer.innerHTML = `<strong>${strongText}</strong> ${message}`;
                alertEl.classList.add('show');
                console.log('[OAuthManager] Alerta mostrada con clase show');
                
                // Ocultar después de 5 segundos
                setTimeout(() => {
                    alertEl.classList.remove('show');
                    console.log('[OAuthManager] Alerta ocultada después de 5 segundos');
                }, 5000);
            } else {
                console.warn('[OAuthManager] No se encontró el contenedor de mensaje en la alerta');
                alert(`${type === 'error' ? 'Error' : (type === 'warning' ? 'Advertencia' : 'Éxito')}: ${message}`);
            }
        } else {
            console.warn('[OAuthManager] No se encontró la alerta:', alertId);
            alert(`${type === 'error' ? 'Error' : (type === 'warning' ? 'Advertencia' : 'Éxito')}: ${message}`);
        }
    }

    handleOAuthMessage(event) {
        console.log('[OAuthManager] Mensaje recibido de ventana externa:', event.origin);
        
        // Verificar origen del mensaje (seguridad)
        if (event.origin !== window.location.origin) {
            console.warn('[OAuthManager] Mensaje rechazado por origen no seguro');
            return;
        }
        
        // Verificar que sea un mensaje de OAuth
        const data = event.data;
        console.log('[OAuthManager] Datos del mensaje:', data);
        
        if (data && data.type === 'oauth_result') {
            if (data.success) {
                console.log('[OAuthManager] Autorización OAuth completada con éxito');
                this.showMessage('success', '¡Autorización completada con éxito!');
                // Recargar estado de autorización
                this.checkAuthStatus();
            } else {
                console.error('[OAuthManager] Error en la autorización OAuth:', data.message);
                this.showMessage('error', `Error en la autorización: ${data.message}`);
            }
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('[OAuthManager] DOM cargado, inicializando componentes');
    
    // Verificar que estamos en la página correcta antes de inicializar
    const correoTab = document.querySelector('#correo-tab');
    const configTabs = document.querySelector('#configTabs');
    
    if (correoTab || configTabs) {
        console.log('[OAuthManager] Página de configuración detectada, inicializando OAuthManager');
        
        // Esperar a que Bootstrap termine de inicializar las pestañas
        setTimeout(() => {
            window.oauthManager = new OAuthManager();
            
            // Añadir listener para el cambio de pestaña
            if (correoTab) {
                document.addEventListener('shown.bs.tab', function(event) {
                    if (event.target.id === 'correo-tab') {
                        console.log('[OAuthManager] Pestaña de correo activada');
                        if (window.oauthManager) {
                            window.oauthManager.checkAuthStatus();
                        }
                    }
                });
                
                // Crear un listener específico para el botón de guardar en la pestaña de correo
                const saveOAuthBtn = document.querySelector('#correo button#saveOAuthConfigBtn');
                if (saveOAuthBtn) {
                    console.log('[OAuthManager] Encontrado botón específico saveOAuthConfigBtn en pestaña correo');
                    
                    // Eliminar listeners previos para evitar duplicados
                    const clonedBtn = saveOAuthBtn.cloneNode(true);
                    saveOAuthBtn.parentNode.replaceChild(clonedBtn, saveOAuthBtn);
                    
                    // Añadir nuevo listener
                    clonedBtn.addEventListener('click', function(e) {
                        console.log('[OAuthManager] Clic en botón saveOAuthConfigBtn (específico de correo)');
                        e.preventDefault();
                        e.stopPropagation();
                        if (window.oauthManager) {
                            window.oauthManager.saveSettingsAndShowMessage(e);
                        }
                    });
                }
            }
        }, 300);
    } else {
        console.log('[OAuthManager] No se detectó la página de configuración, no se inicializará OAuthManager');
    }
    
    // Evento global para capturar botones que no han sido detectados por OAuthManager
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('#saveOAuthConfigBtn');
        if (target && window.oauthManager) {
            console.log('[OAuthManager] Botón saveOAuthConfigBtn detectado por delegación global de eventos');
            e.preventDefault();
            window.oauthManager.saveSettingsAndShowMessage(e);
        }
    });
});