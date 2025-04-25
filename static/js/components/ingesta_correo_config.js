/**
 * ingesta_correo_config.js - Maneja la configuración de ingesta de correo
 * Este archivo se encarga de guardar y validar la configuración de correo para la ingesta
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Script de configuración de ingesta de correo iniciado");
    
    // Obtener referencias a elementos del DOM
    const saveEmailConfigBtn = document.getElementById('saveEmailConfigBtn');
    const ingestaEnabledSwitch = document.getElementById('ingestaEnabled');
    const testConnectionBtn = document.getElementById('testConnectionBtn');
    const connectionStatus = document.getElementById('connectionStatus');
    const syncNowBtn = document.getElementById('syncNowBtn');
    
    // Inputs del formulario
    const emailMonitor = document.getElementById('emailMonitor');
    const protocolType = document.getElementById('protocolType');
    const serverHost = document.getElementById('serverHost');
    const serverPort = document.getElementById('serverPort');
    const emailPassword = document.getElementById('emailPassword');
    const folderMonitor = document.getElementById('folderMonitor');
    const checkInterval = document.getElementById('checkInterval');
    const useSSL = document.getElementById('useSSL');
    const markAsRead = document.getElementById('markAsRead');
    
    // Toggle de contraseña
    const passwordToggle = document.querySelector('.toggle-password');
    
    // Obtener CSRF token
    const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenElement) {
        console.error("Error: CSRF token no encontrado");
        return;
    }
    const csrfToken = csrfTokenElement.value;
    
    // Función para mostrar mensajes
    function showMessage(type, message) {
        const errorAlert = document.getElementById('errorAlert');
        const successAlert = document.getElementById('successAlert');
        
        // Si no existen los elementos de alerta, usar console.log
        if (!errorAlert && !successAlert) {
            console.log(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        const alert = type === 'success' ? successAlert : errorAlert;
        if (!alert) {
            console.log(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        const messageContainer = alert.querySelector('.alert-message');
        if (!messageContainer) {
            console.log(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        const strongElement = messageContainer.querySelector('strong');
        const strongText = strongElement ? strongElement.textContent : (type === 'success' ? '¡Éxito!' : 'Error:');
        messageContainer.innerHTML = `<strong>${strongText}</strong> ${message}`;
        alert.classList.add('show');
        
        // Cerrar automáticamente después de 5 segundos
        setTimeout(() => {
            alert.classList.remove('show');
        }, 5000);
    }
    
    // Función para mostrar el estado de conexión
    function updateConnectionStatus(status, message) {
        if (!connectionStatus) return;
        
        connectionStatus.innerHTML = '';
        
        if (status === 'loading') {
            connectionStatus.classList.remove('text-success', 'text-danger');
            connectionStatus.classList.add('text-warning');
            connectionStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Probando conexión...';
        } else if (status === 'success') {
            connectionStatus.classList.remove('text-warning', 'text-danger');
            connectionStatus.classList.add('text-success');
            connectionStatus.innerHTML = '<i class="fas fa-check-circle"></i> Conexión exitosa';
        } else if (status === 'error') {
            connectionStatus.classList.remove('text-warning', 'text-success');
            connectionStatus.classList.add('text-danger');
            connectionStatus.innerHTML = '<i class="fas fa-times-circle"></i> Error de conexión';
            if (message) {
                connectionStatus.innerHTML += `: ${message}`;
            }
        }
    }
    
    // Función para validar el formulario
    function validateForm() {
        let isValid = true;
        let errorMessage = '';
        
        // Validar correo
        if (!emailMonitor || !emailMonitor.value.trim()) {
            isValid = false;
            errorMessage = 'El correo electrónico es obligatorio';
            emailMonitor?.classList.add('is-invalid');
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailMonitor.value.trim())) {
            isValid = false;
            errorMessage = 'El correo electrónico no es válido';
            emailMonitor?.classList.add('is-invalid');
        } else {
            emailMonitor?.classList.remove('is-invalid');
        }
        
        // Validar servidor
        if (!serverHost || !serverHost.value.trim()) {
            isValid = false;
            errorMessage = errorMessage || 'El servidor de correo es obligatorio';
            serverHost?.classList.add('is-invalid');
        } else {
            serverHost?.classList.remove('is-invalid');
        }
        
        // Validar puerto
        if (!serverPort || !serverPort.value.trim()) {
            isValid = false;
            errorMessage = errorMessage || 'El puerto es obligatorio';
            serverPort?.classList.add('is-invalid');
        } else if (isNaN(serverPort.value) || serverPort.value < 1 || serverPort.value > 65535) {
            isValid = false;
            errorMessage = errorMessage || 'El puerto debe ser un número entre 1 y 65535';
            serverPort?.classList.add('is-invalid');
        } else {
            serverPort?.classList.remove('is-invalid');
        }
        
        // Validar contraseña
        if (!emailPassword || !emailPassword.value.trim()) {
            isValid = false;
            errorMessage = errorMessage || 'La contraseña es obligatoria';
            emailPassword?.classList.add('is-invalid');
        } else {
            emailPassword?.classList.remove('is-invalid');
        }
        
        // Validar intervalo
        if (!checkInterval || !checkInterval.value.trim()) {
            isValid = false;
            errorMessage = errorMessage || 'El intervalo de verificación es obligatorio';
            checkInterval?.classList.add('is-invalid');
        } else if (isNaN(checkInterval.value) || checkInterval.value < 1 || checkInterval.value > 60) {
            isValid = false;
            errorMessage = errorMessage || 'El intervalo debe ser un número entre 1 y 60 minutos';
            checkInterval?.classList.add('is-invalid');
        } else {
            checkInterval?.classList.remove('is-invalid');
        }
        
        return { isValid, errorMessage };
    }
    
    // Función para actualizar el puerto según el protocolo y SSL
    function updateDefaultPort() {
        if (!protocolType || !serverPort || !useSSL) return;
        
        // Solo actualizar si el campo está vacío o tiene el valor por defecto anterior
        const defaultImapSSL = 993;
        const defaultImapNoSSL = 143;
        const defaultPop3SSL = 995;
        const defaultPop3NoSSL = 110;
        
        // Determinar el puerto por defecto según las selecciones actuales
        let defaultPort;
        if (protocolType.value === 'imap') {
            defaultPort = useSSL.checked ? defaultImapSSL : defaultImapNoSSL;
        } else { // pop3
            defaultPort = useSSL.checked ? defaultPop3SSL : defaultPop3NoSSL;
        }
        
        // Verificar si el valor actual corresponde a alguno de los valores por defecto
        const currentPort = parseInt(serverPort.value);
        const isDefaultPort = [defaultImapSSL, defaultImapNoSSL, defaultPop3SSL, defaultPop3NoSSL].includes(currentPort);
        
        // Actualizar solo si está vacío o es un puerto por defecto
        if (!serverPort.value.trim() || isDefaultPort) {
            serverPort.value = defaultPort;
        }
    }
    
    // Función para guardar la configuración
    function saveEmailConfig(button) {
        console.log("Guardando configuración de correo...");
        
        // Validar formulario
        const { isValid, errorMessage } = validateForm();
        if (!isValid) {
            showMessage('error', errorMessage);
            return;
        }
        
        // Mostrar estado de carga
        button.disabled = true;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        
        try {
            // Preparar datos
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            formData.append('action', 'save_email_config');
            formData.append('update_connection_status', 'true'); // Añadir flag para actualizar estado
            
            // Añadir campos del formulario
            formData.append('email_address', emailMonitor.value);
            formData.append('protocol', protocolType.value);
            formData.append('server_host', serverHost.value);
            formData.append('server_port', serverPort.value);
            formData.append('username', emailMonitor.value); // Por defecto, usar el email como username
            formData.append('password', emailPassword.value);
            formData.append('use_ssl', useSSL.checked ? 'true' : 'false');
            formData.append('folder_to_monitor', folderMonitor.value);
            formData.append('check_interval', checkInterval.value);
            formData.append('mark_as_read', markAsRead.checked ? 'true' : 'false');
            formData.append('ingesta_enabled', ingestaEnabledSwitch.checked ? 'true' : 'false');
            
            // Realizar petición
            fetch('/api/email-config/', {
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
                    showMessage('success', data.message || 'Configuración de correo guardada correctamente');
                    
                    // Si se guardó correctamente, probar la conexión automáticamente
                    if (data.connection_status) {
                        // Si la API devolvió el estado de conexión, actualizarlo
                        if (data.connection_status === 'conectado') {
                            updateConnectionStatus('success');
                        } else if (data.connection_status === 'error') {
                            updateConnectionStatus('error', data.connection_error);
                        }
                    } else {
                        // Si no devuelve estado, hacer prueba separada
                        console.log("Probando conexión después de guardar configuración...");
                        
                        // Preparar datos para prueba de conexión
                        const testFormData = new FormData();
                        testFormData.append('csrfmiddlewaretoken', csrfToken);
                        testFormData.append('action', 'test_connection');
                        testFormData.append('email_address', emailMonitor.value);
                        testFormData.append('protocol', protocolType.value);
                        testFormData.append('server_host', serverHost.value);
                        testFormData.append('server_port', serverPort.value);
                        testFormData.append('username', emailMonitor.value);
                        testFormData.append('password', emailPassword.value);
                        testFormData.append('use_ssl', useSSL.checked ? 'true' : 'false');
                        testFormData.append('folder_to_monitor', folderMonitor.value);
                        
                        // Realizar prueba post-guardado
                        fetch('/api/email-config/test/', {
                            method: 'POST',
                            body: testFormData,
                            headers: {
                                'X-CSRFToken': csrfToken
                            }
                        })
                        .then(response => response.json())
                        .then(testData => {
                            console.log("Resultado de prueba post-guardado:", testData);
                            if (testData.success) {
                                updateConnectionStatus('success');
                            } else {
                                updateConnectionStatus('error', testData.error || testData.message);
                            }
                        })
                        .catch(error => {
                            console.error("Error en prueba post-guardado:", error);
                        });
                    }
                    
                    // Recargar la configuración para actualizar el estado
                    loadInitialConfig();
                } else {
                    showMessage('error', data.message || 'Error al guardar la configuración de correo');
                }
                
                // Restaurar botón
                button.disabled = false;
                button.innerHTML = originalHTML;
            })
            .catch(error => {
                console.error("Error al guardar configuración:", error);
                showMessage('error', 'Error al guardar configuración: ' + error.message);
                
                // Restaurar botón en caso de error
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
    
    // Función para probar la conexión al servidor de correo
    function testConnection() {
        console.log("Probando conexión al servidor de correo...");
        
        // Validar campos mínimos necesarios
        if (!serverHost || !serverHost.value.trim() || 
            !serverPort || !serverPort.value.trim() || 
            !emailMonitor || !emailMonitor.value.trim() || 
            !emailPassword || !emailPassword.value.trim()) {
            
            showMessage('error', 'Complete todos los campos requeridos para probar la conexión');
            return;
        }
        
        // Actualizar estado de conexión
        updateConnectionStatus('loading');
        
        // Deshabilitar botón
        testConnectionBtn.disabled = true;
        const originalHTML = testConnectionBtn.innerHTML;
        testConnectionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Probando...';
        
        // Preparar datos
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('action', 'test_connection');
        formData.append('email_address', emailMonitor.value);
        formData.append('protocol', protocolType.value);
        formData.append('server_host', serverHost.value);
        formData.append('server_port', serverPort.value);
        formData.append('username', emailMonitor.value);
        formData.append('password', emailPassword.value);
        formData.append('use_ssl', useSSL.checked ? 'true' : 'false');
        formData.append('folder_to_monitor', folderMonitor.value);
        
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
            console.log("Respuesta de prueba de conexión:", data);
            
            if (data.success) {
                updateConnectionStatus('success');
                showMessage('success', 'Conexión exitosa al servidor de correo');
            } else {
                updateConnectionStatus('error', data.error);
                showMessage('error', data.message || 'Error al conectar con el servidor de correo');
            }
        })
        .catch(error => {
            console.error("Error al probar conexión:", error);
            updateConnectionStatus('error', error.message);
            showMessage('error', 'Error al probar la conexión: ' + error.message);
        })
        .finally(() => {
            // Restaurar botón
            testConnectionBtn.disabled = false;
            testConnectionBtn.innerHTML = originalHTML;
        });
    }
    
    // Función para sincronizar ahora (forzar una verificación inmediata)
    function syncNow() {
        console.log("Iniciando sincronización manual...");
        
        // Deshabilitar botón
        syncNowBtn.disabled = true;
        const originalHTML = syncNowBtn.innerHTML;
        syncNowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sincronizando...';
        
        // Preparar datos
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('action', 'sync_now');
        
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
            console.log("Respuesta de sincronización:", data);
            
            if (data.success) {
                showMessage('success', data.message || 'Sincronización iniciada correctamente');
            } else {
                showMessage('error', data.message || 'Error al iniciar la sincronización');
            }
        })
        .catch(error => {
            console.error("Error al sincronizar:", error);
            showMessage('error', 'Error al sincronizar: ' + error.message);
        })
        .finally(() => {
            // Restaurar botón
            syncNowBtn.disabled = false;
            syncNowBtn.innerHTML = originalHTML;
        });
    }
    
    // Event Listeners
    
    // 1. Guardar configuración de email
    if (saveEmailConfigBtn) {
        saveEmailConfigBtn.addEventListener('click', function(e) {
            e.preventDefault();
            saveEmailConfig(this);
        });
    }
    
    // 2. Probar conexión
    if (testConnectionBtn) {
        testConnectionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            testConnection();
        });
    }
    
    // 3. Sincronizar ahora
    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', function(e) {
            e.preventDefault();
            syncNow();
        });
    }
    
    // 4. Toggle de contraseña
    if (passwordToggle && emailPassword) {
        passwordToggle.addEventListener('click', function() {
            const type = emailPassword.getAttribute('type') === 'password' ? 'text' : 'password';
            emailPassword.setAttribute('type', type);
            
            // Cambiar icono
            const icon = this.querySelector('i');
            if (icon) {
                if (type === 'text') {
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            }
        });
    }
    
    // 5. Cambio de protocolo o SSL para actualizar el puerto por defecto
    if (protocolType) {
        protocolType.addEventListener('change', updateDefaultPort);
    }
    
    if (useSSL) {
        useSSL.addEventListener('change', updateDefaultPort);
    }
    
    // 6. Cargar valores iniciales del servidor
    function loadInitialConfig() {
        // Intentar cargar configuración existente mediante API
        fetch('/api/email-config/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar configuración');
            }
            return response.json();
        })
        .then(data => {
            console.log("Configuración de correo cargada:", data);
            
            // Llenar formulario con datos existentes
            if (data.email_address && emailMonitor) emailMonitor.value = data.email_address;
            if (data.protocol && protocolType) protocolType.value = data.protocol;
            if (data.server_host && serverHost) serverHost.value = data.server_host;
            if (data.server_port && serverPort) serverPort.value = data.server_port;
            if (data.folder_to_monitor && folderMonitor) {
                // Si la carpeta existe en las opciones, seleccionarla
                const folderExists = Array.from(folderMonitor.options).some(option => option.value === data.folder_to_monitor);
                if (folderExists) {
                    folderMonitor.value = data.folder_to_monitor;
                } else if (data.folder_to_monitor) {
                    // Si no existe, crear la opción
                    const newOption = document.createElement('option');
                    newOption.value = data.folder_to_monitor;
                    newOption.textContent = data.folder_to_monitor;
                    folderMonitor.appendChild(newOption);
                    folderMonitor.value = data.folder_to_monitor;
                }
            }
            if (data.check_interval && checkInterval) checkInterval.value = data.check_interval;
            if (useSSL) useSSL.checked = data.use_ssl;
            if (markAsRead) markAsRead.checked = data.mark_as_read;
            if (ingestaEnabledSwitch) ingestaEnabledSwitch.checked = data.ingesta_enabled;
            
            // No llenar contraseña por seguridad
            if (emailPassword) emailPassword.value = ''; // La contraseña se debe ingresar nuevamente
            
            // Actualizar estado de conexión
            if (data.connection_status === 'conectado') {
                updateConnectionStatus('success');
            } else if (data.connection_status === 'error') {
                updateConnectionStatus('error', data.connection_error || 'Error de conexión');
            } else if (data.connection_status === 'no_verificado') {
                // Si nunca se ha verificado, mostrar un mensaje indicando que se necesita verificar
                if (connectionStatus) {
                    connectionStatus.classList.remove('text-success', 'text-danger', 'text-warning');
                    connectionStatus.classList.add('text-secondary');
                    connectionStatus.innerHTML = '<i class="fas fa-question-circle"></i> Conexión no verificada';
                }
            }
        })
        .catch(error => {
            console.error("Error al cargar configuración:", error);
            // No mostrar mensaje de error, simplemente dejar el formulario vacío
        });
    }
    
    // Iniciar carga de configuración al cargar la página
    loadInitialConfig();
    
    console.log("Inicialización de configuración de ingesta de correo completada");
}); 