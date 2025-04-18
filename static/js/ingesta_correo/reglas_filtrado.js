/**
 * reglas_filtrado.js - Funcionalidades para la gestión de reglas de filtrado
 * Implementa la creación, edición, eliminación y reordenamiento de las reglas
 * de filtrado para la ingesta de correos.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Iniciando script de reglas de filtrado');
    
    // Verificar que Bootstrap esté disponible
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap no está disponible');
        return;
    }
    
    // Referencias a elementos del DOM
    const ruleList = document.getElementById('ruleList');
    const btnAddRule = document.getElementById('btnAddRule');
    const btnEmptyAddRule = document.getElementById('btnEmptyAddRule');
    const btnSaveRule = document.getElementById('btnSaveRule');
    const btnConfirmDelete = document.getElementById('btnConfirmDelete');
    const modalElement = document.getElementById('ruleModal');
    
    console.log('Elementos encontrados:', {
        ruleList: !!ruleList,
        btnAddRule: !!btnAddRule,
        btnEmptyAddRule: !!btnEmptyAddRule,
        btnSaveRule: !!btnSaveRule,
        btnConfirmDelete: !!btnConfirmDelete,
        modalElement: !!modalElement
    });
    
    // Inicializar el modal
    let ruleModal;
    try {
        ruleModal = new bootstrap.Modal(modalElement);
        console.log('Modal inicializado correctamente');
    } catch (error) {
        console.error('Error al inicializar el modal:', error);
        return;
    }
    
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    
    // Variables de estado
    let currentRuleId = null;
    let deleteRuleId = null;
    let isDragging = false;
    let changedPriorities = false;
    
    // Configurar event listeners con manejo de errores
    if (btnAddRule) {
        btnAddRule.addEventListener('click', (e) => {
            console.log('Botón Crear Nueva Regla clickeado');
            e.preventDefault();
            try {
                openCreateRuleModal();
            } catch (error) {
                console.error('Error al abrir el modal:', error);
            }
        });
    }
    
    if (btnEmptyAddRule) {
        btnEmptyAddRule.addEventListener('click', (e) => {
            console.log('Botón Crear Primera Regla clickeado');
            e.preventDefault();
            try {
                openCreateRuleModal();
            } catch (error) {
                console.error('Error al abrir el modal:', error);
            }
        });
    }
    
    if (btnSaveRule) {
        btnSaveRule.addEventListener('click', saveRule);
    }
    
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', confirmDeleteRule);
    }
    
    // Inicializar funcionalidad de drag & drop para reordenar
    initDragAndDrop();
    
    /**
     * Muestra un mensaje de éxito
     */
    function showSuccessMessage(message) {
        successMessage.textContent = message;
        successAlert.style.display = 'flex';
        
        setTimeout(() => {
            successAlert.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Muestra un mensaje de error
     */
    function showErrorMessage(message) {
        errorMessage.textContent = message;
        errorAlert.style.display = 'flex';
        
        setTimeout(() => {
            errorAlert.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Abre el modal para crear una nueva regla
     */
    function openCreateRuleModal() {
        console.log('Intentando abrir el modal de creación');
        try {
            // Limpiar el formulario
            const ruleForm = document.getElementById('ruleForm');
            if (ruleForm) {
                ruleForm.reset();
            }
            
            const ruleIdInput = document.getElementById('ruleId');
            if (ruleIdInput) {
                ruleIdInput.value = '';
            }
            
            currentRuleId = null;
            
            // Actualizar título del modal
            const modalLabel = document.getElementById('ruleModalLabel');
            if (modalLabel) {
                modalLabel.textContent = 'Nueva Regla de Filtrado';
            }
            
            // Mostrar el modal
            if (ruleModal) {
                console.log('Mostrando el modal');
                ruleModal.show();
            } else {
                console.error('El modal no está inicializado');
            }
        } catch (error) {
            console.error('Error en openCreateRuleModal:', error);
        }
    }
    
    /**
     * Abre el modal para editar una regla existente
     */
    function loadRuleData(ruleId) {
        // Hacer una petición para obtener los datos de la regla
        fetch(`/ingesta-correo/api/reglas/${ruleId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al obtener los datos de la regla');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Llenar el formulario con los datos
                    document.getElementById('ruleId').value = data.regla.id;
                    document.getElementById('ruleName').value = data.regla.nombre;
                    document.getElementById('ruleField').value = data.regla.campo;
                    document.getElementById('ruleCondition').value = data.regla.condicion;
                    document.getElementById('ruleValue').value = data.regla.valor;
                    document.getElementById('ruleAction').value = data.regla.accion;
                    document.getElementById('rulePriority').value = data.regla.prioridad;
                    document.getElementById('ruleActive').checked = data.regla.activa;
                    
                    // Actualizar título del modal
                    document.getElementById('ruleModalLabel').textContent = 'Editar Regla de Filtrado';
                    
                    // Mostrar el modal
                    ruleModal.show();
                } else {
                    showErrorMessage(data.message || 'Error al cargar los datos de la regla');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorMessage('Error al cargar los datos de la regla');
            });
    }
    
    /**
     * Guarda una regla (crear o actualizar)
     */
    function saveRule() {
        // Validar el formulario
        const form = document.getElementById('ruleForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Obtener datos del formulario
        const ruleId = document.getElementById('ruleId').value;
        const data = {
            nombre: document.getElementById('ruleName').value,
            campo: document.getElementById('ruleField').value,
            condicion: document.getElementById('ruleCondition').value,
            valor: document.getElementById('ruleValue').value,
            accion: document.getElementById('ruleAction').value,
            prioridad: parseInt(document.getElementById('rulePriority').value),
            activa: document.getElementById('ruleActive').checked
        };
        
        // Mostrar estado de carga
        const originalText = btnSaveRule.innerHTML;
        btnSaveRule.disabled = true;
        btnSaveRule.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        
        // Determinar si es creación o actualización
        const isUpdate = ruleId !== '';
        const url = isUpdate ? `/ingesta-correo/api/reglas/${ruleId}/` : '/ingesta-correo/api/reglas/';
        const method = isUpdate ? 'PUT' : 'POST';
        
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Hacer la petición
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la petición');
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                // Cerrar el modal
                ruleModal.hide();
                
                // Mostrar mensaje de éxito
                showSuccessMessage(result.message || `Regla ${isUpdate ? 'actualizada' : 'creada'} correctamente`);
                
                // Actualizar la lista de reglas (recargar la página)
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showErrorMessage(result.message || `Error al ${isUpdate ? 'actualizar' : 'crear'} la regla`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage(`Error al ${isUpdate ? 'actualizar' : 'crear'} la regla`);
        })
        .finally(() => {
            // Restaurar el botón
            btnSaveRule.disabled = false;
            btnSaveRule.innerHTML = originalText;
        });
    }
    
    /**
     * Muestra el modal de confirmación para eliminar una regla
     */
    function showDeleteConfirmation(ruleId) {
        deleteRuleId = ruleId;
        deleteConfirmModal.show();
    }
    
    /**
     * Elimina una regla después de la confirmación
     */
    function confirmDeleteRule() {
        if (!deleteRuleId) return;
        
        // Mostrar estado de carga
        const originalText = btnConfirmDelete.innerHTML;
        btnConfirmDelete.disabled = true;
        btnConfirmDelete.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';
        
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Hacer la petición
        fetch(`/ingesta-correo/api/reglas/${deleteRuleId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la petición');
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                // Cerrar el modal
                deleteConfirmModal.hide();
                
                // Mostrar mensaje de éxito
                showSuccessMessage(result.message || 'Regla eliminada correctamente');
                
                // Eliminar la regla de la lista
                const ruleElement = document.querySelector(`.rule-item[data-id="${deleteRuleId}"]`);
                if (ruleElement) {
                    ruleElement.remove();
                }
                
                // Si no quedan reglas, mostrar mensaje de vacío
                if (document.querySelectorAll('.rule-item').length === 0) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                showErrorMessage(result.message || 'Error al eliminar la regla');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Error al eliminar la regla');
        })
        .finally(() => {
            // Restaurar el botón
            btnConfirmDelete.disabled = false;
            btnConfirmDelete.innerHTML = originalText;
            deleteRuleId = null;
        });
    }
    
    /**
     * Cambia el estado de una regla (activa/inactiva)
     */
    function changeRuleState(ruleId, active) {
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Hacer la petición
        fetch(`/ingesta-correo/api/reglas/${ruleId}/estado/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ activa: active })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la petición');
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                // Actualizar el botón y el indicador visual
                const ruleElement = document.querySelector(`.rule-item[data-id="${ruleId}"]`);
                if (ruleElement) {
                    const toggleButton = ruleElement.querySelector('.toggle-rule');
                    const statusIndicator = ruleElement.querySelector('.rule-status');
                    
                    if (toggleButton) {
                        toggleButton.innerHTML = active ? 
                            '<i class="fas fa-toggle-on"></i>' : 
                            '<i class="fas fa-toggle-off"></i>';
                        toggleButton.title = active ? 'Desactivar' : 'Activar';
                        toggleButton.setAttribute('onclick', `toggleRuleState(event, ${ruleId}, ${!active})`);
                    }
                    
                    if (statusIndicator) {
                        if (active) {
                            statusIndicator.classList.add('active');
                            statusIndicator.classList.remove('inactive');
                        } else {
                            statusIndicator.classList.remove('active');
                            statusIndicator.classList.add('inactive');
                        }
                    }
                    
                    // Actualizar el estado en los detalles expandidos
                    const stateValue = ruleElement.querySelector('.rule-body .criteria-value .badge');
                    if (stateValue) {
                        stateValue.className = active ? 
                            'badge bg-success' : 
                            'badge bg-secondary';
                        stateValue.textContent = active ? 'Activa' : 'Inactiva';
                    }
                }
                
                // Mostrar mensaje de éxito
                showSuccessMessage(result.message || `Regla ${active ? 'activada' : 'desactivada'} correctamente`);
            } else {
                showErrorMessage(result.message || `Error al ${active ? 'activar' : 'desactivar'} la regla`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage(`Error al ${active ? 'activar' : 'desactivar'} la regla`);
        });
    }
    
    /**
     * Inicializa la funcionalidad de drag & drop para reordenar las reglas
     */
    function initDragAndDrop() {
        if (!ruleList) return;
        
        let draggedItem = null;
        const ruleItems = document.querySelectorAll('.rule-item');
        
        // Configurar event listeners para cada regla
        ruleItems.forEach(item => {
            const handle = item.querySelector('.handle');
            if (!handle) return;
            
            // Hacer que solo el handle inicie el arrastre
            handle.addEventListener('mousedown', function(e) {
                // Solo permitir arrastrar con el botón izquierdo del ratón
                if (e.button !== 0) return;
                
                e.stopPropagation();
                draggedItem = item;
                isDragging = true;
                
                // Añadir clase visual mientras se arrastra
                setTimeout(() => {
                    if (isDragging) {
                        item.classList.add('dragging');
                    }
                }, 100);
                
                // Capturar la posición inicial del ratón
                const startY = e.clientY;
                const startTop = item.offsetTop;
                
                // Función para mover el elemento
                const moveItem = function(e) {
                    if (!isDragging) return;
                    
                    const deltaY = e.clientY - startY;
                    const newTop = startTop + deltaY;
                    
                    // Limitar el movimiento dentro del contenedor
                    const containerTop = ruleList.offsetTop;
                    const containerBottom = containerTop + ruleList.offsetHeight;
                    
                    if (newTop >= containerTop && newTop + item.offsetHeight <= containerBottom) {
                        item.style.transform = `translateY(${deltaY}px)`;
                    }
                    
                    // Verificar si hay que reordenar
                    checkReorder(e.clientY);
                };
                
                // Función para determinar si hay que reordenar
                const checkReorder = function(y) {
                    ruleItems.forEach(otherItem => {
                        if (otherItem === draggedItem) return;
                        
                        const rect = otherItem.getBoundingClientRect();
                        const middle = rect.top + rect.height / 2;
                        
                        if (y < middle && draggedItem.previousElementSibling === otherItem) {
                            ruleList.insertBefore(draggedItem, otherItem);
                            changedPriorities = true;
                        } else if (y > middle && draggedItem.nextElementSibling === otherItem) {
                            ruleList.insertBefore(otherItem, draggedItem);
                            changedPriorities = true;
                        }
                    });
                };
                
                // Función para finalizar el arrastre
                const stopDrag = function() {
                    if (!isDragging) return;
                    
                    isDragging = false;
                    draggedItem.classList.remove('dragging');
                    draggedItem.style.transform = '';
                    
                    // Si se cambió el orden, guardar las nuevas prioridades
                    if (changedPriorities) {
                        saveNewPriorities();
                        changedPriorities = false;
                    }
                    
                    // Eliminar event listeners
                    document.removeEventListener('mousemove', moveItem);
                    document.removeEventListener('mouseup', stopDrag);
                };
                
                // Añadir event listeners para el movimiento y final del arrastre
                document.addEventListener('mousemove', moveItem);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }
    
    /**
     * Guarda las nuevas prioridades después de reordenar
     */
    function saveNewPriorities() {
        // Obtener todas las reglas en el nuevo orden
        const ruleItems = document.querySelectorAll('.rule-item');
        const newOrder = [];
        
        // Asignar nuevas prioridades basadas en la posición
        ruleItems.forEach((item, index) => {
            const ruleId = parseInt(item.getAttribute('data-id'));
            newOrder.push({
                id: ruleId,
                prioridad: index
            });
        });
        
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Enviar el nuevo orden al servidor
        fetch('/ingesta-correo/api/reglas/reordenar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ orden: newOrder })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al guardar el nuevo orden');
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                // Actualizar los atributos de prioridad en el DOM
                ruleItems.forEach((item, index) => {
                    item.setAttribute('data-priority', index);
                });
                
                showSuccessMessage('Orden de prioridades actualizado correctamente');
            } else {
                showErrorMessage(result.message || 'Error al guardar el nuevo orden de prioridades');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Error al guardar el nuevo orden de prioridades');
        });
    }

    // Hacer las funciones disponibles globalmente
    window.editRule = function(event, ruleId) {
        event.stopPropagation();
        loadRuleData(ruleId);
    };

    window.deleteRule = function(event, ruleId) {
        event.stopPropagation();
        showDeleteConfirmation(ruleId);
    };

    window.toggleRuleState = function(event, ruleId, active) {
        event.stopPropagation();
        changeRuleState(ruleId, active);
    };

    window.toggleRuleBody = function(headerElement) {
        const body = headerElement.nextElementSibling;
        body.classList.toggle('show');
    };
});

/**
 * Funciones globales para ser llamadas desde HTML
 */

/**
 * Alternar la visualización del cuerpo de una regla
 */
function toggleRuleBody(headerElement) {
    // No activar si se estaba arrastrando
    if (window.isDragging) return;
    
    const ruleItem = headerElement.parentElement;
    const ruleBody = ruleItem.querySelector('.rule-body');
    
    if (ruleBody) {
        ruleBody.classList.toggle('show');
    }
}

/**
 * Cambiar el estado de una regla (activo/inactivo)
 */
function toggleRuleState(event, ruleId, active) {
    event.stopPropagation();
    
    // Obtener el botón y mostrar estado de carga
    const button = event.currentTarget;
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Llamar a la API para cambiar el estado
    fetch(`/ingesta-correo/api/reglas/${ruleId}/estado/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ activa: active })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Actualizar el botón y visualización
            button.innerHTML = active ? 
                '<i class="fas fa-toggle-on"></i>' : 
                '<i class="fas fa-toggle-off"></i>';
            button.title = active ? 'Desactivar' : 'Activar';
            button.setAttribute('onclick', `toggleRuleState(event, ${ruleId}, ${!active})`);
            
            // Actualizar el indicador de estado
            const ruleElement = button.closest('.rule-item');
            const statusIndicator = ruleElement.querySelector('.rule-status');
            
            if (statusIndicator) {
                if (active) {
                    statusIndicator.classList.add('active');
                    statusIndicator.classList.remove('inactive');
                } else {
                    statusIndicator.classList.remove('active');
                    statusIndicator.classList.add('inactive');
                }
            }
            
            // Actualizar el estado en los detalles expandidos
            const stateValue = ruleElement.querySelector('.rule-body .criteria-value .badge');
            if (stateValue) {
                stateValue.className = active ? 
                    'badge bg-success' : 
                    'badge bg-secondary';
                stateValue.textContent = active ? 'Activa' : 'Inactiva';
            }
            
            // Mostrar mensaje de éxito
            const successAlert = document.getElementById('successAlert');
            const successMessage = document.getElementById('successMessage');
            
            if (successAlert && successMessage) {
                successMessage.textContent = `Regla ${active ? 'activada' : 'desactivada'} correctamente`;
                successAlert.style.display = 'flex';
                
                setTimeout(() => {
                    successAlert.style.display = 'none';
                }, 5000);
            }
        } else {
            // Restaurar el botón original en caso de error
            button.innerHTML = originalHTML;
            
            // Mostrar mensaje de error
            const errorAlert = document.getElementById('errorAlert');
            const errorMessage = document.getElementById('errorMessage');
            
            if (errorAlert && errorMessage) {
                errorMessage.textContent = result.message || `Error al ${active ? 'activar' : 'desactivar'} la regla`;
                errorAlert.style.display = 'flex';
                
                setTimeout(() => {
                    errorAlert.style.display = 'none';
                }, 5000);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.innerHTML = originalHTML;
        
        // Mostrar mensaje de error
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        
        if (errorAlert && errorMessage) {
            errorMessage.textContent = `Error al ${active ? 'activar' : 'desactivar'} la regla`;
            errorAlert.style.display = 'flex';
            
            setTimeout(() => {
                errorAlert.style.display = 'none';
            }, 5000);
        }
    })
    .finally(() => {
        button.disabled = false;
    });
}

/**
 * Abrir el modal para editar una regla
 */
function editRule(event, ruleId) {
    event.stopPropagation();
    
    // Hacer una petición para obtener los datos de la regla
    fetch(`/ingesta-correo/api/reglas/${ruleId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Llenar el formulario con los datos
                document.getElementById('ruleId').value = data.regla.id;
                document.getElementById('ruleName').value = data.regla.nombre;
                document.getElementById('ruleField').value = data.regla.campo;
                document.getElementById('ruleCondition').value = data.regla.condicion;
                document.getElementById('ruleValue').value = data.regla.valor;
                document.getElementById('ruleAction').value = data.regla.accion;
                document.getElementById('rulePriority').value = data.regla.prioridad;
                document.getElementById('ruleActive').checked = data.regla.activa;
                
                // Actualizar título del modal
                document.getElementById('ruleModalLabel').textContent = 'Editar Regla de Filtrado';
                
                // Mostrar el modal
                const ruleModal = new bootstrap.Modal(document.getElementById('ruleModal'));
                ruleModal.show();
            } else {
                // Mostrar mensaje de error
                const errorAlert = document.getElementById('errorAlert');
                const errorMessage = document.getElementById('errorMessage');
                
                if (errorAlert && errorMessage) {
                    errorMessage.textContent = data.message || 'Error al cargar los datos de la regla';
                    errorAlert.style.display = 'flex';
                    
                    setTimeout(() => {
                        errorAlert.style.display = 'none';
                    }, 5000);
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Mostrar mensaje de error
            const errorAlert = document.getElementById('errorAlert');
            const errorMessage = document.getElementById('errorMessage');
            
            if (errorAlert && errorMessage) {
                errorMessage.textContent = 'Error al cargar los datos de la regla';
                errorAlert.style.display = 'flex';
                
                setTimeout(() => {
                    errorAlert.style.display = 'none';
                }, 5000);
            }
        });
}

/**
 * Mostrar el modal de confirmación para eliminar una regla
 */
function deleteRule(event, ruleId) {
    event.stopPropagation();
    
    // Guardar el ID de la regla a eliminar
    window.deleteRuleId = ruleId;
    
    // Mostrar el modal de confirmación
    const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    deleteConfirmModal.show();
    
    // Configurar el botón de confirmar
    const btnConfirmDelete = document.getElementById('btnConfirmDelete');
    if (btnConfirmDelete) {
        btnConfirmDelete.onclick = function() {
            // Mostrar estado de carga
            const originalText = btnConfirmDelete.innerHTML;
            btnConfirmDelete.disabled = true;
            btnConfirmDelete.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';
            
            // Hacer la petición para eliminar
            fetch(`/ingesta-correo/api/reglas/${ruleId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Cerrar el modal
                    deleteConfirmModal.hide();
                    
                    // Eliminar la regla del DOM
                    const ruleElement = document.querySelector(`.rule-item[data-id="${ruleId}"]`);
                    if (ruleElement) {
                        ruleElement.remove();
                    }
                    
                    // Mostrar mensaje de éxito
                    const successAlert = document.getElementById('successAlert');
                    const successMessage = document.getElementById('successMessage');
                    
                    if (successAlert && successMessage) {
                        successMessage.textContent = result.message || 'Regla eliminada correctamente';
                        successAlert.style.display = 'flex';
                        
                        setTimeout(() => {
                            successAlert.style.display = 'none';
                        }, 5000);
                    }
                    
                    // Si no quedan reglas, recargar para mostrar el mensaje de vacío
                    if (document.querySelectorAll('.rule-item').length === 0) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                } else {
                    // Mostrar mensaje de error
                    const errorAlert = document.getElementById('errorAlert');
                    const errorMessage = document.getElementById('errorMessage');
                    
                    if (errorAlert && errorMessage) {
                        errorMessage.textContent = result.message || 'Error al eliminar la regla';
                        errorAlert.style.display = 'flex';
                        
                        setTimeout(() => {
                            errorAlert.style.display = 'none';
                        }, 5000);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Mostrar mensaje de error
                const errorAlert = document.getElementById('errorAlert');
                const errorMessage = document.getElementById('errorMessage');
                
                if (errorAlert && errorMessage) {
                    errorMessage.textContent = 'Error al eliminar la regla';
                    errorAlert.style.display = 'flex';
                    
                    setTimeout(() => {
                        errorAlert.style.display = 'none';
                    }, 5000);
                }
            })
            .finally(() => {
                // Restaurar el botón
                btnConfirmDelete.disabled = false;
                btnConfirmDelete.innerHTML = originalText;
            });
        };
    }
}