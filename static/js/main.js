// static/js/main.js

console.log("✅ MortgageDealsHub loaded");

document.addEventListener("DOMContentLoaded", () => {
  // ========================================
  // LTV Calculator (Homepage)
  // ========================================
  const propertyValueInput = document.querySelector('input[name="property_value"]');
  const depositInput = document.querySelector('input[name="deposit"]');
  const ltvOutput = document.getElementById('ltv-output');

  function calculateLTV() {
    if (!propertyValueInput || !depositInput || !ltvOutput) return;

    const propertyValue = parseFloat(propertyValueInput.value) || 0;
    const deposit = parseFloat(depositInput.value) || 0;

    if (propertyValue > 0 && deposit >= 0) {
      const loanAmount = propertyValue - deposit;
      const ltv = (loanAmount / propertyValue) * 100;
      ltvOutput.textContent = ltv.toFixed(1) + '%';

      // Color coding
      if (ltv <= 60) {
        ltvOutput.style.color = '#2e7d32'; // Green
      } else if (ltv <= 80) {
        ltvOutput.style.color = '#f57c00'; // Orange
      } else {
        ltvOutput.style.color = '#d32f2f'; // Red
      }
    }
  }

  // Attach event listeners
  if (propertyValueInput && depositInput) {
    propertyValueInput.addEventListener('input', calculateLTV);
    depositInput.addEventListener('input', calculateLTV);
    // Calculate on page load
    calculateLTV();
  }

  // ========================================
  // Form Validation Enhancement
  // ========================================
  const signupForm = document.querySelector("form.auth-form");

  if (signupForm) {
    const passwordInput = signupForm.querySelector('input[name="password"]');

    if (passwordInput) {
      passwordInput.addEventListener('input', () => {
        const password = passwordInput.value;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const isLongEnough = password.length >= 8;

        if (isLongEnough && hasUppercase && hasLowercase && hasNumber) {
          passwordInput.style.borderColor = '#2e7d32';
        } else {
          passwordInput.style.borderColor = '#d32f2f';
        }
      });
    }
  }

  // ========================================
  // Flash Message Auto-Dismiss
  // ========================================
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transition = 'opacity 0.5s';
      setTimeout(() => msg.remove(), 500);
    }, 5000); // Auto-dismiss after 5 seconds
  });

  // ========================================
  // Number Formatting for Inputs
  // ========================================
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach(input => {
    input.addEventListener('blur', () => {
      if (input.value) {
        const num = parseFloat(input.value);
        if (!isNaN(num) && num >= 0) {
          input.value = Math.round(num);
        }
      }
    });
  });

  // ========================================
  // Mobile Menu Toggle (if needed in future)
  // ========================================
  const mobileMenuButton = document.querySelector('.mobile-menu-toggle');
  const mainNav = document.querySelector('.main-nav');

  if (mobileMenuButton && mainNav) {
    mobileMenuButton.addEventListener('click', () => {
      mainNav.classList.toggle('active');
    });
  }

  console.log("✅ All enhancements loaded");
});

// Advanced Filters Toggle
function toggleAdvanced() {
    const content = document.getElementById('advanced-filters');
    const icon = document.getElementById('toggle-icon');

    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.textContent = '▲';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
    }
}
