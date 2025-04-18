/**
 * dashboard.js - Funcionalidades para el dashboard de ingesta de correo
 * Versión mejorada con verificación de conexión
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard de ingesta inicializado");
    
    // Referencias a elementos DOM
    const toggleServicioBtn = document.getElementById('toggleServicio');
    const verifyConnectionBtn = document.getElementById('verifyConnection');
    const refreshChartBtn = document.getElementById('refreshChart');
    const refreshTrendsBtn = document.getElementById('refreshTrends');
    const refreshActivityBtn = document.getElementById('refreshActivity');
    const trendsChartEl = document.getElementById('trendsChart');
    const statusAlertEl = document.getElementById('statusAlert');
    const statusMessageEl = document.getElementById('statusMessage');
    
    // Referencias al modal de verificación
    let verificationModal;
    const verificationModalEl = document.getElementById('verificationModal');
    if (verificationModalEl) {
        verificationModal = new bootstrap.Modal(verificationModalEl, {
            backdrop: 'static'
        });
    } else {
        console.error("No se encontró el modal de verificación");
    }
    
    const verificationEmail = document.getElementById('verification-email');
    const verificationOAuth = document.getElementById('verification-oauth');
    const verificationFolder = document.getElementById('verification-folder');
    const verificationPermissions = document.getElementById('verification-permissions');
    const fixConnectionBtn = document.getElementById('fixConnectionBtn');
    
    // Gráfico de tendencias
    let trendsChart = null;
    
    // Inicializar gráfico de tendencias
    initTrendsChart();
    
    // Configurar actualización automática cada 5 minutos
    setInterval(updateDashboard, 5 * 60 * 1000); // 5 minutos
    
    // Event listeners
    if (toggleServicioBtn) {
        toggleServicioBtn.addEventListener('click', toggleServicio);
        console.log("Botón de toggle servicio configurado");
    } else {
        console.warn("No se encontró el botón de toggle servicio");
    }
    
    if (verifyConnectionBtn) {
        verifyConnectionBtn.addEventListener('click', function() {
            console.log("Verificando conexión...");
            verifyConnection();
        });
        console.log("Botón de verificar conexión configurado");
    } else {
        console.warn("No se encontró el botón de verificar conexión");
    }
    
    if (refreshChartBtn) {
        refreshChartBtn.addEventListener('click', function() {
            updateDashboard();
            animateRefreshIcon(this);
        });
    }
    
    if (refreshTrendsBtn) {
        refreshTrendsBtn.addEventListener('click', function() {
            updateTrendsChart();
            animateRefreshIcon(this);
        });
    }
    
    if (refreshActivityBtn) {
        refreshActivityBtn.addEventListener('click', function() {
            updateActivity();
            animateRefreshIcon(this);
        });
    }
    
    if (fixConnectionBtn) {
        fixConnectionBtn.addEventListener('click', function() {
            // Redirigir a la página de configuración de OAuth
            window.location.href = '/configuracion/#correo';
        });
    }
    
    /**
     * Inicializa el gráfico de tendencias diarias
     */
    function initTrendsChart() {
        if (!trendsChartEl) {
            console.warn("No se encontró el elemento del gráfico de tendencias");
            return;
        }
        
        try {
            // Intentar obtener los datos del atributo data-trends
            const trendsData = trendsChartEl.getAttribute('data-trends');
            let dailyTrends = [];
            
            if (trendsData) {
                dailyTrends = JSON.parse(trendsData);
                console.log("Datos de tendencias cargados:", dailyTrends.length, "registros");
            }
            
            if (dailyTrends.length === 0) {
                console.log("No hay datos de tendencias, cargando desde API...");
                fetchDailyTrends();
                return;
            }
            
            // Crear el gráfico con los datos disponibles
            createTrendsChart(trendsChartEl, dailyTrends);
            
        } catch (error) {
            console.error('Error al inicializar gráfico:', error);
            showStatusAlert('danger', 'Error al inicializar el gráfico de tendencias');
        }
    }
    
    /**
     * Crea el gráfico de tendencias con los datos proporcionados
     */
    function createTrendsChart(ctx, data) {
        if (trendsChart) {
            trendsChart.destroy();
        }
        
        const dates = data.map(item => item.fecha);
        const correosProcesados = data.map(item => item.correos_procesados);
        const glosas = data.map(item => item.glosas_extraidas);
        const pendientes = data.map(item => item.pendientes);
        const errores = data.map(item => item.errores);
        
        trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Correos Procesados',
                        data: correosProcesados,
                        borderColor: '#2bae66',
                        backgroundColor: 'rgba(43, 174, 102, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Glosas Extraídas',
                        data: glosas,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Pendientes',
                        data: pendientes,
                        borderColor: '#0387c2',
                        backgroundColor: 'rgba(3, 135, 194, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Errores',
                        data: errores,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    intersect: false
                }
            }
        });
        
        console.log("Gráfico de tendencias creado con éxito");
    }
    
    /**
     * Obtiene los datos de tendencias diarias mediante AJAX
     */
    function fetchDailyTrends() {
        fetch('/ingesta-correo/api/dashboard/')
            .then(response => response.json())
            .then(data => {
                if (data.daily_trends && data.daily_trends.length > 0) {
                    if (trendsChartEl) {
                        createTrendsChart(trendsChartEl, data.daily_trends);
                    }
                }
            })
            .catch(error => {
                console.error('Error al obtener tendencias:', error);
                showStatusAlert('danger', 'Error al obtener datos de tendencias');
            });
    }
    
    /**
     * Función para activar/desactivar el servicio de ingesta
     */
    function toggleServicio() {
        // Obtener el CSRF token
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Cambiar estado visual del botón
        toggleServicioBtn.disabled = true;
        const originalText = toggleServicioBtn.innerHTML;
        toggleServicioBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        
        // Enviar solicitud al servidor
        fetch('/ingesta-correo/api/toggle-servicio/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar el estado del botón según la respuesta
                if (data.active) {
                    toggleServicioBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Detener Servicio';
                    toggleServicioBtn.classList.remove('btn-success');
                    toggleServicioBtn.classList.add('btn-danger');
                    
                    // Actualizar el estado del servicio en la UI
                    const serviceStatusEl = document.getElementById('service-status');
                    if (serviceStatusEl) {
                        serviceStatusEl.innerHTML = 
                            '<span class="text-success"><i class="fas fa-circle"></i> Activo</span>';
                    }
                } else {
                    toggleServicioBtn.innerHTML = '<i class="fas fa-play-circle"></i> Iniciar Servicio';
                    toggleServicioBtn.classList.remove('btn-danger');
                    toggleServicioBtn.classList.add('btn-success');
                    
                    // Actualizar el estado del servicio en la UI
                    const serviceStatusEl = document.getElementById('service-status');
                    if (serviceStatusEl) {
                        serviceStatusEl.innerHTML = 
                            '<span class="text-secondary"><i class="fas fa-circle"></i> Inactivo</span>';
                    }
                }
                
                // Mostrar mensaje de éxito
                showStatusAlert('success', data.message);
                
                // Actualizar todo el dashboard
                setTimeout(updateDashboard, 500);
            } else {
                // Restaurar botón original en caso de error
                toggleServicioBtn.innerHTML = originalText;
                showStatusAlert('danger', data.message || 'Error al cambiar el estado del servicio');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toggleServicioBtn.innerHTML = originalText;
            showStatusAlert('danger', 'Error de conexión al servidor');
        })
        .finally(() => {
            toggleServicioBtn.disabled = false;
        });
    }
    
    /**
     * Función para verificar la conexión OAuth
     */
    function verifyConnection() {
        console.log("Verificando conexión OAuth...");
        
        // Verificar que el modal existe
        if (!verificationModal) {
            console.error("No se encontró el modal de verificación");
            showStatusAlert('danger', 'Error al abrir el modal de verificación');
            return;
        }
        
        // Mostrar modal de verificación
        verificationModal.show();
        
        // Resetear el estado de las verificaciones
        if (verificationEmail) verificationEmail.textContent = '-';
        if (verificationOAuth) verificationOAuth.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        if (verificationFolder) verificationFolder.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        if (verificationPermissions) verificationPermissions.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        
        // Ocultar botón de arreglar
        if (fixConnectionBtn) fixConnectionBtn.style.display = 'none';
        
        // Obtener el CSRF token
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        if (!csrfToken) {
            console.error("No se encontró el token CSRF");
            showStatusAlert('danger', 'Error: No se encontró el token CSRF');
            return;
        }
        
        // Enviar solicitud al servidor
        fetch('/ingesta-correo/api/verify-connection/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("Respuesta de verificación recibida:", data);
            
            // Actualizar información de email
            if (verificationEmail) {
                if (data.status.email_address) {
                    verificationEmail.textContent = data.status.email_address;
                } else {
                    verificationEmail.textContent = 'No configurado';
                }
            }
            
            // Actualizar estado OAuth
            if (verificationOAuth) {
                if (data.status.oauth_authorized) {
                    if (data.status.oauth_token_valid) {
                        verificationOAuth.innerHTML = '<i class="fas fa-check-circle text-success"></i> Autorizado';
                    } else {
                        verificationOAuth.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> Token expirado';
                    }
                } else {
                    verificationOAuth.innerHTML = '<i class="fas fa-times-circle text-danger"></i> No autorizado';
                }
            }
            
            // Actualizar acceso a carpeta
            if (verificationFolder) {
                if (data.status.folder_accessible) {
                    verificationFolder.innerHTML = '<i class="fas fa-check-circle text-success"></i> Accesible';
                } else {
                    verificationFolder.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Error de acceso';
                }
            }
            
            // Actualizar permisos de lectura
            if (verificationPermissions) {
                if (data.status.read_permissions) {
                    verificationPermissions.innerHTML = '<i class="fas fa-check-circle text-success"></i> Correctos';
                } else {
                    verificationPermissions.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Insuficientes';
                }
            }
            
            // Actualizar mensaje global y mostrar/ocultar botón de arreglo
            const modalBody = document.querySelector('#verificationModal .verification-message');
            if (modalBody) {
                if (data.success) {
                    modalBody.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i> ' + data.message;
                    if (fixConnectionBtn) fixConnectionBtn.style.display = 'none';
                } else {
                    modalBody.innerHTML = '<i class="fas fa-exclamation-triangle text-warning me-2"></i> ' + data.message;
                    if (fixConnectionBtn) fixConnectionBtn.style.display = 'block';
                }
            }
            
            // Actualizar icono principal
            const iconElement = document.querySelector('#verificationModal .verification-icon i');
            if (iconElement) {
                iconElement.className = data.success ? 
                    'fas fa-check-circle text-success' : 
                    'fas fa-exclamation-triangle text-warning';
            }
            
            // Actualizar dashboard con la información más reciente
            updateDashboard();
        })
        .catch(error => {
            console.error('Error en verificación de conexión:', error);
            
            // Actualizar mensaje de error
            const modalBody = document.querySelector('#verificationModal .verification-message');
            if (modalBody) {
                modalBody.innerHTML = '<i class="fas fa-times-circle text-danger me-2"></i> Error de conexión al servidor';
            }
            
            // Mostrar botón de arreglo
            if (fixConnectionBtn) fixConnectionBtn.style.display = 'block';
            
            // Actualizar estados a fallido
            if (verificationOAuth) verificationOAuth.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Error';
            if (verificationFolder) verificationFolder.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Error';
            if (verificationPermissions) verificationPermissions.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Error';
            
            // Actualizar icono principal
            const iconElement = document.querySelector('#verificationModal .verification-icon i');
            if (iconElement) {
                iconElement.className = 'fas fa-times-circle text-danger';
            }
            
            // Mostrar mensaje de error en la UI
            showStatusAlert('danger', 'Error al verificar la conexión');
        });
    }
    
    /**
     * Actualiza el gráfico de tendencias
     */
    function updateTrendsChart() {
        fetch('/ingesta-correo/api/dashboard/')
            .then(response => response.json())
            .then(data => {
                if (data.daily_trends) {
                    if (trendsChartEl) {
                        createTrendsChart(trendsChartEl, data.daily_trends);
                    }
                }
            })
            .catch(error => {
                console.error('Error al actualizar gráfico:', error);
                showStatusAlert('danger', 'Error al actualizar el gráfico');
            });
    }
    
    /**
     * Actualiza la lista de actividad reciente
     */
    function updateActivity() {
        // Esta función requeriría un endpoint adicional para recuperar solo la actividad reciente
        // Por ahora, simplemente recargaremos la página para obtener la actividad más reciente
        fetch('/ingesta-correo/api/dashboard/')
            .then(response => response.json())
            .then(data => {
                // Como no tenemos la actividad reciente en la respuesta de la API actual,
                // mostraremos un mensaje sugiriendo recargar la página
                showStatusAlert('info', 'Para ver la actividad más reciente, recargue la página');
            })
            .catch(error => {
                console.error('Error al actualizar actividad:', error);
                showStatusAlert('danger', 'Error al obtener la actividad reciente');
            });
    }
    
    /**
     * Actualiza todas las métricas del dashboard
     */
    function updateDashboard() {
        fetch('/ingesta-correo/api/dashboard/')
            .then(response => response.json())
            .then(data => {
                // Actualizar métricas de 24h
                if (data.metrics_24h) {
                    updateMetrics(data.metrics_24h);
                }
                
                // Actualizar gráfico de tendencias
                if (data.daily_trends) {
                    if (trendsChartEl) {
                        createTrendsChart(trendsChartEl, data.daily_trends);
                    }
                }
                
                // Actualizar estado del sistema
                if (data.system_status) {
                    updateSystemStatus(data.system_status);
                }
            })
            .catch(error => {
                console.error('Error al actualizar dashboard:', error);
            });
    }
    
    /**
     * Actualiza los valores de las métricas en la UI
     */
    function updateMetrics(metrics) {
        const corProcEl = document.getElementById('correos-procesados');
        const glosaExtEl = document.getElementById('glosas-extraidas');
        const pendEl = document.getElementById('pendientes');
        const errEl = document.getElementById('errores');
        
        if (corProcEl) corProcEl.textContent = metrics.correos_procesados;
        if (glosaExtEl) glosaExtEl.textContent = metrics.glosas_extraidas;
        if (pendEl) pendEl.textContent = metrics.pendientes;
        if (errEl) errEl.textContent = metrics.errores;
    }
    
    /**
     * Actualiza el estado del sistema en la UI
     */
    function updateSystemStatus(status) {
        // Actualizar el botón de toggle servicio
        if (toggleServicioBtn) {
            if (status.servicio_activo) {
                toggleServicioBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Detener Servicio';
                toggleServicioBtn.classList.remove('btn-success');
                toggleServicioBtn.classList.add('btn-danger');
                
                const serviceStatusEl = document.getElementById('service-status');
                if (serviceStatusEl) {
                    serviceStatusEl.innerHTML = 
                        '<span class="text-success"><i class="fas fa-circle"></i> Activo</span>';
                }
            } else {
                toggleServicioBtn.innerHTML = '<i class="fas fa-play-circle"></i> Iniciar Servicio';
                toggleServicioBtn.classList.remove('btn-danger');
                toggleServicioBtn.classList.add('btn-success');
                
                const serviceStatusEl = document.getElementById('service-status');
                if (serviceStatusEl) {
                    serviceStatusEl.innerHTML = 
                        '<span class="text-secondary"><i class="fas fa-circle"></i> Inactivo</span>';
                }
            }
            
            // Deshabilitar el botón si OAuth no está configurado
            toggleServicioBtn.disabled = !status.oauth_configured;
        }
        
        // Actualizar estado de OAuth
        const oauthStatusEl = document.getElementById('oauth-status');
        if (oauthStatusEl) {
            if (status.oauth_authorized) {
                oauthStatusEl.innerHTML = 
                    '<span class="text-success"><i class="fas fa-circle"></i> Autorizado</span>';
            } else {
                oauthStatusEl.innerHTML = 
                    '<span class="text-danger"><i class="fas fa-circle"></i> No autorizado</span>';
            }
        }
        
        // Actualizar cuenta de correo
        const emailAccountEl = document.getElementById('email-account');
        if (emailAccountEl && status.email_address) {
            emailAccountEl.textContent = status.email_address;
        }
        
        // Actualizar última verificación
        const lastCheckEl = document.getElementById('last-check');
        if (lastCheckEl && status.ultima_verificacion) {
            const date = new Date(status.ultima_verificacion);
            lastCheckEl.textContent = formatDate(date);
        }
        
        // Actualizar último correo procesado
        const lastProcessedEl = document.getElementById('last-processed');
        if (lastProcessedEl && status.ultimo_correo_procesado) {
            const date = new Date(status.ultimo_correo_procesado);
            lastProcessedEl.textContent = formatDate(date);
        }
        
        // Actualizar errores recientes
        const recentErrorsEl = document.getElementById('recent-errors');
        if (recentErrorsEl) {
            if (status.errores_recientes > 0) {
                recentErrorsEl.innerHTML = `<span class="text-danger">${status.errores_recientes}</span>`;
            } else {
                recentErrorsEl.innerHTML = `<span class="text-success">0</span>`;
            }
        }
        
        // Actualizar reintentos
        const retryCountEl = document.getElementById('retry-count');
        if (retryCountEl && status.reintentos !== undefined) {
            retryCountEl.textContent = status.reintentos;
        }
    }
    
    /**
     * Anima el ícono de refrescar
     */
    function animateRefreshIcon(button) {
        if (!button) return;
        
        const icon = button.querySelector('i');
        if (icon) {
            // Guardar clase original
            const originalClass = icon.className;
            
            // Cambiar a ícono de carga
            icon.className = 'fas fa-spinner fa-spin';
            
            // Restaurar después de 1 segundo
            setTimeout(() => {
                icon.className = originalClass;
            }, 1000);
        }
    }
    
    /**
     * Muestra una alerta de estado
     */
    function showStatusAlert(type, message) {
        if (!statusAlertEl || !statusMessageEl) {
            console.warn("No se encontraron elementos de alerta");
            return;
        }
        
        // Configurar el tipo de alerta
        statusAlertEl.className = '';
        statusAlertEl.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show', 'mb-4');
        
        // Configurar el ícono según el tipo
        const iconElement = statusAlertEl.querySelector('.alert-icon i');
        if (iconElement) {
            iconElement.className = '';
            if (type === 'success') {
                iconElement.classList.add('fas', 'fa-check-circle');
            } else if (type === 'danger') {
                iconElement.classList.add('fas', 'fa-exclamation-circle');
            } else if (type === 'warning') {
                iconElement.classList.add('fas', 'fa-exclamation-triangle');
            } else {
                iconElement.classList.add('fas', 'fa-info-circle');
            }
        }
        
        // Establecer el mensaje
        statusMessageEl.textContent = message;
        
        // Mostrar la alerta
        statusAlertEl.style.display = 'flex';
        
        // Programar ocultación automática después de 5 segundos
        setTimeout(() => {
            if (statusAlertEl) {
                try {
                    const alert = new bootstrap.Alert(statusAlertEl);
                    alert.close();
                } catch (error) {
                    console.warn("Error al cerrar alerta:", error);
                    // Alternativa si bootstrap.Alert no está disponible
                    statusAlertEl.style.display = 'none';
                }
            }
        }, 5000);
    }
    
    /**
     * Formatea una fecha para mostrarla en la interfaz
     */
    function formatDate(date) {
        if (!date) return 'Nunca';
        
        try {
            const options = {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            };
            
            return date.toLocaleDateString('es-ES', options);
        } catch (error) {
            console.warn("Error al formatear fecha:", error);
            return date.toString();
        }
    }
});