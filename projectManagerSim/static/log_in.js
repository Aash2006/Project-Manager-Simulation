document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const button = document.getElementById('loginBtn');
    const inputs = document.querySelectorAll('.form-input');

    // Add input validation
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });

        input.addEventListener('input', function() {
            this.classList.remove('is-invalid', 'is-valid');
        });
    });

    // Form submission with loading state
    form.addEventListener('submit', function() {
        button.disabled = true;
        button.classList.add('loading');
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Signing In...';
    });

    // Auto-focus username field
    const usernameField = document.querySelector('input[name="username"]');
    if (usernameField) {
        usernameField.focus();
    }
});