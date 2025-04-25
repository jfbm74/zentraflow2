/**
 * Script para la administración de reglas de filtrado
 * Maneja la lógica de mostrar/ocultar campos según se trate de una regla simple o compuesta
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Iniciando script reglas_filtrado.js");
    
        // Seleccionar los elementos relevantes
    const esCompuestaCheckbox = document.getElementById('id_es_compuesta');
    const fieldsetReglaSimple = document.querySelector('.regla-simple')?.closest('fieldset');
    const fieldsetOperadorLogico = document.getElementById('id_operador_logico')?.closest('.form-row');
    const inlineCondiciones = document.querySelector('.inline-group');
        
        // Función para actualizar la visibilidad de los campos
        function actualizarVisibilidad() {
        if (!esCompuestaCheckbox) return;
        
        const esCompuesta = esCompuestaCheckbox.checked;
            
            if (esCompuesta) {
                // Ocultar campos de regla simple
            if (fieldsetReglaSimple) fieldsetReglaSimple.style.display = 'none';
                // Mostrar campos de regla compuesta
            if (fieldsetOperadorLogico) fieldsetOperadorLogico.style.display = 'block';
            if (inlineCondiciones) inlineCondiciones.style.display = 'block';
            } else {
                // Mostrar campos de regla simple
            if (fieldsetReglaSimple) fieldsetReglaSimple.style.display = 'block';
                // Ocultar campos de regla compuesta
            if (fieldsetOperadorLogico) fieldsetOperadorLogico.style.display = 'none';
            if (inlineCondiciones) inlineCondiciones.style.display = 'none';
            }
        }
        
        // Actualizar visibilidad inicial
    if (esCompuestaCheckbox) {
        actualizarVisibilidad();
        
        // Actualizar cuando cambie el checkbox
        esCompuestaCheckbox.addEventListener('change', actualizarVisibilidad);
    }
        
        // Añadir clases personalizadas a algunos elementos para mejorar la UX
    document.querySelectorAll('.field-display_activa span').forEach(function(span) {
        const text = span.textContent;
            if (text === '✓') {
            span.classList.add('regla-activa');
            } else if (text === '✗') {
            span.classList.add('regla-inactiva');
            }
        });
        
        // Colorear las filas de las reglas inactivas
    document.querySelectorAll('tr').forEach(function(tr) {
        const activaCell = tr.querySelector('td.field-display_activa');
        if (activaCell && activaCell.querySelector('span.regla-inactiva')) {
            tr.classList.add('regla-row-inactiva');
            }
        });
        
        // Validar que las reglas compuestas tienen al menos una condición
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!esCompuestaCheckbox) return;
            
            const esCompuesta = esCompuestaCheckbox.checked;
            if (esCompuesta) {
                // Verificar si hay al menos una condición (excluir los formularios vacíos)
                const condicionesValidas = Array.from(document.querySelectorAll('.inline-related:not(.empty-form)')).filter(function(condicion) {
                    const campoInput = condicion.querySelector('select[id$="-campo"]');
                    const condicionInput = condicion.querySelector('select[id$="-condicion"]');
                    const valorInput = condicion.querySelector('input[id$="-valor"]');
                    
                    // Verificar que todos los campos tengan valor
                    return campoInput?.value && condicionInput?.value && valorInput?.value;
                }).length;
                
                if (condicionesValidas === 0) {
                    alert('Las reglas compuestas deben tener al menos una condición. Por favor, añada una condición o desmarque la opción "Es compuesta".');
                    e.preventDefault();
                    return false;
                }
            }
        });
    });

    // Configuración del botón guardar regla
    const btnSaveRule = document.getElementById('btnSaveRule');
    if (btnSaveRule) {
        btnSaveRule.addEventListener('click', function() {
            saveRule();
        });
    }
    
    // Función para guardar regla
    function saveRule() {
        console.log('Guardando regla...');
        
        // Validar formulario
        if (!validateRuleForm()) {
            return;
        }
        
        // Obtener datos del formulario
        const ruleId = document.getElementById('ruleId').value;
        const ruleData = {
            nombre: document.getElementById('ruleName').value,
            campo: document.getElementById('ruleField').value,
            condicion: document.getElementById('ruleCondition').value,
            valor: document.getElementById('ruleValue').value,
            accion: document.getElementById('ruleAction').value,
            prioridad: document.getElementById('rulePriority').value,
            activa: document.getElementById('ruleActive').checked
        };
        
        // CSRF token
        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Determinar si es creación o edición
        const isEdit = ruleId !== '';
        const url = isEdit ? `/ingesta-correo/api/reglas/${ruleId}/` : '/ingesta-correo/api/reglas/';
        const method = isEdit ? 'PUT' : 'POST';
        
        // Enviar al servidor
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(ruleData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            // Mostrar mensaje de éxito
            showSuccessMessage(isEdit ? 'Regla actualizada con éxito' : 'Regla creada con éxito');
            
            // Cerrar modal y recargar página
            const modalInstance = bootstrap.Modal.getInstance(document.getElementById('ruleModal'));
            if (modalInstance) {
                modalInstance.hide();
            }
            
            setTimeout(function() {
                window.location.reload();
            }, 1000);
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Ha ocurrido un error al procesar la solicitud');
        });
    }
    
    // Editar regla existente
    window.editRule = function(event, ruleId) {
        // Detener propagación para evitar toggle del cuerpo
        event.stopPropagation();
        
        console.log(`Intentando editar regla con ID: ${ruleId}`);
        
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
        
        // Cargar datos de la regla directamente desde la lista de reglas en el DOM
        const ruleElement = document.querySelector(`[data-id="${ruleId}"]`);
        if (ruleElement) {
            try {
                console.log('Obteniendo datos de la regla del DOM');
                
                // Intentar extraer los datos directamente del DOM
                const titleElement = ruleElement.querySelector('.rule-title');
                const nombre = titleElement ? titleElement.childNodes[4].textContent.trim() : '';
                
                // Obtener campo y acción de las badges
                const campoBadge = titleElement ? titleElement.querySelector('.rule-badge.field-asunto, .rule-badge.field-remitente, .rule-badge.field-contenido, .rule-badge.field-adjunto_nombre') : null;
                const accionBadge = titleElement ? titleElement.querySelector('.rule-badge.action-procesar, .rule-badge.action-ignorar, .rule-badge.action-marcar_revision') : null;
                
                const campo = campoBadge ? campoBadge.className.split('field-')[1].split(' ')[0] : '';
                const accion = accionBadge ? accionBadge.className.split('action-')[1].split(' ')[0] : '';
                
                // Obtener estado
                const isActive = ruleElement.querySelector('.rule-status').classList.contains('active');
                
                // Obtener el valor y la condición de los detalles
                let valor = '';
                let condicion = '';
                let prioridad = 10;
                
                const ruleBody = ruleElement.querySelector('.rule-body');
                if (ruleBody) {
                    const criteriaItems = ruleBody.querySelectorAll('.criteria-item');
                    criteriaItems.forEach(item => {
                        const label = item.querySelector('.criteria-label');
                        const value = item.querySelector('.criteria-value');
                        
                        if (label && value) {
                            const labelText = label.textContent.trim();
                            const valueText = value.textContent.trim();
                            
                            if (labelText === 'Condición:') {
                                // Mapear texto de condición a su valor
                                if (valueText.includes('Contiene')) condicion = 'contiene';
                                else if (valueText.includes('No contiene')) condicion = 'no_contiene';
                                else if (valueText.includes('Es igual a')) condicion = 'es_igual';
                                else if (valueText.includes('Empieza con')) condicion = 'empieza_con';
                                else if (valueText.includes('Termina con')) condicion = 'termina_con';
                                else condicion = 'contiene'; // Valor por defecto
                            }
                            else if (labelText === 'Valor:') {
                                valor = valueText.replace(/^'|'$/g, ''); // Quitar comillas
                            }
                            else if (labelText === 'Prioridad:') {
                                prioridad = parseInt(valueText) || 10;
                            }
                        }
                    });
                }
                
                console.log('Datos obtenidos del DOM:', { nombre, campo, condicion, valor, accion, isActive, prioridad });
                
                // Llenar el formulario con los datos
                document.getElementById('ruleName').value = nombre || '';
                document.getElementById('ruleField').value = campo || '';
                document.getElementById('ruleCondition').value = condicion || '';
                document.getElementById('ruleValue').value = valor || '';
                document.getElementById('ruleAction').value = accion || '';
                document.getElementById('rulePriority').value = prioridad || 10;
                document.getElementById('ruleActive').checked = isActive;
                
                // Configurar campo de prueba
                setupTestFields(campo);
                document.getElementById('testRuleSection').style.display = 'block';
                
                // También intentamos obtener los datos de la API para mayor precisión
                console.log('Intentando obtener datos de la API como respaldo');
            } catch (error) {
                console.error('Error al extraer datos del DOM:', error);
            }
        }
        
        // Cargar datos de la regla desde la API (como respaldo o para completar datos)
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
            console.log('Respuesta de API:', response);
            
            // Verificar si la respuesta tiene datos válidos
            if (!response) {
                console.error('Respuesta de API vacía');
                return;
            }
            
            // Verificar si la respuesta tiene el campo regla o está en el nivel superior
            const reglaData = response.regla || response;
            
            if (!reglaData) {
                console.error('No se encontraron datos de la regla en la respuesta');
                return;
            }
            
            // Llenar el formulario con los datos de la API solo si están disponibles
            if (reglaData.nombre) document.getElementById('ruleName').value = reglaData.nombre;
            if (reglaData.campo) document.getElementById('ruleField').value = reglaData.campo;
            if (reglaData.condicion) document.getElementById('ruleCondition').value = reglaData.condicion;
            if (reglaData.valor) document.getElementById('ruleValue').value = reglaData.valor;
            if (reglaData.accion) document.getElementById('ruleAction').value = reglaData.accion;
            if (reglaData.prioridad) document.getElementById('rulePriority').value = reglaData.prioridad;
            if (reglaData.activa !== undefined) document.getElementById('ruleActive').checked = reglaData.activa;
            
            // Configurar campo de prueba si tenemos el campo de la API
            if (reglaData.campo) {
                setupTestFields(reglaData.campo);
                document.getElementById('testRuleSection').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error al cargar datos de la API:', error);
            // No mostrar mensaje de error al usuario, ya que tenemos los datos del DOM
        });
    };
    
    // Eliminar regla
    let ruleToDelete = null;
    
    window.deleteRule = function(event, ruleId) {
        // Detener propagación para evitar toggle del cuerpo
        event.stopPropagation();
        
        // Guardar ID para uso posterior
        ruleToDelete = ruleId;
        
        // Mostrar modal de confirmación
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        deleteModal.show();
    };
    
    // Confirmar eliminación
    const btnConfirmDelete = document.getElementById('btnConfirmDelete');
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', function() {
            if (ruleToDelete) {
                // CSRF token
                const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
                
                // Enviar solicitud de eliminación
                fetch(`/ingesta-correo/api/reglas/${ruleToDelete}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrftoken
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Error en la respuesta del servidor');
                    }
                    return response.json();
                })
                .then(() => {
                    // Cerrar modal y mostrar mensaje
                    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    showSuccessMessage('Regla eliminada correctamente');
                    
                    // Eliminar elemento del DOM o recargar
                    const ruleElement = document.querySelector(`[data-id="${ruleToDelete}"]`);
                    if (ruleElement) {
                        ruleElement.style.opacity = '0';
                        setTimeout(() => {
                            ruleElement.remove();
                            
                            // Si no quedan reglas, mostrar mensaje vacío
                            if (document.querySelectorAll('.rule-item').length === 0) {
                                location.reload();
                            }
                        }, 300);
                    }
                    
                    // Resetear
                    ruleToDelete = null;
                })
                .catch(error => {
                    console.error('Error:', error);
                    
                    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    showErrorMessage('Error al eliminar la regla');
                    ruleToDelete = null;
                });
            }
        });
    }
    
    // Cambiar estado de regla (activar/desactivar)
    window.toggleRuleState = function(event, ruleId, active) {
        // Detener propagación para evitar toggle del cuerpo
        event.stopPropagation();
        
        // CSRF token
        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Enviar cambio de estado
        fetch(`/ingesta-correo/api/reglas/${ruleId}/estado/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ activa: active })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(() => {
            const button = event.currentTarget;
            const icon = button.querySelector('i');
            const status = button.closest('.rule-header').querySelector('.rule-status');
            
            // Actualizar interfaz
            if (active) {
                icon.classList.remove('fa-toggle-off');
                icon.classList.add('fa-toggle-on');
                status.classList.remove('inactive');
                status.classList.add('active');
                button.setAttribute('title', 'Desactivar');
                button.setAttribute('onclick', `toggleRuleState(event, ${ruleId}, false)`);
            } else {
                icon.classList.remove('fa-toggle-on');
                icon.classList.add('fa-toggle-off');
                status.classList.remove('active');
                status.classList.add('inactive');
                button.setAttribute('title', 'Activar');
                button.setAttribute('onclick', `toggleRuleState(event, ${ruleId}, true)`);
            }
            
            showSuccessMessage(`Regla ${active ? 'activada' : 'desactivada'} correctamente`);
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage(`Error al ${active ? 'activar' : 'desactivar'} la regla`);
        });
    };
    
    // Expandir/colapsar el detalle de la regla
    window.toggleRuleBody = function(headerElem) {
        const body = headerElem.nextElementSibling;
        
        if (body.style.display === 'block') {
            body.style.display = 'none';
        } else {
            body.style.display = 'block';
        }
    };
    
    // Mostrar mensaje de éxito
    function showSuccessMessage(message) {
        const alertElement = document.getElementById('successAlert');
        document.getElementById('successMessage').textContent = message;
        alertElement.style.display = 'block';
        setTimeout(function() {
            alertElement.style.display = 'none';
        }, 3000);
    }
    
    // Mostrar mensaje de error
    function showErrorMessage(message) {
        const alertElement = document.getElementById('errorAlert');
        document.getElementById('errorMessage').textContent = message;
        alertElement.style.display = 'block';
        setTimeout(function() {
            alertElement.style.display = 'none';
        }, 5000);
    }
    
    // Validar formulario
    function validateRuleForm() {
        // Validación básica
        if (!document.getElementById('ruleName').value) {
            showErrorMessage('El nombre de la regla es obligatorio');
            return false;
        }
        
        if (!document.getElementById('ruleField').value) {
            showErrorMessage('Debe seleccionar un campo');
            return false;
        }
        
        if (!document.getElementById('ruleCondition').value) {
            showErrorMessage('Debe seleccionar una condición');
            return false;
        }
        
        if (!document.getElementById('ruleValue').value) {
            showErrorMessage('Debe proporcionar un valor');
            return false;
        }
        
        if (!document.getElementById('ruleAction').value) {
            showErrorMessage('Debe seleccionar una acción');
            return false;
        }
        
        return true;
    }
    
    // Configurar campos de prueba según el campo seleccionado
    const ruleFieldSelect = document.getElementById('ruleField');
    if (ruleFieldSelect) {
        ruleFieldSelect.addEventListener('change', function() {
            const testSection = document.getElementById('testRuleSection');
            if (testSection && testSection.style.display !== 'none') {
                setupTestFields(this.value);
            }
        });
    }
    
    function setupTestFields(field) {
        // Ocultar todos los campos de prueba
        document.querySelectorAll('.test-field').forEach(function(element) {
            element.style.display = 'none';
        });
        
        // Mostrar solo el campo relevante
        switch (field) {
            case 'ASUNTO':
                document.getElementById('testSubjectField').style.display = 'block';
                break;
            case 'REMITENTE':
                document.getElementById('testSenderField').style.display = 'block';
                break;
            case 'DESTINATARIO':
                document.getElementById('testRecipientField').style.display = 'block';
                break;
            case 'CONTENIDO':
                document.getElementById('testContentField').style.display = 'block';
                break;
            case 'ADJUNTO_NOMBRE':
                document.getElementById('testAttachmentField').style.display = 'block';
                break;
        }
    }
    
    // Manejar eventos del formulario para evitar envío normal
    const ruleForm = document.getElementById('ruleForm');
    if (ruleForm) {
        ruleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            document.getElementById('btnSaveRule').click();
        });
    }
    
    // Habilitar drag & drop para reordenar reglas
    if (typeof Sortable !== 'undefined') {
        const ruleList = document.getElementById('ruleList');
        if (ruleList) {
            new Sortable(ruleList, {
                animation: 150,
                ghostClass: 'dragging',
                handle: '.handle',
                onEnd: function(evt) {
                    const ruleItems = document.querySelectorAll('.rule-item');
                    const newOrder = [];
                    
                    // Recopilar IDs y prioridades
                    ruleItems.forEach(function(item, index) {
                        newOrder.push({
                            id: item.getAttribute('data-id'),
                            prioridad: (index + 1) * 10
                        });
                        
                        // Actualizar atributo de prioridad
                        item.setAttribute('data-priority', (index + 1) * 10);
                    });
                    
                    // Enviar nuevo orden al servidor
                    if (newOrder.length > 0) {
                        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
                        
                        fetch('/ingesta-correo/api/reglas/reordenar/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken
                            },
                            body: JSON.stringify({ reglas: newOrder })
                        })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Error en la respuesta del servidor');
                            }
                            return response.json();
                        })
                        .then(() => {
                            showSuccessMessage('Orden de reglas actualizado correctamente');
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showErrorMessage('Error al actualizar el orden de las reglas');
                            // Recargar para restaurar orden original
                            setTimeout(function() {
                                window.location.reload();
                            }, 2000);
                        });
                    }
                }
            });
        }
    }
});

// Crear función para probar regla
window.testRule = function() {
    // La implementación se encuentra en reglas_test.js
}; 