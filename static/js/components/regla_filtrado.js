// Funciones para manejar las reglas de filtrado
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const toggleButtons = document.querySelectorAll('.toggle-rule');
    const deleteButtons = document.querySelectorAll('.delete-rule');
    const testButtons = document.querySelectorAll('.test-rule');
    
    // Función para mostrar mensajes
    function showMessage(message, type = 'success') {
        // Buscar el contenedor de mensajes
        let messagesContainer = document.querySelector('.messages-container');
        
        // Si no existe, crear uno al inicio del contenido principal
        if (!messagesContainer) {
            messagesContainer = document.createElement('div');
            messagesContainer.className = 'messages-container';
            
            // Intentar insertar al principio del contenido principal
            const contentMain = document.querySelector('.container-fluid') || document.body;
            if (contentMain.firstChild) {
                contentMain.insertBefore(messagesContainer, contentMain.firstChild);
            } else {
                contentMain.appendChild(messagesContainer);
            }
        }
        
        // Crear la alerta
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        messagesContainer.appendChild(alertDiv);
        
        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
        
        // También mostrar en la consola
        console.log(`Mensaje: ${message} (${type})`);
    }
    
    // Función para activar/desactivar una regla
    function toggleRuleState(button) {
        const reglaId = button.dataset.reglaId || button.getAttribute('data-id');
        if (!reglaId) {
            console.error('No se pudo obtener el ID de la regla');
            return;
        }
        
        const url = `/ingesta-correo/reglas/${reglaId}/toggle/`;
        console.log(`Enviando petición a: ${url}`);
        
        // Deshabilitar el botón mientras se procesa
        button.disabled = true;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data);
            if (data.success) {
                // Actualizar el estado visual del botón
                const isActive = data.activo;
                button.innerHTML = isActive ? 
                    '<i class="fas fa-toggle-on"></i> Activa' : 
                    '<i class="fas fa-toggle-off"></i> Inactiva';
                button.classList.toggle('btn-success', isActive);
                button.classList.toggle('btn-secondary', !isActive);
                
                // Actualizar el estado en la interfaz si existe
                const estadoLabel = document.querySelector(`[data-regla-estado="${reglaId}"]`);
                if (estadoLabel) {
                    estadoLabel.textContent = isActive ? 'Activa' : 'Inactiva';
                    estadoLabel.className = isActive ? 'badge bg-success' : 'badge bg-secondary';
                }
                
                showMessage(data.message || 'Estado de la regla actualizado correctamente', 'success');
            } else {
                showMessage(data.message || 'Error al actualizar el estado de la regla', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Error al comunicarse con el servidor', 'danger');
        })
        .finally(() => {
            // Re-habilitar el botón
            button.disabled = false;
        });
    }
    
    // Función para eliminar una regla
    function deleteRule(button) {
        const reglaId = button.dataset.reglaId || button.getAttribute('data-id');
        if (!reglaId) {
            console.error('No se pudo obtener el ID de la regla');
            return;
        }
        
        const regresar = button.dataset.returnUrl || '/ingesta-correo/reglas/';
        
        if (confirm('¿Estás seguro de que deseas eliminar esta regla?')) {
            // Deshabilitar botón mientras se procesa
            button.disabled = true;
            
            // URL directa al endpoint de eliminación - verificar en urls.py
            const url = `/ingesta-correo/api/reglas/${reglaId}/`;
            console.log(`Enviando petición DELETE a: ${url}`);
            
            fetch(url, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Respuesta del servidor:', data);
                if (data.success) {
                    showMessage(data.message || 'Regla eliminada correctamente', 'success');
                    // Redirigir después de un breve delay
                    setTimeout(() => {
                        window.location.href = regresar;
                    }, 1000);
                } else {
                    showMessage(data.message || 'Error al eliminar la regla', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage(`Error al eliminar: ${error.message}`, 'danger');
            })
            .finally(() => {
                // Re-habilitar el botón
                button.disabled = false;
            });
        }
    }
    
    // Función para probar una regla
    function testRule(button) {
        const reglaId = button.dataset.reglaId || button.getAttribute('data-id');
        if (!reglaId) {
            console.error('No se pudo obtener el ID de la regla');
            return;
        }
        
        const form = document.getElementById('testForm');
        if (!form) {
            console.error('No se pudo encontrar el formulario de prueba');
            return;
        }
        
        const url = `/ingesta-correo/reglas/${reglaId}/test/`;
        console.log(`Enviando petición a: ${url}`);
        
        const formData = new FormData(form);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Respuesta del servidor:', data);
            const resultContainer = document.getElementById('testResults');
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="alert alert-${data.cumple ? 'success' : 'warning'}">
                        <h5 class="alert-heading">
                            ${data.cumple ? 
                                '<i class="fas fa-check-circle"></i> La regla coincide' : 
                                '<i class="fas fa-times-circle"></i> La regla no coincide'}
                        </h5>
                        <p>${data.mensaje}</p>
                    </div>
                `;
                resultContainer.scrollIntoView({ behavior: 'smooth' });
            } else {
                console.error('No se encontró el contenedor de resultados');
                showMessage(data.mensaje, data.cumple ? 'success' : 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Error al probar la regla', 'danger');
        });
    }
    
    // Función para obtener el token CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Asignar eventos a los botones
    toggleButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            toggleRuleState(button);
        });
    });
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            deleteRule(button);
        });
    });
    
    testButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            testRule(button);
        });
    });
    
    // Exponer funciones globalmente para uso en atributos onclick
    window.toggleRuleState = toggleRuleState;
    window.deleteRule = deleteRule;
    window.testRule = testRule;
}); 
}); 