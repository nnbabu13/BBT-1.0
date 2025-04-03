// Baccarat Oscar Grind Tracker - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Enable all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    const setupForm = document.getElementById('setupForm');
    if (setupForm) {
        setupForm.addEventListener('submit', function(event) {
            const bankroll = parseFloat(document.getElementById('bankroll').value);
            const baseBet = parseFloat(document.getElementById('base_bet').value);
            const profitTarget = parseFloat(document.getElementById('profit_target').value);
            
            let hasError = false;
            
            // Clear previous error messages
            document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
            document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            
            // Validate bankroll
            if (isNaN(bankroll) || bankroll <= 0) {
                addErrorMessage('bankroll', 'Bankroll must be a positive number');
                hasError = true;
            }
            
            // Validate base bet
            if (isNaN(baseBet) || baseBet <= 0) {
                addErrorMessage('base_bet', 'Base bet must be a positive number');
                hasError = true;
            }
            
            // Validate profit target
            if (isNaN(profitTarget) || profitTarget <= 0) {
                addErrorMessage('profit_target', 'Profit target must be a positive number');
                hasError = true;
            }
            
            // Validate base bet relative to bankroll
            if (baseBet > bankroll) {
                addErrorMessage('base_bet', 'Base bet cannot exceed starting bankroll');
                hasError = true;
            }
            
            if (hasError) {
                event.preventDefault();
            }
        });
    }
    
    // Bet form validation
    const betForm = document.getElementById('betForm');
    if (betForm) {
        betForm.addEventListener('submit', function(event) {
            const actualBet = parseFloat(document.getElementById('actual_bet').value);
            const result = document.getElementById('result').value;
            
            let hasError = false;
            
            // Clear previous error messages
            document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
            document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            
            // Validate bet amount
            if (isNaN(actualBet) || actualBet <= 0) {
                addErrorMessage('actual_bet', 'Bet amount must be a positive number');
                hasError = true;
            }
            
            // Validate result selection
            if (!result) {
                addErrorMessage('result', 'Please select a result');
                hasError = true;
            }
            
            if (hasError) {
                event.preventDefault();
            }
        });
        
        // Show warning if actual bet doesn't match suggested bet
        const actualBetInput = document.getElementById('actual_bet');
        const suggestedBet = parseFloat(actualBetInput.value);
        const betWarning = document.getElementById('betWarning');
        
        actualBetInput.addEventListener('input', function() {
            const currentValue = parseFloat(this.value);
            
            if (currentValue !== suggestedBet) {
                betWarning.style.display = 'block';
            } else {
                betWarning.style.display = 'none';
            }
        });
    }
    
    // Helper function to add error messages to form fields
    function addErrorMessage(fieldId, message) {
        const field = document.getElementById(fieldId);
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
    
    // Auto resize textarea if present
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Trigger on load
        textarea.dispatchEvent(new Event('input'));
    });
    
    // Format currency inputs to 2 decimal places on blur
    const currencyInputs = document.querySelectorAll('input[type="number"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
});

// Confirm before form submission for critical actions
function confirmReset() {
    return confirm('Are you sure you want to reset this session? All progress will be lost.');
}
