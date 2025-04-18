/**
 * dashboard.js - Funcionalidades para el dashboard de ingesta de correo
 */

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos DOM
    const toggleServicioBtn = document.getElementById('toggleServicio');
    const refreshChartBtn = document.getElementById('refreshChart');
    const refreshActivityBtn = document.getElementById('refreshActivity');
    const trendsChartEl = document.getElementById('trendsChart');
    
    // Gráfico de tendencias
    let trendsChart = null;
    
    // Inicializar gráfico de tendencias
    initTrendsChart();
    
    // Configurar actualización automática cada 5 minutos
    setInterval(updateDashboard, 5 * 60 * 1000); // 5 minutos
    
    // Event listeners
    if (toggleServicioBtn) {
        toggleServicioBtn.addEventListener('click', toggleServicio);
    }
    
    if (refreshChartBtn) {
        refreshChartBtn.addEventListener('click', function() {
            refreshChart(this);
        });
    }
    
    if (refreshActivityBtn) {
        refreshActivityBtn.addEventListener('click', function() {
            refreshActivity(this);
        });
    }
    
    /**
     * Inicializa el gráfico de tendencias diarias
     */
    function initTrendsChart() {
        if (!trendsChartEl) return;
        
        // Obtener los datos del backend (pasados al template)
        let dailyTrends = [];
        try {
            // Intentar obtener los datos del atributo data-trends
            const trendsData = trendsChartEl.getAttribute('data-trends');
            if (trendsData) {
                dailyTrends = JSON.parse(trendsData);
            } else {
                // Si no hay datos en el atributo, intentar obtenerlos de la variable global
                const trendsJson = document.getElementById('daily_trends_json');
                if (trendsJson) {
                    dailyTrends = JSON.parse(trendsJson.textContent || '[]');
                }
            }
        } catch (error) {
            console.error('Error al parsear datos de tendencias:', error);
            // Intentar obtener los datos mediante una petición AJAX
            fetchDailyTrends();
            return;
        }
        
        if (dailyTrends.length === 0) {
            fetchDailyTrends();
            return;
        }
        
        // Crear el gráfico con los datos disponibles
        createTrendsChart(trendsChartEl, dailyTrends);
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
                } else {
                    toggleServicioBtn.innerHTML = '<i class="fas fa-play-circle"></i> Iniciar Servicio';
                    toggleServicioBtn.classList.remove('btn-danger');
                    toggleServicioBtn.classList.add('btn-success');
                }
                
                // Mostrar mensaje de éxito
                showNotification('success', data.message);
                
                // Actualizar todo el dashboard
                setTimeout(updateDashboard, 500);
            } else {
                // Restaurar botón original en caso de error
                toggleServicioBtn.innerHTML = originalText;
                showNotification('error', data.message || 'Error al cambiar el estado del servicio');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toggleServicioBtn.innerHTML = originalText;
            showNotification('error', 'Error de conexión al servidor');
        })
        .finally(() => {
            toggleServicioBtn.disabled = false;
        });
    }
    
    /**
     * Actualiza el gráfico de tendencias
     */
    function refreshChart(button) {
        if (!button) return;
        
        // Añadir animación de rotación al ícono
        const icon = button.querySelector('i');
        if (icon) {
            icon.classList.add('refreshing');
        }
        
        // Obtener datos actualizados
        fetch('/ingesta-correo/api/dashboard/')
            .then(response => response.json())
            .then(data => {
                if (data.daily_trends) {
                    if (trendsChartEl) {
                        createTrendsChart(trendsChartEl, data.daily_trends);
                    }
                }
                
                // Actualizar las métricas de 24h
                if (data.metrics_24h) {
                    updateMetrics(data.metrics_24h);
                }
            })
            .catch(error => {
                console.error('Error al actualizar gráfico:', error);
                showNotification('error', 'Error al actualizar el gráfico');
            })
            .finally(() => {
                // Quitar animación
                if (icon) {
                    setTimeout(() => {
                        icon.classList.remove('refreshing');
                    }, 500);
                }
            });
    }
    
    /**
     * Actualiza la lista de actividad reciente
     */
    function refreshActivity(button) {
        if (!button) return;
        
        // Añadir animación de rotación al ícono
        const icon = button.querySelector('i');
        if (icon) {
            icon.classList.add('refreshing');
        }
        
        // Aquí iría la lógica para actualizar la actividad reciente mediante AJAX
        // Por simplicidad, mostraremos un mensaje de recarga necesaria
        showNotification('info', 'Para actualizar la actividad reciente es necesario recargar la página');
        
        // Quitar animación después de un tiempo
        setTimeout(() => {
            if (icon) {
                icon.classList.remove('refreshing');
            }
        }, 1000);
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
            } else {
                toggleServicioBtn.innerHTML = '<i class="fas fa-play-circle"></i> Iniciar Servicio';
                toggleServicioBtn.classList.remove('btn-danger');
                toggleServicioBtn.classList.add('btn-success');
            }
        }
        
        // Actualizar indicadores de estado
        // Aquí se actualizarían otros elementos de la UI según el estado del sistema
    }
    
    /**
     * Muestra una notificación temporal
     */
    function showNotification(type, message) {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.innerHTML = `
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Añadir al DOM
        document.body.appendChild(notification);
        
        // Eliminar después de 5 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
});