/**
 * reglas_test.js - Funcionalidades para probar reglas de filtrado
 * Permite a los usuarios verificar si una regla funciona correctamente antes de guardarla
 */

document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos DOM
    const testRuleSection = document.getElementById('testRuleSection');
    const btnTestRule = document.getElementById('btnTestRule');
    const testSubject = document.getElementById('testSubject');
    const testSender = document.getElementById('testSender');
    const testRecipient = document.getElementById('testRecipient');
    const testContent = document.getElementById('testContent');
    const testAttachment = document.getElementById('testAttachment');
    const testResultContainer = document.getElementById('testResultContainer');
    const testResult = document.getElementById('testResult');
    const testMessage = document.getElementById('testMessage');
    const testAction = document.getElementById('testAction');
    
    // Event listener para el botón de prueba
    if (btnTestRule) {
        btnTestRule.addEventListener('click', testRule);
    }
    
    /**
     * Prueba la regla con los datos proporcionados
     */
    function testRule() {
        // Validar que tenemos los campos necesarios de la regla
        const ruleField = document.getElementById('ruleField');
        const ruleCondition = document.getElementById('ruleCondition');
        const ruleValue = document.getElementById('ruleValue');
        const ruleAction = document.getElementById('ruleAction');
        
        if (!ruleField || !ruleCondition || !ruleValue || !ruleAction) {
            showTestResult(false, 'No se pudieron obtener los campos del formulario de reglas.');
            return;
        }
        
        // Validar que los campos tienen valores
        if (!ruleField.value || !ruleCondition.value || !ruleValue.value || !ruleAction.value) {
            showTestResult(false, 'Por favor, complete todos los campos de la regla antes de probarla.');
            return;
        }
        
        // Obtener los datos de prueba según el campo seleccionado
        const datosPrueba = {};
        
        switch(ruleField.value) {
            case 'ASUNTO':
                if (!testSubject || !testSubject.value.trim()) {
                    showTestResult(false, 'Por favor, ingrese un asunto de prueba.');
                    return;
                }
                datosPrueba.asunto = testSubject.value.trim();
                break;
            case 'REMITENTE':
                if (!testSender || !testSender.value.trim()) {
                    showTestResult(false, 'Por favor, ingrese un remitente de prueba.');
                    return;
                }
                datosPrueba.remitente = testSender.value.trim();
                break;
            case 'DESTINATARIO':
                if (!testRecipient || !testRecipient.value.trim()) {
                    showTestResult(false, 'Por favor, ingrese un destinatario de prueba.');
                    return;
                }
                datosPrueba.destinatario = testRecipient.value.trim();
                break;
            case 'CONTENIDO':
                if (!testContent || !testContent.value.trim()) {
                    showTestResult(false, 'Por favor, ingrese un contenido de prueba.');
                    return;
                }
                datosPrueba.contenido = testContent.value.trim();
                break;
            case 'ADJUNTO':
                if (!testAttachment || !testAttachment.value.trim()) {
                    showTestResult(false, 'Por favor, ingrese un nombre de adjunto de prueba.');
                    return;
                }
                datosPrueba.adjunto = testAttachment.value.trim();
                break;
            default:
                showTestResult(false, 'Campo no reconocido.');
                return;
        }
        
        // Mostrar estado de carga
        showTestingState();
        
        // Crear objeto con datos de la regla
        const regla = {
            campo: ruleField.value,
            condicion: ruleCondition.value,
            valor: ruleValue.value,
            accion: ruleAction.value
        };
        
        // Obtener el token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Hacer la petición para probar la regla
        fetch('/ingesta-correo/api/reglas/test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                regla: regla,
                datos_prueba: datosPrueba
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la petición');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Mostrar resultado
                const resultado = data.resultado;
                showTestResult(
                    resultado.cumple, 
                    resultado.mensaje, 
                    resultado.accion
                );
            } else {
                showTestResult(false, data.message || 'Error al probar la regla.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showTestResult(false, 'Error de conexión al probar la regla.');
        });
    }
    
    /**
     * Muestra el estado de carga durante la prueba
     */
    function showTestingState() {
        if (!testResultContainer || !testResult || !testMessage || !testAction) return;
        
        testResultContainer.style.display = 'block';
        testResult.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Probando...';
        testResult.className = 'alert alert-info';
        testMessage.style.display = 'none';
        testAction.style.display = 'none';
    }
    
    /**
     * Muestra el resultado de la prueba
     */
    function showTestResult(cumple, mensaje, accion) {
        if (!testResultContainer || !testResult || !testMessage || !testAction) return;
        
        testResultContainer.style.display = 'block';
        
        if (cumple) {
            testResult.innerHTML = '<i class="fas fa-check-circle"></i> ¡La regla se cumple!';
            testResult.className = 'alert alert-success';
        } else {
            testResult.innerHTML = '<i class="fas fa-times-circle"></i> La regla no se cumple';
            testResult.className = 'alert alert-danger';
        }
        
        testMessage.textContent = mensaje;
        testMessage.style.display = 'block';
        
        if (accion && cumple) {
            const accionDisplay = {
                'PROCESAR': 'Procesar',
                'IGNORAR': 'Ignorar',
                'ARCHIVAR': 'Archivar',
                'ETIQUETAR': 'Etiquetar'
            }[accion] || accion;
            
            testAction.textContent = `Acción a ejecutar: ${accionDisplay}`;
            testAction.style.display = 'block';
        } else {
            testAction.style.display = 'none';
        }
    }
    
    /**
     * Actualiza los campos de prueba visibles según el campo seleccionado
     */
    function updateTestFields() {
        const ruleField = document.getElementById('ruleField');
        if (!ruleField || !testRuleSection) return;
        
        // Mostrar la sección de prueba
        testRuleSection.style.display = 'block';
        
        // Ocultar todos los campos de prueba
        const testFields = testRuleSection.querySelectorAll('.test-field');
        testFields.forEach(field => {
            field.style.display = 'none';
        });
        
        // Mostrar solo el campo relevante según la selección
        switch(ruleField.value) {
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
            case 'ADJUNTO':
                document.getElementById('testAttachmentField').style.display = 'block';
                break;
            default:
                testRuleSection.style.display = 'none';
                break;
        }
        
        // Ocultar el resultado anterior
        if (testResultContainer) {
            testResultContainer.style.display = 'none';
        }
    }
    
    // Event listener para cambios en el campo de la regla
    const ruleField = document.getElementById('ruleField');
    if (ruleField) {
        ruleField.addEventListener('change', updateTestFields);
        
        // Actualizar campos al cargar la página
        updateTestFields();
    }
});