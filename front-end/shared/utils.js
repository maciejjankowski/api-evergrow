// Evergrow360 App Utilities
(function() {
    'use strict';

    // Global app namespace
    window.Evergrow360 = window.Evergrow360 || {};

    // Utility functions
    const Utils = {
        // DOM helpers
        $: function(selector) {
            return document.querySelector(selector);
        },

        $$: function(selector) {
            return document.querySelectorAll(selector);
        },

        createElement: function(tag, className, text) {
            const element = document.createElement(tag);
            if (className) element.className = className;
            if (text) element.textContent = text;
            return element;
        },

        // Form validation
        validateEmail: function(email) {
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return regex.test(email);
        },

        validateRequired: function(value) {
            return value && value.trim().length > 0;
        },

        validatePassword: function(password) {
            // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
            const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
            return regex.test(password);
        },

        // Show form errors
        showFieldError: function(field, message) {
            this.hideFieldError(field);
            field.classList.add('error');
            
            const errorElement = this.createElement('div', 'form-error', message);
            field.parentNode.appendChild(errorElement);
        },

        hideFieldError: function(field) {
            field.classList.remove('error');
            const errorElement = field.parentNode.querySelector('.form-error');
            if (errorElement) {
                errorElement.remove();
            }
        },

        // Local storage helpers
        setStorage: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Storage error:', e);
                return false;
            }
        },

        getStorage: function(key) {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : null;
            } catch (e) {
                console.error('Storage error:', e);
                return null;
            }
        },

        removeStorage: function(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('Storage error:', e);
                return false;
            }
        },

        // HTTP helpers
        request: function(url, options = {}) {
            const defaults = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            const config = Object.assign(defaults, options);

            return fetch(url, config)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('Request error:', error);
                    throw error;
                });
        },

        // Date helpers
        formatDate: function(date) {
            return new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        },

        formatTime: function(date) {
            return new Date(date).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit'
            });
        },

        formatDateTime: function(date) {
            return `${this.formatDate(date)} at ${this.formatTime(date)}`;
        },

        // Currency helpers
        formatCurrency: function(amount, currency = 'EUR') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        // Loading states
        showLoading: function(element, text = 'Loading...') {
            element.innerHTML = `
                <div class="flex-center">
                    <div class="loading-spinner"></div>
                    <span class="ml-2">${text}</span>
                </div>
            `;
            element.disabled = true;
        },

        hideLoading: function(element, originalText) {
            element.innerHTML = originalText;
            element.disabled = false;
        },

        // Notifications
        showNotification: function(message, type = 'info') {
            const notification = this.createElement('div', `notification notification-${type}`, message);
            document.body.appendChild(notification);

            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        },

        // Progress tracking
        updateProgress: function(element, percentage) {
            const progressFill = element.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = `${percentage}%`;
            }
        },

        // Modal helpers
        openModal: function(modalId) {
            const modal = this.$(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        },

        closeModal: function(modalId) {
            const modal = this.$(modalId);
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        },

        // Tab management
        switchTab: function(tabId, contentId) {
            // Hide all tab contents
            this.$$('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });

            // Remove active class from all tabs
            this.$$('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected content and activate tab
            const content = this.$(contentId);
            const tab = this.$(tabId);

            if (content) content.classList.remove('hidden');
            if (tab) tab.classList.add('active');
        },

        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Generate UUID
        generateUUID: function() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
    };

    // Modal management
    const Modal = {
        init: function() {
            // Close modals when clicking overlay
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('modal-overlay')) {
                    e.target.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });

            // Close modals with Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const activeModal = Utils.$('.modal-overlay.active');
                    if (activeModal) {
                        activeModal.classList.remove('active');
                        document.body.style.overflow = '';
                    }
                }
            });
        }
    };

    // Form validation management
    const FormValidator = {
        init: function() {
            document.addEventListener('submit', function(e) {
                const form = e.target;
                if (form.hasAttribute('data-validate')) {
                    e.preventDefault();
                    FormValidator.validateForm(form);
                }
            });

            // Real-time validation
            document.addEventListener('blur', function(e) {
                const field = e.target;
                if (field.hasAttribute('data-validate')) {
                    FormValidator.validateField(field);
                }
            }, true);
        },

        validateForm: function(form) {
            const fields = form.querySelectorAll('[data-validate]');
            let isValid = true;

            fields.forEach(field => {
                if (!this.validateField(field)) {
                    isValid = false;
                }
            });

            if (isValid) {
                // Submit form or call success handler
                const onSuccess = form.getAttribute('data-success');
                if (onSuccess && window[onSuccess]) {
                    window[onSuccess](form);
                } else {
                    form.submit();
                }
            }
        },

        validateField: function(field) {
            const rules = field.getAttribute('data-validate').split('|');
            let isValid = true;

            Utils.hideFieldError(field);

            for (let rule of rules) {
                const [ruleName, ruleValue] = rule.split(':');

                switch (ruleName) {
                    case 'required':
                        if (!Utils.validateRequired(field.value)) {
                            Utils.showFieldError(field, 'This field is required');
                            isValid = false;
                        }
                        break;

                    case 'email':
                        if (field.value && !Utils.validateEmail(field.value)) {
                            Utils.showFieldError(field, 'Please enter a valid email address');
                            isValid = false;
                        }
                        break;

                    case 'password':
                        if (field.value && !Utils.validatePassword(field.value)) {
                            Utils.showFieldError(field, 'Password must be at least 8 characters with uppercase, lowercase, and number');
                            isValid = false;
                        }
                        break;

                    case 'minlength':
                        if (field.value && field.value.length < parseInt(ruleValue)) {
                            Utils.showFieldError(field, `Minimum length is ${ruleValue} characters`);
                            isValid = false;
                        }
                        break;

                    case 'match':
                        const matchField = Utils.$(`[name="${ruleValue}"]`);
                        if (matchField && field.value !== matchField.value) {
                            Utils.showFieldError(field, 'Passwords do not match');
                            isValid = false;
                        }
                        break;
                }

                if (!isValid) break;
            }

            return isValid;
        }
    };

    // Initialize modules when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        Modal.init();
        FormValidator.init();
        
        // Add loading spinner styles if not present
        if (!Utils.$('.loading-spinner')) {
            const style = document.createElement('style');
            style.textContent = `
                .loading-spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--slate-light);
                    border-top: 2px solid var(--gold-primary);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 1rem 1.5rem;
                    border-radius: var(--radius-md);
                    color: white;
                    font-weight: 500;
                    z-index: 1100;
                    animation: slideIn 0.3s ease;
                }
                
                .notification-info { background: var(--blue-accent); }
                .notification-success { background: var(--green-success); }
                .notification-warning { background: var(--warning-orange); }
                .notification-error { background: var(--error-red); }
                
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    });

    // Expose utilities globally
    window.Evergrow360.Utils = Utils;
    window.Evergrow360.Modal = Modal;
    window.Evergrow360.FormValidator = FormValidator;

})();