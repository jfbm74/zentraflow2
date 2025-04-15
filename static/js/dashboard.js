/**
 * dashboard.js - Funcionalidades específicas de la página de dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Botón Ir a Bandeja de Glosas
    const btnBandeja = document.querySelector('.btn-action');
    if (btnBandeja) {
        btnBandeja.addEventListener('click', function() {
            // Redireccionar a la bandeja de glosas
            window.location.href = '/bandeja-glosas/';
        });
    }
    
    // Botón de filtro por semana
    const btnWeek = document.querySelector('.btn-week');
    if (btnWeek) {
        btnWeek.addEventListener('click', function() {
            // Aquí iría la lógica para mostrar un dropdown con filtros de fecha
            // Por simplicidad, solo mostraremos un ejemplo
            alert('Filtro por fecha: Esta funcionalidad estará disponible próximamente');
        });
    }
    
    // Botón de exportar
    const btnExport = document.querySelector('.btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', function() {
            // Aquí iría la lógica para exportar los datos
            alert('Exportar: Esta funcionalidad estará disponible próximamente');
        });
    }
    
    // Manejo de acciones en tarjetas
    document.querySelectorAll('.dashboard-card-actions').forEach(action => {
        action.addEventListener('click', function() {
            const cardTitle = this.closest('.dashboard-card-header').querySelector('.dashboard-card-title').textContent;
            alert(`Opciones para ${cardTitle}: Esta funcionalidad estará disponible próximamente`);
        });
    });
});