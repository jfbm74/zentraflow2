/**
 * layout.js - Maneja funcionalidades comunes del layout de ZentraFlow
 * Implementa la funcionalidad de colapsar la barra lateral con estado persistente
 */

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    
    // Función para guardar el estado del sidebar en localStorage
    function saveSidebarState(isCollapsed) {
        localStorage.setItem('zentraflow_sidebar_collapsed', isCollapsed ? 'true' : 'false');
    }
    
    // Función para obtener el estado guardado del sidebar
    function getSavedSidebarState() {
        return localStorage.getItem('zentraflow_sidebar_collapsed') === 'true';
    }
    
    // Aplicar el estado guardado al cargar la página
    if (sidebar && mainContent) {
        const isCollapsed = getSavedSidebarState();
        
        if (isCollapsed && window.innerWidth >= 992) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
        
        // Actualizar tooltips basado en el estado inicial
        updateTooltips();
    }
    
    // Manejar clic en el botón de toggle
    if (menuToggle && sidebar && mainContent) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            // En dispositivos móviles
            if (window.innerWidth < 992) {
                sidebar.classList.toggle('show');
            } else {
                // Solo guardar estado en localStorage para pantallas grandes
                saveSidebarState(sidebar.classList.contains('collapsed'));
            }
            
            // Actualizar tooltips cuando se colapsa/expande
            updateTooltips();
        });
    }
    
    // Manejar cambio de tamaño de ventana
    window.addEventListener('resize', function() {
        if (window.innerWidth < 992) {
            if (sidebar) {
                sidebar.classList.remove('collapsed');
                sidebar.classList.remove('show');
            }
            if (mainContent) {
                mainContent.classList.remove('expanded');
            }
        } else {
            // Restaurar el estado guardado al volver a pantalla grande
            const isCollapsed = getSavedSidebarState();
            if (sidebar) {
                sidebar.classList.toggle('collapsed', isCollapsed);
            }
            if (mainContent) {
                mainContent.classList.toggle('expanded', isCollapsed);
            }
            updateTooltips();
        }
    });
    
    // Inicializar tooltips para items de la barra lateral colapsada
    function updateTooltips() {
        if (sidebar && sidebar.classList.contains('collapsed')) {
            document.querySelectorAll('.sidebar-menu-link').forEach(item => {
                const text = item.querySelector('.sidebar-menu-text')?.textContent;
                if (text) {
                    item.setAttribute('title', text);
                }
            });
        } else if (sidebar) {
            document.querySelectorAll('.sidebar-menu-link').forEach(item => {
                item.removeAttribute('title');
            });
        }
    }
    
    // Actualizar tooltips cuando termine la transición
    if (sidebar) {
        sidebar.addEventListener('transitionend', updateTooltips);
    }
    
    // Agregar clase active a elementos de menú al hacer clic
    document.querySelectorAll('.sidebar-menu-link').forEach(item => {
        if (!item.classList.contains('logout-link')) {
            item.addEventListener('click', function(e) {
                document.querySelectorAll('.sidebar-menu-link').forEach(el => {
                    el.classList.remove('active');
                });
                this.classList.add('active');
            });
        }
    });
});