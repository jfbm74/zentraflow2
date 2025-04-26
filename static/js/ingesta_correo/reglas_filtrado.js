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

    // Inicializar los cuerpos de las reglas para que estén ocultos al cargar
    document.addEventListener('DOMContentLoaded', function() {
        // Ocultar todos los cuerpos de reglas al inicio
        document.querySelectorAll('.rule-body').forEach(function(body) {
            body.style.display = 'none';
        });
    });
}); 