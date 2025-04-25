/**
 * Script para probar reglas de filtrado de correos
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Iniciando script reglas_test.js");
    
    // Botón para probar regla
    const btnTestRule = document.getElementById('btnTestRule');
    if (btnTestRule) {
        btnTestRule.addEventListener('click', function() {
            testCurrentRule();
        });
    }
    
    // Función principal para probar la regla actual
    function testCurrentRule() {
        console.log("Probando regla actual");
        
        // Obtener datos de la regla del formulario
        const ruleData = {
            campo: document.getElementById('ruleField').value,
            condicion: document.getElementById('ruleCondition').value,
            valor: document.getElementById('ruleValue').value,
            // Para reglas existentes, incluir el ID
            regla_id: document.getElementById('ruleId').value || null
        };
        
        // Obtener datos de prueba según el campo seleccionado
        let testValue = '';
        switch (ruleData.campo) {
            case 'ASUNTO':
                testValue = document.getElementById('testSubject').value;
                break;
            case 'REMITENTE':
                testValue = document.getElementById('testSender').value;
                break;
            case 'DESTINATARIO':
                testValue = document.getElementById('testRecipient').value;
                break;
            case 'CONTENIDO':
                testValue = document.getElementById('testContent').value;
                break;
            case 'ADJUNTO_NOMBRE':
                testValue = document.getElementById('testAttachment').value;
                break;
        }
        
        // Validar que se ingresó un valor de prueba
        if (!testValue) {
            showTestError('Por favor ingrese un valor para probar la regla');
            return;
        }
        
        // Preparar datos de prueba
        const testData = {
            regla: ruleData,
            datos_prueba: {
                asunto: ruleData.campo === 'ASUNTO' ? testValue : '',
                remitente: ruleData.campo === 'REMITENTE' ? testValue : '',
                destinatario: ruleData.campo === 'DESTINATARIO' ? testValue : '',
                contenido: ruleData.campo === 'CONTENIDO' ? testValue : '',
                adjunto_nombre: ruleData.campo === 'ADJUNTO_NOMBRE' ? testValue : ''
            }
        };
        
        // CSRF token
        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Mostrar estado de carga
        const testResultContainer = document.getElementById('testResultContainer');
        const testResult = document.getElementById('testResult');
        const testMessage = document.getElementById('testMessage');
        const testAction = document.getElementById('testAction');
        
        if (testResultContainer) testResultContainer.style.display = 'block';
        if (testResult) {
            testResult.classList.remove('alert-success', 'alert-danger');
            testResult.classList.add('alert-info');
            testResult.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Probando regla...';
        }
        if (testMessage) testMessage.textContent = '';
        if (testAction) testAction.textContent = '';
        
        // Enviar solicitud al servidor
        fetch('/ingesta-correo/api/reglas/test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(testData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(response => {
            // Procesar resultado
            const matches = response.resultado;
            
            if (matches) {
                // La regla coincide
                if (testResult) {
                    testResult.classList.remove('alert-info', 'alert-danger');
                    testResult.classList.add('alert-success');
                    testResult.innerHTML = '<i class="fas fa-check-circle me-2"></i> ¡La regla coincide!';
                }
                
                if (testMessage) {
                    testMessage.textContent = 'El valor de prueba cumple con la condición de la regla.';
                }
                
                // Mostrar acción que se aplicaría
                const accion = document.getElementById('ruleAction').value;
                let accionText = 'Se aplicaría la acción: ';
                
                switch (accion) {
                    case 'PROCESAR':
                        accionText += 'Procesar automáticamente';
                        break;
                    case 'IGNORAR':
                        accionText += 'Ignorar correo';
                        break;
                    case 'MARCAR_REVISION':
                        accionText += 'Marcar para revisión';
                        break;
                    case 'MOVER_CARPETA':
                        accionText += 'Mover a carpeta';
                        break;
                    case 'ASIGNAR_ETIQUETA':
                        accionText += 'Asignar etiqueta';
                        break;
                    case 'REDIRIGIR':
                        accionText += 'Redirigir correo';
                        break;
                    default:
                        accionText += accion;
                }
                
                if (testAction) testAction.textContent = accionText;
            } else {
                // La regla no coincide
                if (testResult) {
                    testResult.classList.remove('alert-info', 'alert-success');
                    testResult.classList.add('alert-danger');
                    testResult.innerHTML = '<i class="fas fa-times-circle me-2"></i> La regla no coincide';
                }
                
                if (testMessage) {
                    testMessage.textContent = 'El valor de prueba no cumple con la condición de la regla.';
                }
                
                if (testAction) testAction.textContent = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showTestError('Ha ocurrido un error al probar la regla');
        });
    }
    
    // Mostrar error en la sección de prueba
    function showTestError(message) {
        const testResultContainer = document.getElementById('testResultContainer');
        const testResult = document.getElementById('testResult');
        const testMessage = document.getElementById('testMessage');
        const testAction = document.getElementById('testAction');
        
        if (testResultContainer) testResultContainer.style.display = 'block';
        
        if (testResult) {
            testResult.classList.remove('alert-info', 'alert-success');
            testResult.classList.add('alert-danger');
            testResult.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i> Error';
        }
        
        if (testMessage) testMessage.textContent = message;
        if (testAction) testAction.textContent = '';
    }
    
    // Vincular la función global de prueba
    window.testRule = testCurrentRule;
}); 