// Mejoras de UX para la experiencia de login de Zentraflow
document.addEventListener('DOMContentLoaded', function() {
    // Animación de entrada para elementos del formulario
    const formElements = document.querySelectorAll('.login-form-container > *');
    formElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });
    
    // Efecto de partículas para el panel izquierdo (decorativo)
    const brandPanel = document.querySelector('.illustration-container');
    if (brandPanel) {
        createParticleEffect(brandPanel);
    }
    
    // Animación de pulso para el botón de login
    const loginButton = document.querySelector('button[type="submit"]');
    if (loginButton) {
        setTimeout(() => {
            loginButton.classList.add('pulse-animation');
        }, 1500);
    }
    
    // Validación mejorada del formulario
    const emailInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            validateEmail(this);
        });
    }
    
    // Detección de carga completada
    window.addEventListener('load', function() {
        document.body.classList.add('loaded');
    });
    
    // Para la página de restablecimiento de contraseña
    const newPasswordElement = document.getElementById('password-text');
    if (newPasswordElement) {
        highlightPasswordStrength(newPasswordElement.innerText);
    }
});

// Función para crear efecto de partículas
function createParticleEffect(container) {
    // Crear canvas para las partículas
    const canvas = document.createElement('canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.opacity = '0.3';
    canvas.style.pointerEvents = 'none';
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    // Ajustar el tamaño del canvas al contenedor
    function resizeCanvas() {
        canvas.width = container.offsetWidth;
        canvas.height = container.offsetHeight;
    }
    
    // Crear partículas
    let particles = [];
    const particleCount = 30;
    const colors = ['#2bae66', '#0387c2', '#ffffff'];
    
    function createParticles() {
        particles = [];
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 3 + 1,
                color: colors[Math.floor(Math.random() * colors.length)],
                speed: {
                    x: (Math.random() - 0.5) * 0.5,
                    y: (Math.random() - 0.5) * 0.5
                }
            });
        }
    }
    
    // Animar partículas
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
            
            // Mover partículas
            p.x += p.speed.x;
            p.y += p.speed.y;
            
            // Rebotar en los bordes
            if (p.x < 0 || p.x > canvas.width) p.speed.x *= -1;
            if (p.y < 0 || p.y > canvas.height) p.speed.y *= -1;
        }
        
        // Conectar partículas cercanas
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const distance = Math.sqrt(
                    Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2)
                );
                
                if (distance < 100) {
                    ctx.beginPath();
                    ctx.strokeStyle = p1.color;
                    ctx.globalAlpha = 1 - (distance / 100);
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        }
        
        requestAnimationFrame(animateParticles);
    }
    
    // Iniciar el efecto
    window.addEventListener('resize', () => {
        resizeCanvas();
        createParticles();
    });
    
    resizeCanvas();
    createParticles();
    animateParticles();
}

// Función para validar formato de email
function validateEmail(input) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailPattern.test(input.value);
    
    if (input.value.length > 0 && !isValid) {
        input.classList.add('is-invalid');
        const feedback = input.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = 'Por favor ingresa un correo electrónico válido.';
        }
    } else {
        input.classList.remove('is-invalid');
    }
    
    return isValid;
}

// Función para mostrar la fortaleza de la contraseña
function highlightPasswordStrength(password) {
    const strengthElement = document.createElement('div');
    strengthElement.className = 'password-strength mt-2';
    
    let strength = 0;
    let strengthClass = '';
    let strengthText = '';
    
    // Criterios de fortaleza
    if (password.length >= 8) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^A-Za-z0-9]/)) strength++;
    
    // Determinar la clase y texto según la fortaleza
    switch(strength) {
        case 0:
        case 1:
            strengthClass = 'text-danger';
            strengthText = 'Débil';
            break;
        case 2:
        case 3:
            strengthClass = 'text-warning';
            strengthText = 'Moderada';
            break;
        case 4:
        case 5:
            strengthClass = 'text-success';
            strengthText = 'Fuerte';
            break;
    }
    
    // Crear el indicador visual
    strengthElement.innerHTML = `
        <small class="${strengthClass}">
            <i class="fas ${strength >= 4 ? 'fa-shield-alt' : 'fa-info-circle'}"></i>
            Seguridad de la contraseña: <strong>${strengthText}</strong>
        </small>
        <div class="progress" style="height: 5px;">
            <div class="progress-bar bg-${strengthClass.replace('text-', '')}" 
                 style="width: ${(strength/5)*100}%"></div>
        </div>
    `;
    
    // Insertar después del elemento de contraseña
    const passwordContainer = document.querySelector('.password-display');
    if (passwordContainer && !document.querySelector('.password-strength')) {
        passwordContainer.parentNode.insertBefore(strengthElement, passwordContainer.nextSibling);
    }
}