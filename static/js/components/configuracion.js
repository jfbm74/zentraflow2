/**
 * configuracion.js - Funcionalidades para el módulo de Configuración del Cliente
 */

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    const footerSaveBtn = document.getElementById('footerSaveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const successAlert = document.getElementById('successAlert');
    const configForm = document.querySelectorAll('.config-card');
    const authMethodSelect = document.getElementById('authMethod');
    const oauthCredentials = document.getElementById('oauthCredentials');
    const serviceCredentials = document.getElementById('serviceCredentials');
    const logoUpload = document.getElementById('logoUpload');
    const logoPreview = document.getElementById('logoPreview');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    const reauthorizeBtn = document.getElementById('reauthorizeBtn');
    const tenantSelect = document.getElementById('tenant-select');

    // Cambiar entre métodos de autenticación
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

    // Toggle de contraseña
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            // Cambiar icono
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });

    // Selector de idioma
    document.querySelectorAll('.language-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.language-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            this.classList.add('selected');
        });
    });

    // Gestión de logo
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
        removeLogoBtn.addEventListener('click', function() {
            logoPreview.src = '/static/images/placeholder-logo.png';
            if (logoUpload) {
                logoUpload.value = ''; // Limpiar input file
            }
        });
    }

    // Abrir modal para editar regla de filtro
    document.querySelectorAll('.filter-edit').forEach(button => {
        button.addEventListener('click', function() {
            const rule = this.closest('.filter-rule');
            const filterType = rule.querySelector('.filter-type').textContent.replace(':', '').trim();
            const filterValue = rule.querySelector('.filter-value').textContent.trim();
            
            // Configurar modal con valores actuales
            const filterTypeSelect = document.getElementById('filterType');
            const filterValueInput = document.getElementById('filterValue');
            
            // Seleccionar la opción correcta en el select
            for (let i = 0; i < filterTypeSelect.options.length; i++) {
                if (filterTypeSelect.options[i].text.startsWith(filterType)) {
                    filterTypeSelect.selectedIndex = i;
                    break;
                }
            }
            
            filterValueInput.value = filterValue;
            
            // Mostrar modal
            const filterModal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
            filterModal.show();
        });
    });

    // Eliminar regla de filtro
    document.querySelectorAll('.filter-delete').forEach(button => {
        button.addEventListener('click', function() {
            const rule = this.closest('.filter-rule');
            rule.remove();
        });
    });

    // Agregar regla de filtro
    const addFilterBtn = document.querySelector('.add-filter-btn');
    if (addFilterBtn) {
        addFilterBtn.addEventListener('click', function() {
            // Limpiar modal para nueva regla
            document.getElementById('filterType').selectedIndex = 0;
            document.getElementById('filterValue').value = '';
            
            // Mostrar modal
            const filterModal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
            filterModal.show();
        });
    }

    // Guardar regla de filtro
    const saveFilterBtn = document.getElementById('saveFilterBtn');
    if (saveFilterBtn) {
        saveFilterBtn.addEventListener('click', function() {
            const filterType = document.getElementById('filterType');
            const filterValue = document.getElementById('filterValue');
            const filterTypeText = filterType.options[filterType.selectedIndex].text;
            const filterValueText = filterValue.value.trim();
            
            if (filterValueText) {
                // Crear nueva regla
                const newRule = document.createElement('div');
                newRule.className = 'filter-rule';
                newRule.innerHTML = `
                    <div class="filter-type">${filterTypeText}:</div>
                    <div class="filter-value">${filterValueText}</div>
                    <div class="filter-actions">
                        <button class="filter-edit"><i class="fas fa-edit"></i></button>
                        <button class="filter-delete"><i class="fas fa-times"></i></button>
                    </div>
                `;
                
                // Agregar eventos a los botones de la nueva regla
                newRule.querySelector('.filter-edit').addEventListener('click', function() {
                    // Código para editar (similar al anterior)
                    const rule = this.closest('.filter-rule');
                    const filterType = rule.querySelector('.filter-type').textContent.replace(':', '').trim();
                    const filterValue = rule.querySelector('.filter-value').textContent.trim();
                    
                    const filterTypeSelect = document.getElementById('filterType');
                    const filterValueInput = document.getElementById('filterValue');
                    
                    for (let i = 0; i < filterTypeSelect.options.length; i++) {
                        if (filterTypeSelect.options[i].text.startsWith(filterType)) {
                            filterTypeSelect.selectedIndex = i;
                            break;
                        }
                    }
                    
                    filterValueInput.value = filterValue;
                    
                    const filterModal = new bootstrap.Modal(document.getElementById('filterRuleModal'));
                    filterModal.show();
                });
                
                newRule.querySelector('.filter-delete').addEventListener('click', function() {
                    this.closest('.filter-rule').remove();
                });
                
                // Insertar la nueva regla antes del botón
                document.querySelector('.email-filter-rules').insertBefore(newRule, addFilterBtn);
                
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('filterRuleModal')).hide();
            }
        });
    }

    // Manejo similar para restricciones IP
    document.querySelectorAll('.ip-delete').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.ip-range').remove();
        });
    });

    const addIpBtn = document.querySelector('.add-ip-btn');
    if (addIpBtn) {
        addIpBtn.addEventListener('click', function() {
            document.getElementById('ipRange').value = '';
            document.getElementById('ipDescription').value = '';
            
            const ipModal = new bootstrap.Modal(document.getElementById('ipRangeModal'));
            ipModal.show();
        });
    }

    const saveIpBtn = document.getElementById('saveIpBtn');
    if (saveIpBtn) {
        saveIpBtn.addEventListener('click', function() {
            const ipRange = document.getElementById('ipRange').value.trim();
            
            if (ipRange) {
                // Crear nuevo rango IP
                const newIpRange = document.createElement('div');
                newIpRange.className = 'ip-range';
                newIpRange.innerHTML = `
                    <div class="ip-value">${ipRange}</div>
                    <div class="ip-actions">
                        <button class="ip-edit"><i class="fas fa-edit"></i></button>
                        <button class="ip-delete"><i class="fas fa-times"></i></button>
                    </div>
                `;
                
                // Agregar eventos
                newIpRange.querySelector('.ip-delete').addEventListener('click', function() {
                    this.closest('.ip-range').remove();
                });
                
                // Insertar nuevo rango
                document.querySelector('.ip-restrictions').appendChild(newIpRange);
                
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('ipRangeModal')).hide();
            }
        });
    }

    // Reautorizar OAuth
    if (reauthorizeBtn) {
        reauthorizeBtn.addEventListener('click', function() {
            // Mostrar modal de confirmación
            const reauthorizeModal = new bootstrap.Modal(document.getElementById('reauthorizeModal'));
            reauthorizeModal.show();
        });
    }

    // Confirmar reautorización
    const confirmReauthorizeBtn = document.getElementById('confirmReauthorizeBtn');
    if (confirmReauthorizeBtn) {
        confirmReauthorizeBtn.addEventListener('click', function() {
            // Simular proceso de reautorización
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            this.disabled = true;
            
            setTimeout(function() {
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('reauthorizeModal')).hide();
                
                // Mostrar ventana de autorización de Google (simulado)
                window.open('/auth/google-oauth', 'oauth_window', 'width=600,height=700');
                
                // Restablecer botón
                confirmReauthorizeBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Sí, Reautorizar';
                confirmReauthorizeBtn.disabled = false;
            }, 1000);
        });
    }

    // Guardar configuración
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', function() {
            saveConfiguration();
        });
    }

    if (footerSaveBtn) {
        footerSaveBtn.addEventListener('click', function() {
            saveConfiguration();
        });
    }

    function saveConfiguration() {
        // Aquí iría la lógica real para enviar los datos al servidor
        // Por ahora solo mostramos una alerta de éxito
        
        // Mostrar spinner en botones de guardar
        saveConfigBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        saveConfigBtn.disabled = true;
        
        footerSaveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        footerSaveBtn.disabled = true;
        
        // Simular petición al servidor
        setTimeout(function() {
            // Reestablecer botones
            saveConfigBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
            saveConfigBtn.disabled = false;
            
            footerSaveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
            footerSaveBtn.disabled = false;
            
            // Mostrar alerta de éxito
            successAlert.classList.add('show');
            
            // Ocultar alerta después de 5 segundos
            setTimeout(function() {
                successAlert.classList.remove('show');
            }, 5000);
            
            // Hacer scroll al inicio para ver la alerta
            window.scrollTo({top: 0, behavior: 'smooth'});
        }, 1500);
    }

    // Cancelar cambios
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (confirm('¿Estás seguro de cancelar los cambios? Los cambios no guardados se perderán.')) {
                // Recargar la página para restaurar valores originales
                window.location.reload();
            }
        });
    }

    // Cambiar tenant (solo para Super Admin)
    if (tenantSelect) {
        tenantSelect.addEventListener('change', function() {
            const tenantId = this.value;
            if (tenantId) {
                // Redireccionar a la configuración del tenant seleccionado
                window.location.href = `/configuracion/${tenantId}/`;
            }
        });
    }

    // Cerrar sesiones activas
    document.querySelectorAll('.security-sessions .btn-danger').forEach(button => {
        if (!button.closest('.text-end')) { // Excluir el botón "Cerrar todas las sesiones"
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                
                // Simular cierre de sesión
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                button.disabled = true;
                
                setTimeout(() => {
                    row.style.opacity = '0.5';
                    row.style.textDecoration = 'line-through';
                    button.innerHTML = 'Cerrada';
                    button.classList.remove('btn-danger');
                    button.classList.add('btn-secondary');
                    button.disabled = true;
                }, 1000);
            });
        }
    });

    // Botón de "Cerrar todas las sesiones"
    const closeAllSessionsBtn = document.querySelector('.security-sessions .text-end .btn-danger');
    if (closeAllSessionsBtn) {
        closeAllSessionsBtn.addEventListener('click', function() {
            if (confirm('¿Está seguro que desea cerrar todas las otras sesiones activas?')) {
                // Simular cierre de todas las sesiones
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
                this.disabled = true;
                
                const sessionRows = document.querySelectorAll('.security-sessions tbody tr:not(.active-session)');
                
                setTimeout(() => {
                    sessionRows.forEach(row => {
                        row.style.opacity = '0.5';
                        row.style.textDecoration = 'line-through';
                        const btn = row.querySelector('.btn-danger');
                        if (btn) {
                            btn.innerHTML = 'Cerrada';
                            btn.classList.remove('btn-danger');
                            btn.classList.add('btn-secondary');
                            btn.disabled = true;
                        }
                    });
                    
                    this.innerHTML = '<i class="fas fa-check"></i> Sesiones Cerradas';
                    this.classList.remove('btn-danger');
                    this.classList.add('btn-success');
                    
                    // Restablecer después de 3 segundos
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-power-off"></i> Cerrar Todas las Sesiones';
                        this.classList.remove('btn-success');
                        this.classList.add('btn-danger');
                        this.disabled = false;
                    }, 3000);
                }, 1500);
            }
        });
    }

    // Manejo de sincronización de correo ahora
    const syncNowBtn = document.querySelector('.history-timeline').nextElementSibling.querySelector('.btn-primary');
    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', function() {
            // Mostrar spinner
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sincronizando...';
            this.disabled = true;
            
            // Simular sincronización
            setTimeout(() => {
                // Crear nuevo elemento de timeline
                const timelineItem = document.createElement('div');
                timelineItem.className = 'timeline-item';
                timelineItem.innerHTML = `
                    <div class="timeline-marker success"></div>
                    <div class="timeline-content">
                        <div class="timeline-date">15/04/2025 ${new Date().getHours()}:${String(new Date().getMinutes()).padStart(2, '0')}:${String(new Date().getSeconds()).padStart(2, '0')}</div>
                        <div class="timeline-title">Sincronización exitosa</div>
                        <div class="timeline-details">5 correos procesados, 0 nuevas glosas</div>
                    </div>
                `;
                
                // Insertar al inicio
                const timeline = document.querySelector('.history-timeline');
                timeline.insertBefore(timelineItem, timeline.firstChild);
                
                // Restablecer botón
                this.innerHTML = '<i class="fas fa-sync-alt"></i> Sincronizar Ahora';
                this.disabled = false;
            }, 2000);
        });
    }

    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Ocultar elementos inactivos con animación
    document.querySelectorAll('.module-inactive').forEach(item => {
        item.style.opacity = '0.6';
    });
    
    // Efecto de hover para las tarjetas de configuración
    document.querySelectorAll('.config-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.05)';
        });
    });
    
    // Animación del punto de estado
    const statusCircle = document.querySelector('.status-value.text-success i');
    if (statusCircle) {
        setInterval(() => {
            statusCircle.style.opacity = '0.4';
            setTimeout(() => {
                statusCircle.style.opacity = '1';
            }, 800);
        }, 2000);
    }
    
    // Validación de formatos específicos
    const ipRangeInput = document.getElementById('ipRange');
    if (ipRangeInput) {
        ipRangeInput.addEventListener('blur', function() {
            const value = this.value.trim();
            const ipv4Regex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\/([0-9]|[1-2][0-9]|3[0-2]))?$/;
            
            if (value && !ipv4Regex.test(value)) {
                this.classList.add('is-invalid');
                if (!this.nextElementSibling || !this.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Formato IPv4 CIDR no válido. Ejemplo: 192.168.1.0/24';
                    this.parentNode.insertBefore(feedback, this.nextSibling);
                }
            } else {
                this.classList.remove('is-invalid');
                if (this.nextElementSibling && this.nextElementSibling.classList.contains('invalid-feedback')) {
                    this.nextElementSibling.remove();
                }
            }
        });
    }
    
    // Gestionar visibilidad de módulos
    document.querySelectorAll('.form-check-input[id^="modulo"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const moduloId = this.id.replace('modulo', '').toLowerCase();
            
            // Actualizar tab relacionada si existe
            const tab = document.querySelector(`#${moduloId}-tab`);
            if (tab) {
                if (this.checked) {
                    tab.classList.remove('disabled');
                    tab.removeAttribute('disabled');
                } else {
                    tab.classList.add('disabled');
                    tab.setAttribute('disabled', 'disabled');
                    
                    // Si el tab deshabilitado está activo, cambiar a General
                    if (tab.classList.contains('active')) {
                        document.querySelector('#general-tab').click();
                    }
                }
            }
        });
    });
    
    // Botón para descargar respaldo
    const backupBtn = document.querySelector('.status-actions .btn-outline-primary');
    if (backupBtn) {
        backupBtn.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando...';
            this.disabled = true;
            
            // Simular descarga de respaldo
            setTimeout(() => {
                // Crear un enlace de descarga ficticio
                const link = document.createElement('a');
                link.href = 'data:text/plain;charset=utf-8,contenido_del_respaldo';
                link.download = `respaldo_zentraflow_${new Date().toISOString().slice(0,10)}.zip`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Restaurar botón
                this.innerHTML = '<i class="fas fa-download"></i> Descargar Respaldo';
                this.disabled = false;
            }, 1500);
        });
    }
    
    // Cambiar tab via hash en URL (para permitir enlaces directos a pestañas)
    function activateTabFromHash() {
        const hash = window.location.hash;
        if (hash) {
            const tabId = hash.replace('#', '');
            const tab = document.querySelector(`#${tabId}-tab`);
            if (tab && !tab.classList.contains('disabled')) {
                tab.click();
            }
        }
    }
    
    // Activar tab basado en hash al cargar
    activateTabFromHash();
    
    // Actualizar hash cuando cambia de tab
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const id = event.target.id.replace('-tab', '');
            history.replaceState(null, null, `#${id}`);
        });
    });
    
    // Detectar cambios sin guardar antes de salir de la página
    let formChanged = false;
    
    document.querySelectorAll('input, select, textarea').forEach(input => {
        input.addEventListener('change', function() {
            formChanged = true;
        });
    });
    
    window.addEventListener('beforeunload', function(e) {
        if (formChanged) {
            // Mensaje estándar que será mostrado por el navegador
            const message = '¿Está seguro de abandonar la página? Los cambios no guardados se perderán.';
            e.returnValue = message;
            return message;
        }
    });
    
    // Marcar formulario como guardado cuando se guarda
    saveConfigBtn.addEventListener('click', function() {
        formChanged = false;
    });
    
    footerSaveBtn.addEventListener('click', function() {
        formChanged = false;
    });
});