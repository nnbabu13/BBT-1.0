/**
 * Custom JavaScript for Baccarat Oscar Grind Tracker
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enable all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add error message to form fields
    window.addErrorMessage = function(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('is-invalid');
            
            // Check if error message already exists
            let errorDiv = field.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                errorDiv = document.createElement('div');
                errorDiv.classList.add('invalid-feedback');
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
            
            errorDiv.textContent = message;
        }
    };

    // Reset confirmation modal
    window.confirmReset = function() {
        return confirm('Are you sure you want to reset your session? This will delete all bet history and return to the setup page.');
    };

    // Form validation for numerical inputs
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const min = parseFloat(this.min);
            
            if (isNaN(value) || value < min) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    });

    // Auto-focus on bet amount field in session page
    const betAmountField = document.getElementById('bet_amount');
    if (betAmountField) {
        betAmountField.focus();
    }
});