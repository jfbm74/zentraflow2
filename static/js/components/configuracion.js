// static/js/components/configuracion.js
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    const footerSaveBtn = document.getElementById('footerSaveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const successAlert = document.getElementById('successAlert');
    const tenantSelect = document.getElementById('tenant-select');
    const configTabs = document.getElementById('configTabs');
    const authMethodSelect = document.getElementById('authMethod');
    const oauthCredentials = document.getElementById('oauthCredentials');
    const serviceCredentials = document.getElementById('serviceCredentials');
    
    // Función para mostrar el mensaje de éxito
    function showSuccessMessage() {
        successAlert.classList.add('show');
        setTimeout(() => {
            successAlert.classList.remove('show');
        }, 3000);
    }
    
    // Función para cambiar de tenant
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
    
    // Cambiar entre tipos de autenticación de correo
    if (authMethodSelect) {
        authMethodSelect.addEventListener('change', function() {
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
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
    
    // Manejo del selector de idioma
    document.querySelectorAll('.language-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.language-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
        });
    });
    
    // Manejo del logo
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    
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
    
    if (removeLogoBtn) {
        removeLogoBtn.addEventListener('click', function() {
            logoPreview.src = '/static/images/placeholder-logo.png';
            if (logoUpload) {
                logoUpload.value = '';
            }
        });
    }
    
    // Manejo de reglas de filtro
    const addFilterBtn = document.querySelector('.add-filter-btn');
    if (addFilterBtn) {
        addFilterBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
            modal.show();
        });
    }
    
    const saveFilterBtn = document.getElementById('saveFilterBtn');
    if (saveFilterBtn) {
        saveFilterBtn.addEventListener('click', function() {
            const filterType = document.getElementById('filterType').value;
            const filterValue = document.getElementById('filterValue').value;
            
            if (filterValue.trim() !== '') {
                const filterRulesContainer = document.querySelector('.email-filter-rules');
                const newRule = document.createElement('div');
                newRule.className = 'filter-rule';
                newRule.innerHTML = `
                    <div class="filter-type">${filterType === 'from' ? 'De:' : filterType === 'subject' ? 'Asunto:' : filterType === 'body' ? 'Contenido:' : 'Tiene Adjunto:'}</div>
                    <div class="filter-value">${filterValue}</div>
                    <div class="filter-actions">
                        <button class="filter-edit"><i class="fas fa-edit"></i></button>
                        <button class="filter-delete"><i class="fas fa-times"></i></button>
                    </div>
                `;
                
                filterRulesContainer.insertBefore(newRule, addFilterBtn);
                
                // Agregar listeners para los nuevos botones
                newRule.querySelector('.filter-delete').addEventListener('click', function() {
                    newRule.remove();
                });
                
                newRule.querySelector('.filter-edit').addEventListener('click', function() {
                    // Rellenar el modal con los valores actuales
                    document.getElementById('filterType').value = filterType;
                    document.getElementById('filterValue').value = filterValue;
                    
                    // Mostrar modal
                    const modal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
                    modal.show();
                    
                    // Al guardar, actualizar en lugar de crear nuevo
                    saveFilterBtn.dataset.editing = true;
                    saveFilterBtn.dataset.editingRule = newRule;
                });
                
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('filterRuleModal')).hide();
            }
        });
    }
    
    // Manejo de rangos IP
    const addIpBtn = document.querySelector('.add-ip-btn');
    if (addIpBtn) {
        addIpBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('ipRangeModal'));
            modal.show();
        });
    }
    
    const saveIpBtn = document.getElementById('saveIpBtn');
    if (saveIpBtn) {
        saveIpBtn.addEventListener('click', function() {
            const ipRange = document.getElementById('ipRange').value;
            const ipDescription = document.getElementById('ipDescription').value;
            
            if (ipRange.trim() !== '') {
                const ipRestrictionsContainer = document.querySelector('.ip-restrictions');
                const newRange = document.createElement('div');
                newRange.className = 'ip-range';
                newRange.innerHTML = `
                    <div class="ip-value">${ipRange}</div>
                    <div class="ip-actions">
                        <button class="ip-edit"><i class="fas fa-edit"></i></button>
                        <button class="ip-delete"><i class="fas fa-times"></i></button>
                    </div>
                `;
                
                ipRestrictionsContainer.appendChild(newRange);
                
                // Agregar listeners para los nuevos botones
                newRange.querySelector('.ip-delete').addEventListener('click', function() {
                    newRange.remove();
                });
                
                newRange.querySelector('.ip-edit').addEventListener('click', function() {
                    // Rellenar el modal con los valores actuales
                    document.getElementById('ipRange').value = ipRange;
                    document.getElementById('ipDescription').value = ipDescription;
                    
                    // Mostrar modal
                    const modal = new bootstrap.Modal(document.getElementById('ipRangeModal'));
                    modal.show();
                    
                    // Al guardar, actualizar en lugar de crear nuevo
                    saveIpBtn.dataset.editing = true;
                    saveIpBtn.dataset.editingRange = newRange;
                });
                
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('ipRangeModal')).hide();
            }
        });
    }
    
    // Recopilar reglas y rangos para envío
    function collectFilterRules() {
        const rules = [];
        document.querySelectorAll('.filter-rule').forEach(rule => {
            const typeElement = rule.querySelector('.filter-type');
            const valueElement = rule.querySelector('.filter-value');
            
            if (typeElement && valueElement) {
                const typeText = typeElement.textContent;
                const type = typeText.includes('De:') ? 'from' : 
                             typeText.includes('Asunto:') ? 'subject' : 
                             typeText.includes('Contenido:') ? 'body' : 'has-attachment';
                             
                rules.push({
                    tipo: type,
                    valor: valueElement.textContent
                });
            }
        });
        
        return rules;
    }
    
    function collectIpRanges() {
        const ranges = [];
        document.querySelectorAll('.ip-range').forEach(range => {
            const valueElement = range.querySelector('.ip-value');
            
            if (valueElement) {
                ranges.push({
                    rango: valueElement.textContent,
                    descripcion: ''
                });
            }
        });
        
        return ranges;
    }
    
    // Lógica para guardar configuración
    function saveConfiguration() {
        // Determinar qué pestaña está activa
        const activeTab = document.querySelector('.nav-link.active').getAttribute('id');
        const tabName = activeTab.replace('-tab', '');
        
        // Crear FormData según la pestaña activa
        const formData = new FormData();
        formData.append('tab', tabName);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        if (tabName === 'general') {
            // Configuración general
            formData.append('clientName', document.getElementById('clientName').value);
            formData.append('clientNIT', document.getElementById('clientNIT').value);
            formData.append('zona_horaria', document.getElementById('timezone').value);
            formData.append('formato_fecha', document.getElementById('dateFormat').value);
            formData.append('idioma', document.querySelector('.language-option.selected').querySelector('span').textContent.toLowerCase());
            
            formData.append('modulo_ingesta', document.getElementById('moduloIngesta').checked);
            formData.append('modulo_extraccion', document.getElementById('moduloExtraccion').checked);
            formData.append('modulo_flujo', document.getElementById('moduloFlujo').checked);
            formData.append('modulo_pdf', document.getElementById('moduloPDF').checked);
            
            // Logo (si se cambió)
            if (logoUpload && logoUpload.files.length > 0) {
                formData.append('logo', logoUpload.files[0]);
            }
        } 
        else if (tabName === 'correo') {
            // Configuración de correo
            formData.append('ingesta_habilitada', document.getElementById('ingestaEnabled').checked);
            formData.append('correo_monitoreo', document.getElementById('emailMonitor').value);
            formData.append('metodo_autenticacion', document.getElementById('authMethod').value);
            
            if (document.getElementById('authMethod').value === 'oauth') {
                formData.append('client_id', document.getElementById('clientId').value);
                formData.append('client_secret', document.getElementById('clientSecret').value);
            }
            
            formData.append('carpeta_monitoreo', document.getElementById('folderMonitor').value);
            formData.append('intervalo_verificacion', document.getElementById('checkInterval').value);
            formData.append('marcar_leidos', document.getElementById('markAsRead').checked);
            
            // Reglas de filtro
            formData.append('reglas_filtro', JSON.stringify(collectFilterRules()));
        }
        else if (tabName === 'seguridad') {
            // Configuración de seguridad
            formData.append('req_mayusculas', document.getElementById('requireUppercase').checked);
            formData.append('req_numeros', document.getElementById('requireNumbers').checked);
            formData.append('req_especiales', document.getElementById('requireSpecial').checked);
            formData.append('longitud_min_password', document.getElementById('minLength').value);
            formData.append('intentos_bloqueo', document.getElementById('lockAttempts').value);
            formData.append('desbloqueo_automatico', document.getElementById('autoUnlock').checked);
            
            // Método 2FA
            let twoFactorMethod = 'disabled';
            if (document.getElementById('twoFactorEmail').checked) {
                twoFactorMethod = 'email';
            } else if (document.getElementById('twoFactorApp').checked) {
                twoFactorMethod = 'app';
            }
            formData.append('metodo_2fa', twoFactorMethod);
            
            // Rangos IP
            formData.append('rangos_ip', JSON.stringify(collectIpRanges()));
        }
        
        // Enviar datos al servidor
        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage();
            } else {
                alert('Error al guardar la configuración: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar la configuración');
        });
    }
    
    // Event listeners para botones de guardar
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveConfiguration);
    }
    
    if (footerSaveBtn) {
        footerSaveBtn.addEventListener('click', saveConfiguration);
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            window.location.reload();
        });
    }
    
    // Reautorizar OAuth
    const reauthorizeBtn = document.getElementById('reauthorizeBtn');
    if (reauthorizeBtn) {
        reauthorizeBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('reauthorizeModal'));
            modal.show();
        });
    }
    
    const confirmReauthorizeBtn = document.getElementById('confirmReauthorizeBtn');
    if (confirmReauthorizeBtn) {
        confirmReauthorizeBtn.addEventListener('click', function() {
            // Aquí iría la lógica para reautorizar OAuth
            alert('Proceso de reautorización iniciado. Se abrirá una ventana de Google para confirmar el acceso.');
            
            // Cerrar modal
            bootstrap.Modal.getInstance(document.getElementById('reauthorizeModal')).hide();
        });
    }
    
    // Inicialización al cargar la página
    // Mostrar/ocultar el tipo de autenticación correcto
    if (authMethodSelect) {
        const currentMethod = authMethodSelect.value;
        if (currentMethod === 'oauth') {
            oauthCredentials.style.display = 'block';
            serviceCredentials.style.display = 'none';
        } else {
            oauthCredentials.style.display = 'none';
            serviceCredentials.style.display = 'block';
        }
    }
    
    // Inicializar tooltips y popovers de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Sincronización de correo (botón en historial)
    const syncNowBtn = document.querySelector('.btn[data-action="sync-now"]');
    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', function() {
            // Mostrar spinner o indicador de carga
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sincronizando...';
            this.disabled = true;
            
            // Simulación de sincronización (esto sería una llamada real a la API)
            setTimeout(() => {
                // Actualizar UI después de sincronización
                this.innerHTML = '<i class="fas fa-sync-alt"></i> Sincronizar Ahora';
                this.disabled = false;
                
                // Añadir nueva entrada al historial
                const timelineContainer = document.querySelector('.history-timeline');
                const newItem = document.createElement('div');
                newItem.className = 'timeline-item';
                
                const now = new Date();
                const formattedDate = now.toLocaleDateString('es-CO') + ' ' + 
                                      now.getHours().toString().padStart(2, '0') + ':' + 
                                      now.getMinutes().toString().padStart(2, '0') + ':' + 
                                      now.getSeconds().toString().padStart(2, '0');
                
                newItem.innerHTML = `
                    <div class="timeline-marker success"></div>
                    <div class="timeline-content">
                        <div class="timeline-date">${formattedDate}</div>
                        <div class="timeline-title">Sincronización exitosa</div>
                        <div class="timeline-details">5 correos procesados, 1 nuevas glosas</div>
                    </div>
                `;
                
                // Insertar al inicio
                if (timelineContainer.firstChild) {
                    timelineContainer.insertBefore(newItem, timelineContainer.firstChild);
                } else {
                    timelineContainer.appendChild(newItem);
                }
                
                // Mostrar notificación
                showSuccessMessage();
            }, 2000);
        });
    }
    
    // Manejar sesiones activas (cerrar sesión)
    document.querySelectorAll('.btn-danger[data-action="close-session"]').forEach(button => {
        button.addEventListener('click', function() {
            const sessionRow = this.closest('tr');
            
            // Confirmar
            if (confirm('¿Está seguro que desea cerrar esta sesión?')) {
                // Simular cierre de sesión (esto sería una llamada real a la API)
                sessionRow.classList.add('table-danger');
                setTimeout(() => {
                    sessionRow.remove();
                }, 500);
            }
        });
    });
    
    // Cerrar todas las sesiones
    const closeAllSessionsBtn = document.querySelector('.btn-danger[data-action="close-all-sessions"]');
    if (closeAllSessionsBtn) {
        closeAllSessionsBtn.addEventListener('click', function() {
            // Confirmar
            if (confirm('¿Está seguro que desea cerrar todas las sesiones excepto la actual?')) {
                // Simular cierre de sesiones (esto sería una llamada real a la API)
                document.querySelectorAll('tr:not(.active-session)').forEach(row => {
                    row.classList.add('table-danger');
                    setTimeout(() => {
                        row.remove();
                    }, 500);
                });
            }
        });
    }
});