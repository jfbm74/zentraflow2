/**
 * Funciones específicas para probar reglas de filtrado
 * Este archivo contiene la implementación de la funcionalidad de prueba de reglas
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Iniciando script reglas_test.js");

    // Inicializar sección de prueba al abrir el modal
    const ruleModal = document.getElementById('ruleModal');
    const testRuleSection = document.getElementById('testRuleSection');

    if (ruleModal && testRuleSection) {
        ruleModal.addEventListener('shown.bs.modal', function () {
            // Si es una regla existente, configurar el estado inicial de la sección de prueba
            if (document.getElementById('ruleId').value) {
                testRuleSection.style.display = 'block';
                setupTestFields(document.getElementById('ruleField').value);
            } else {
                testRuleSection.style.display = 'none';
            }
        });
    }

    // Manejar cambios en el campo de la regla para actualizar los campos de prueba
    const ruleFieldSelect = document.getElementById('ruleField');
    if (ruleFieldSelect) {
        ruleFieldSelect.addEventListener('change', function() {
            setupTestFields(this.value);
            // Mostrar sección de prueba
            if (testRuleSection) {
                testRuleSection.style.display = 'block';
            }
        });
    }

    // Configurar el botón de prueba
    const testRuleButton = document.getElementById('btnTestRule');
    if (testRuleButton) {
        testRuleButton.addEventListener('click', testRuleImplementation);
    }
});

/**
 * Configura los campos de prueba según el campo seleccionado
 * @param {string} selectedField - El campo seleccionado para la regla
 */
window.setupTestFields = function(selectedField) {
    console.log(`Configurando campos de prueba para: ${selectedField}`);
    
    const testFieldContainer = document.getElementById('testFieldContainer');
    if (!testFieldContainer) {
        console.error('No se encontró el contenedor de campos de prueba');
        return;
    }
    
    // Limpiar el contenedor
    testFieldContainer.innerHTML = '';
    
    let inputField;
    
    switch (selectedField) {
        case 'asunto':
            // Campo para probar asunto
            inputField = document.createElement('input');
            inputField.type = 'text';
            inputField.id = 'testSubject';
            inputField.name = 'testSubject';
            inputField.className = 'form-control';
            inputField.placeholder = 'Ingrese un asunto de prueba';
            
            const subjectLabel = document.createElement('label');
            subjectLabel.htmlFor = 'testSubject';
            subjectLabel.textContent = 'Asunto de prueba:';
            
            const subjectGroup = document.createElement('div');
            subjectGroup.className = 'mb-3';
            subjectGroup.appendChild(subjectLabel);
            subjectGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(subjectGroup);
            break;
            
        case 'remitente':
            // Campo para probar remitente
            inputField = document.createElement('input');
            inputField.type = 'email';
            inputField.id = 'testSender';
            inputField.name = 'testSender';
            inputField.className = 'form-control';
            inputField.placeholder = 'correo@ejemplo.com';
            
            const senderLabel = document.createElement('label');
            senderLabel.htmlFor = 'testSender';
            senderLabel.textContent = 'Remitente de prueba:';
            
            const senderGroup = document.createElement('div');
            senderGroup.className = 'mb-3';
            senderGroup.appendChild(senderLabel);
            senderGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(senderGroup);
            break;
            
        case 'destinatario':
            // Campo para probar destinatario
            inputField = document.createElement('input');
            inputField.type = 'email';
            inputField.id = 'testRecipient';
            inputField.name = 'testRecipient';
            inputField.className = 'form-control';
            inputField.placeholder = 'destinatario@ejemplo.com';
            
            const recipientLabel = document.createElement('label');
            recipientLabel.htmlFor = 'testRecipient';
            recipientLabel.textContent = 'Destinatario de prueba:';
            
            const recipientGroup = document.createElement('div');
            recipientGroup.className = 'mb-3';
            recipientGroup.appendChild(recipientLabel);
            recipientGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(recipientGroup);
            break;
            
        case 'contenido':
            // Campo para probar contenido
            inputField = document.createElement('textarea');
            inputField.id = 'testContent';
            inputField.name = 'testContent';
            inputField.className = 'form-control';
            inputField.placeholder = 'Ingrese el contenido de prueba';
            inputField.rows = 4;
            
            const contentLabel = document.createElement('label');
            contentLabel.htmlFor = 'testContent';
            contentLabel.textContent = 'Contenido de prueba:';
            
            const contentGroup = document.createElement('div');
            contentGroup.className = 'mb-3';
            contentGroup.appendChild(contentLabel);
            contentGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(contentGroup);
            break;
            
        case 'nombre_adjunto':
            // Campo para probar nombre de adjunto
            inputField = document.createElement('input');
            inputField.type = 'text';
            inputField.id = 'testAttachmentName';
            inputField.name = 'testAttachmentName';
            inputField.className = 'form-control';
            inputField.placeholder = 'documento.pdf';
            
            const attachmentLabel = document.createElement('label');
            attachmentLabel.htmlFor = 'testAttachmentName';
            attachmentLabel.textContent = 'Nombre de adjunto de prueba:';
            
            const attachmentGroup = document.createElement('div');
            attachmentGroup.className = 'mb-3';
            attachmentGroup.appendChild(attachmentLabel);
            attachmentGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(attachmentGroup);
            break;
            
        case 'tiene_adjuntos':
            // Campo para probar si tiene adjuntos
            inputField = document.createElement('select');
            inputField.id = 'testHasAttachments';
            inputField.name = 'testHasAttachments';
            inputField.className = 'form-select';
            
            const optionYes = document.createElement('option');
            optionYes.value = 'true';
            optionYes.textContent = 'Sí';
            
            const optionNo = document.createElement('option');
            optionNo.value = 'false';
            optionNo.textContent = 'No';
            
            inputField.appendChild(optionYes);
            inputField.appendChild(optionNo);
            
            const hasAttachmentsLabel = document.createElement('label');
            hasAttachmentsLabel.htmlFor = 'testHasAttachments';
            hasAttachmentsLabel.textContent = '¿Tiene adjuntos?:';
            
            const hasAttachmentsGroup = document.createElement('div');
            hasAttachmentsGroup.className = 'mb-3';
            hasAttachmentsGroup.appendChild(hasAttachmentsLabel);
            hasAttachmentsGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(hasAttachmentsGroup);
            break;
            
        case 'fecha_recibido':
            // Campo para probar fecha de recibido
            inputField = document.createElement('input');
            inputField.type = 'datetime-local';
            inputField.id = 'testReceivedDate';
            inputField.name = 'testReceivedDate';
            inputField.className = 'form-control';
            
            // Establecer fecha actual como valor predeterminado
            const now = new Date();
            const dateString = now.toISOString().slice(0, 16);
            inputField.value = dateString;
            
            const dateLabel = document.createElement('label');
            dateLabel.htmlFor = 'testReceivedDate';
            dateLabel.textContent = 'Fecha de recibido:';
            
            const dateGroup = document.createElement('div');
            dateGroup.className = 'mb-3';
            dateGroup.appendChild(dateLabel);
            dateGroup.appendChild(inputField);
            
            testFieldContainer.appendChild(dateGroup);
            break;
            
        default:
            // Mensaje de error para campo no reconocido
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning';
            alertDiv.textContent = `Campo no soportado para pruebas: ${selectedField}`;
            testFieldContainer.appendChild(alertDiv);
            break;
    }
    
    // Crear el área de resultados
    const resultContainer = document.getElementById('testResultContainer');
    if (resultContainer) {
        resultContainer.innerHTML = '';
    }
};

/**
 * Implementación principal para probar reglas
 * Esta función es llamada desde el botón de prueba y también desde reglas_common.js
 */
window.testRuleImplementation = function() {
    console.log("Ejecutando prueba de regla");
    
    // Obtener datos del formulario
    const ruleId = document.getElementById('ruleId').value;
    const campo = document.getElementById('ruleField').value;
    const condicion = document.getElementById('ruleCondition').value;
    const valor = document.getElementById('ruleValue').value;
    
    if (!campo || !condicion) {
        showErrorMessage('Por favor seleccione campo y condición para realizar la prueba');
        return;
    }
    
    // Obtener el valor de prueba según el campo seleccionado
    let valorPrueba = '';
    switch (campo) {
        case 'asunto':
            valorPrueba = document.getElementById('testSubject')?.value || '';
            break;
        case 'remitente':
            valorPrueba = document.getElementById('testSender')?.value || '';
            break;
        case 'destinatario':
            valorPrueba = document.getElementById('testRecipient')?.value || '';
            break;
        case 'contenido':
            valorPrueba = document.getElementById('testContent')?.value || '';
            break;
        case 'nombre_adjunto':
            valorPrueba = document.getElementById('testAttachmentName')?.value || '';
            break;
        case 'tiene_adjuntos':
            valorPrueba = document.getElementById('testHasAttachments')?.value === 'true';
            break;
        case 'fecha_recibido':
            valorPrueba = document.getElementById('testReceivedDate')?.value || '';
            break;
        default:
            showErrorMessage(`Campo no soportado para pruebas: ${campo}`);
            return;
    }
    
    if (valorPrueba === '' && campo !== 'tiene_adjuntos') {
        showErrorMessage('Por favor ingrese un valor de prueba');
        return;
    }
    
    // CSRF token
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Datos para la prueba
    const datosPrueba = {
        campo: campo,
        condicion: condicion,
        valor: valor,
        valor_prueba: valorPrueba
    };
    
    // Si es una regla existente, usamos su ID
    if (ruleId) {
        datosPrueba.regla_id = ruleId;
    }
    
    console.log('Datos de prueba:', datosPrueba);
    
    // Mostrar indicador de carga
    const resultContainer = document.getElementById('testResultContainer');
    if (resultContainer) {
        resultContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p class="mt-2">Probando regla...</p></div>';
    }
    
    // Ejecutar la prueba
    fetch('/ingesta-correo/api/reglas/test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(datosPrueba)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Respuesta de prueba:', data);
        
        // Mostrar resultados
        if (resultContainer) {
            let alertClass = data.cumple ? 'alert-success' : 'alert-danger';
            let iconClass = data.cumple ? 'fa-check-circle' : 'fa-times-circle';
            let resultText = data.cumple ? 'CUMPLE' : 'NO CUMPLE';
            
            resultContainer.innerHTML = `
                <div class="alert ${alertClass} mt-3">
                    <div class="d-flex align-items-center">
                        <div class="me-3">
                            <i class="fas ${iconClass} fa-2x"></i>
                        </div>
                        <div>
                            <h5 class="mb-1">La regla ${resultText} con el valor de prueba</h5>
                            <p class="mb-0">${data.mensaje || ''}</p>
                        </div>
                    </div>
                </div>`;
            
            // Explicación detallada
            if (data.explicacion) {
                const explicacionDiv = document.createElement('div');
                explicacionDiv.className = 'card mt-3';
                
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header';
                cardHeader.innerHTML = '<h6 class="mb-0">Explicación de la evaluación</h6>';
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                cardBody.textContent = data.explicacion;
                
                explicacionDiv.appendChild(cardHeader);
                explicacionDiv.appendChild(cardBody);
                
                resultContainer.appendChild(explicacionDiv);
            }
        }
    })
    .catch(error => {
        console.error('Error en la prueba:', error);
        
        // Mostrar error
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="alert alert-danger mt-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error al probar la regla: ${error.message}
                </div>`;
        }
    });
}; 