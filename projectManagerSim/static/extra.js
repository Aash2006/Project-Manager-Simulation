/**
 * Visual Effects JavaScript - Clean & Static Version
 */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.scroll-reveal');
    
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Elements just appear now, no sliding
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1
    });

    revealElements.forEach(element => {
        revealObserver.observe(element);
    });
}

function initNavbarScroll() {
    const navbar = document.querySelector('.navbar, .simple-nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, { passive: true });
    }
}

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width') || bar.style.width;
        if (width) {
            const numericWidth = parseInt(width);
            bar.style.width = width;

            bar.classList.remove('low-energy', 'medium-energy', 'high-energy');
            
            if (numericWidth < 30) {
                bar.classList.add('low-energy');
            } else if (numericWidth < 70) {
                bar.classList.add('medium-energy');
            } else {
                bar.classList.add('high-energy');
            }
        }
    });
}

function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border: 2px solid var(--primary-purple);
        padding: 1rem;
        z-index: 10000;
        box-shadow: var(--shadow-heavy);
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, duration);
}

function initVisualEffects() {
    initScrollReveal();
    initNavbarScroll();
    animateProgressBars();
    
    console.log('UI initialized (Static Mode)');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVisualEffects);
} else {
    initVisualEffects();
}

window.VisualEffects = {
    showNotification,
    animateProgressBars
};