/**
 * Funciones comunes para la gestión de reglas de filtrado
 * Este archivo contiene funciones compartidas entre diferentes vistas de reglas
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Iniciando script reglas_common.js");

    // Inicializar tooltips de Bootstrap si están disponibles
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Manejar eventos del modal de reglas
    const ruleModal = document.getElementById('ruleModal');
    if (ruleModal) {
        ruleModal.addEventListener('hidden.bs.modal', function () {
            // Resetear formulario al cerrar modal
            document.getElementById('ruleForm')?.reset();
            // Resetear ID (para distinguir creación vs edición)
            document.getElementById('ruleId').value = '';
            // Ocultar sección de prueba
            const testSection = document.getElementById('testRuleSection');
            if (testSection) testSection.style.display = 'none';
        });
    }

    // Inicializar los cuerpos de las reglas para que estén ocultos al cargar
    document.querySelectorAll('.rule-body').forEach(function(body) {
        body.style.display = 'none';
    });
});

/**
 * Función para editar una regla
 * @param {Event} event - Evento del clic
 * @param {number|string} ruleId - ID de la regla a editar
 */
window.editRule = function(event, ruleId) {
    // Detener propagación para evitar toggle del cuerpo
    event.stopPropagation();
    
    console.log(`Editando regla con ID: ${ruleId}`);
    
    // CSRF token
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Mostrar el modal primero para mejorar la experiencia del usuario
    const ruleModal = new bootstrap.Modal(document.getElementById('ruleModal'));
    ruleModal.show();
    
    // Actualizar título del modal inmediatamente
    document.getElementById('ruleModalLabel').textContent = 'Editar Regla de Filtrado';
    document.getElementById('ruleId').value = ruleId;
    
    // Mostrar indicador de carga
    document.getElementById('ruleName').value = 'Cargando...';
    document.getElementById('ruleValue').value = 'Cargando...';
    
    // Cargar datos de la regla desde la API
    fetch(`/ingesta-correo/api/reglas/${ruleId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(response => {
        console.log('Respuesta del API:', response);
        
        // Verificar si la respuesta tiene datos válidos
        if (!response) {
            console.error('Respuesta del API vacía');
            return;
        }
        
        // Verificar si la respuesta tiene el campo regla o está en el nivel superior
        const reglaData = response.regla || response;
        
        if (!reglaData) {
            console.error('No se encontraron datos de la regla en la respuesta');
            return;
        }
        
        // Llenar el formulario con los datos de la API
        if (reglaData.nombre) document.getElementById('ruleName').value = reglaData.nombre;
        if (reglaData.campo) document.getElementById('ruleField').value = reglaData.campo;
        if (reglaData.condicion) document.getElementById('ruleCondition').value = reglaData.condicion;
        if (reglaData.valor) document.getElementById('ruleValue').value = reglaData.valor;
        if (reglaData.accion) document.getElementById('ruleAction').value = reglaData.accion;
        if (reglaData.prioridad) document.getElementById('rulePriority').value = reglaData.prioridad;
        if (reglaData.activa !== undefined) document.getElementById('ruleActive').checked = reglaData.activa;
        
        // Configurar campo de prueba si tenemos el campo
        if (reglaData.campo && typeof setupTestFields === 'function') {
            setupTestFields(reglaData.campo);
            const testRuleSection = document.getElementById('testRuleSection');
            if (testRuleSection) testRuleSection.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error al cargar datos de la API:', error);
        
        // Mostrar mensaje de error si hay una función para ello
        if (typeof showErrorMessage === 'function') {
            showErrorMessage('Error al cargar los datos de la regla');
        } else {
            alert('Error al cargar los datos de la regla');
        }
    });
};

/**
 * Función para activar/desactivar una regla
 * @param {Event} event - Evento del clic
 * @param {HTMLElement|number|string} elementOrId - Elemento HTML o ID de la regla
 * @param {boolean} [active] - Estado a establecer (opcional)
 */
window.toggleRuleState = function(event, elementOrId, active) {
    event.stopPropagation();
    
    // Interpretar los parámetros según su tipo
    let ruleId, button;
    
    if (typeof elementOrId === 'object') {
        // Nuevo formato: toggleRuleState(event, button)
        button = elementOrId;
        ruleId = button.dataset.id;
    } else {
        // Formato antiguo: toggleRuleState(event, ruleId, active)
        ruleId = elementOrId;
        button = event.currentTarget;
    }
    
    if (!ruleId) {
        console.error('No se pudo determinar el ID de la regla');
        return;
    }
    
    console.log(`Activando/Desactivando regla ${ruleId}`);
    
    // CSRF token
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Deshabilitar botón mientras se procesa
    if (button) button.disabled = true;
    
    // Si active está definido, lo usamos; si no, asumimos que queremos invertir el estado actual
    const newState = active !== undefined ? active : null;
    
    // Enviar cambio de estado
    fetch(`/ingesta-correo/reglas/${ruleId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: newState !== null ? JSON.stringify({ activa: newState }) : null
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta del servidor:', data);
        if (data.success) {
            // Si tenemos el botón directamente
            if (button) {
                const isActive = data.activo;
                const icon = button.querySelector('i');
                
                if (icon) {
                    // Cambiar la clase del icono
                    icon.className = isActive ? 'fas fa-toggle-on' : 'fas fa-toggle-off';
                }
                
                // Actualizar el botón
                button.setAttribute('title', isActive ? 'Desactivar' : 'Activar');
                
                // Actualizar estado en el encabezado
                try {
                    const ruleItem = button.closest('.rule-item');
                    if (ruleItem) {
                        // Actualizar badge de estado
                        const statusBadge = ruleItem.querySelector('.criteria-value .badge');
                        if (statusBadge) {
                            statusBadge.className = isActive ? 'badge bg-success' : 'badge bg-secondary';
                            statusBadge.textContent = isActive ? 'Activa' : 'Inactiva';
                        }
                        
                        // Actualizar círculo de estado
                        const statusCircle = ruleItem.querySelector('.rule-status');
                        if (statusCircle) {
                            statusCircle.className = isActive ? 'rule-status active' : 'rule-status inactive';
                        }
                    }
                } catch (e) {
                    console.error('Error al actualizar estado visual:', e);
                }
            }
            
            // Mostrar mensaje de éxito
            if (typeof showSuccessMessage === 'function') {
                showSuccessMessage(data.message || 'Estado actualizado correctamente');
            } else {
                alert(data.message || 'Estado actualizado correctamente');
            }
            
            // Recargar la página para reflejar los cambios
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            // Mostrar mensaje de error
            if (typeof showErrorMessage === 'function') {
                showErrorMessage(data.message || 'Error al actualizar el estado');
            } else {
                alert('Error: ' + (data.message || 'Error al actualizar el estado'));
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Mostrar mensaje de error
        if (typeof showErrorMessage === 'function') {
            showErrorMessage('Error al comunicarse con el servidor');
        } else {
            alert('Error: Error al comunicarse con el servidor');
        }
    })
    .finally(() => {
        // Re-habilitar el botón
        if (button) button.disabled = false;
    });
};

/**
 * Función para eliminar una regla
 * @param {Event} event - Evento del clic
 * @param {HTMLElement|number|string} elementOrId - Elemento HTML o ID de la regla
 */
window.deleteRule = function(event, elementOrId) {
    event.stopPropagation();
    
    // Interpretar los parámetros según su tipo
    let ruleId, button;
    
    if (typeof elementOrId === 'object') {
        // Nuevo formato: deleteRule(event, button)
        button = elementOrId;
        ruleId = button.dataset.id;
    } else {
        // Formato antiguo: deleteRule(event, ruleId)
        ruleId = elementOrId;
        button = event.currentTarget;
    }
    
    if (!ruleId) {
        console.error('No se pudo determinar el ID de la regla');
        return;
    }
    
    console.log(`Eliminando regla ${ruleId}`);
    
    if (confirm('¿Está seguro de que desea eliminar esta regla?')) {
        // CSRF token
        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Deshabilitar botón mientras se procesa
        if (button) button.disabled = true;
        
        // Usar la API endpoint para eliminar
        fetch(`/ingesta-correo/api/reglas/${ruleId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data);
            if (data.success) {
                // Mostrar mensaje de éxito
                if (typeof showSuccessMessage === 'function') {
                    showSuccessMessage(data.message || 'Regla eliminada correctamente');
                } else {
                    alert(data.message || 'Regla eliminada correctamente');
                }
                
                // Recargar la página para reflejar los cambios
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // Mostrar mensaje de error
                if (typeof showErrorMessage === 'function') {
                    showErrorMessage(data.message || 'Error al eliminar la regla');
                } else {
                    alert('Error: ' + (data.message || 'Error al eliminar la regla'));
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Mostrar mensaje de error
            if (typeof showErrorMessage === 'function') {
                showErrorMessage('Error al comunicarse con el servidor');
            } else {
                alert('Error: Error al comunicarse con el servidor');
            }
        })
        .finally(() => {
            // Re-habilitar el botón
            if (button) button.disabled = false;
        });
    }
};

/**
 * Función para expandir/colapsar el detalle de la regla
 * @param {HTMLElement} headerElem - Elemento de cabecera de la regla
 */
window.toggleRuleBody = function(headerElem) {
    // Prevenir la propagación del clic a otros elementos (como botones)
    event.stopPropagation();
    
    // Buscar el body que sigue al header
    const body = headerElem.nextElementSibling;
    console.log('Toggle rule body:', { header: headerElem, body: body });
    
    if (body && body.classList.contains('rule-body')) {
        // Toggle la visibilidad del body
        if (body.style.display === 'block') {
            body.style.display = 'none';
            // Cambiar icono si existe
            const toggleIcon = headerElem.querySelector('.toggle-icon i');
            if (toggleIcon) {
                toggleIcon.classList.remove('fa-chevron-up');
                toggleIcon.classList.add('fa-chevron-down');
            }
        } else {
            body.style.display = 'block';
            // Cambiar icono si existe
            const toggleIcon = headerElem.querySelector('.toggle-icon i');
            if (toggleIcon) {
                toggleIcon.classList.remove('fa-chevron-down');
                toggleIcon.classList.add('fa-chevron-up');
            }
        }
    } else {
        console.error('No se encontró el cuerpo de la regla o no tiene la clase esperada');
    }
};

/**
 * Función para probar regla
 * Esta es una función común que redirige a la implementación específica en reglas_test.js
 */
window.testRule = function() {
    // La implementación completa se encuentra en reglas_test.js
    console.log("Llamando a la función testRule");
    
    // Si existe una implementación específica, la llamamos
    if (window.testRuleImplementation) {
        window.testRuleImplementation();
    } else {
        console.warn("La implementación de testRule no está disponible");
        alert("Funcionalidad de prueba no disponible. Asegúrese de incluir reglas_test.js");
    }
};

/**
 * Funciones comunes para manejar reglas de filtrado
 */

// Variable para controlar estado de edición
let isEditing = false;

/**
 * Función para mostrar mensajes de éxito
 * @param {string} message - Mensaje a mostrar
 */
function showSuccessMessage(message) {
    const successAlert = document.getElementById('successAlert');
    const successMessage = document.getElementById('successMessage');
    
    if (successMessage) successMessage.textContent = message;
    if (successAlert) {
        successAlert.style.display = 'block';
        setTimeout(function() {
            successAlert.style.display = 'none';
        }, 3000);
    }
}

/**
 * Función para mostrar mensajes de error
 * @param {string} message - Mensaje a mostrar
 */
function showErrorMessage(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorMessage) errorMessage.textContent = message;
    if (errorAlert) {
        errorAlert.style.display = 'block';
        setTimeout(function() {
            errorAlert.style.display = 'none';
        }, 5000);
    }
} 