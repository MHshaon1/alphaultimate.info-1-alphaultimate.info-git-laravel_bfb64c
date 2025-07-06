// Alpha Ultimate Workdesk - Main JavaScript Application

(function() {
    'use strict';

    // Initialize application when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
    });

    function initializeApp() {
        // Initialize all components
        initializeFeatherIcons();
        initializeTooltips();
        initializeFormValidation();
        initializeAlerts();
        initializeNavigation();
        initializeFileUploads();
        initializeAutoCalculations();
        initializeDataTables();
        initializeModals();
        
        console.log('Alpha Ultimate Workdesk initialized successfully');
    }

    // Initialize Feather Icons
    function initializeFeatherIcons() {
        if (typeof feather !== 'undefined') {
            feather.replace();
            
            // Re-initialize icons after AJAX content loads
            document.addEventListener('DOMNodeInserted', function(e) {
                if (e.target.nodeType === 1) {
                    feather.replace();
                }
            });
        }
    }

    // Initialize Bootstrap tooltips
    function initializeTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
            new bootstrap.Tooltip(tooltipTriggerEl)
        );
    }

    // Enhanced form validation
    function initializeFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Focus on first invalid field
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                    }
                }
                
                form.classList.add('was-validated');
            });
        });

        // Real-time validation
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    }

    function validateField(field) {
        const isValid = field.checkValidity();
        const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                        field.parentNode.querySelector('.valid-feedback');
        
        field.classList.remove('is-valid', 'is-invalid');
        
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
        }
    }

    // Alert management
    function initializeAlerts() {
        // Auto-hide success alerts
        const successAlerts = document.querySelectorAll('.alert-success');
        successAlerts.forEach(alert => {
            setTimeout(() => {
                fadeOutAlert(alert);
            }, 5000);
        });

        // Add close functionality to alerts
        const alertCloseButtons = document.querySelectorAll('.alert .btn-close');
        alertCloseButtons.forEach(button => {
            button.addEventListener('click', function() {
                fadeOutAlert(this.closest('.alert'));
            });
        });
    }

    function fadeOutAlert(alert) {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity = '0';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 500);
    }

    function showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('.alert-container') || 
                              createAlertContainer();
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i data-feather="${getAlertIcon(type)}" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alertDiv);
        feather.replace();
        
        // Auto-hide after 5 seconds for success alerts
        if (type === 'success') {
            setTimeout(() => fadeOutAlert(alertDiv), 5000);
        }
    }

    function createAlertContainer() {
        const container = document.createElement('div');
        container.className = 'alert-container';
        document.body.appendChild(container);
        return container;
    }

    function getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        return icons[type] || 'info';
    }

    // Navigation enhancements
    function initializeNavigation() {
        // Active page highlighting
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });

        // Mobile menu auto-close
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    if (navbarCollapse.classList.contains('show')) {
                        navbarToggler.click();
                    }
                });
            });
        }
    }

    // File upload enhancements
    function initializeFileUploads() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', function() {
                handleFileUpload(this);
            });
        });
    }

    function handleFileUpload(input) {
        const files = input.files;
        const maxSize = 16 * 1024 * 1024; // 16MB
        const allowedTypes = input.getAttribute('accept');
        
        // Validate file size and type
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            if (file.size > maxSize) {
                showAlert(`File "${file.name}" is too large. Maximum size is 16MB.`, 'danger');
                input.value = '';
                return;
            }
            
            if (allowedTypes && !isFileTypeAllowed(file, allowedTypes)) {
                showAlert(`File "${file.name}" type is not allowed.`, 'danger');
                input.value = '';
                return;
            }
        }
        
        // Show file preview/info
        showFileInfo(input, files);
    }

    function isFileTypeAllowed(file, allowedTypes) {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const mimeType = file.type.toLowerCase();
        
        return allowedTypes.split(',').some(type => {
            type = type.trim();
            return type === fileExtension || type === mimeType;
        });
    }

    function showFileInfo(input, files) {
        const container = input.parentNode;
        let infoDiv = container.querySelector('.file-info');
        
        if (!infoDiv) {
            infoDiv = document.createElement('div');
            infoDiv.className = 'file-info mt-2';
            container.appendChild(infoDiv);
        }
        
        if (files.length === 0) {
            infoDiv.innerHTML = '';
            return;
        }
        
        const fileList = Array.from(files).map(file => {
            const size = formatFileSize(file.size);
            return `<small class="text-success d-block">
                <i data-feather="file" class="me-1"></i>
                ${file.name} (${size})
            </small>`;
        }).join('');
        
        infoDiv.innerHTML = fileList;
        feather.replace();
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Auto-calculations for forms
    function initializeAutoCalculations() {
        // Purchase request calculations
        const quantityInput = document.getElementById('quantity');
        const unitPriceInput = document.getElementById('unitPrice');
        const totalAmountInput = document.getElementById('totalAmount');
        
        if (quantityInput && unitPriceInput && totalAmountInput) {
            [quantityInput, unitPriceInput].forEach(input => {
                input.addEventListener('input', calculatePurchaseTotal);
            });
        }

        // Expense record calculations
        initializeExpenseCalculations();
    }

    function calculatePurchaseTotal() {
        const quantity = parseFloat(document.getElementById('quantity').value) || 0;
        const unitPrice = parseFloat(document.getElementById('unitPrice').value) || 0;
        const total = quantity * unitPrice;
        
        document.getElementById('totalAmount').value = total.toFixed(2);
    }

    function initializeExpenseCalculations() {
        // This will be called for dynamically added expense items
        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('item-quantity') || 
                e.target.classList.contains('item-rate')) {
                calculateExpenseItemAmount(e.target);
            }
        });
    }

    function calculateExpenseItemAmount(input) {
        const row = input.closest('.expense-item');
        if (!row) return;
        
        const quantity = parseFloat(row.querySelector('.item-quantity').value) || 0;
        const rate = parseFloat(row.querySelector('.item-rate').value) || 0;
        const amount = quantity * rate;
        
        row.querySelector('.item-amount').value = amount.toFixed(2);
        
        // Update total if function exists
        if (typeof calculateTotalAmount === 'function') {
            calculateTotalAmount();
        }
    }

    // Data table enhancements
    function initializeDataTables() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            makeTableResponsive(table);
            addTableSearch(table);
        });
    }

    function makeTableResponsive(table) {
        if (!table.closest('.table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    }

    function addTableSearch(table) {
        const container = table.closest('.card') || table.parentNode;
        const existingSearch = container.querySelector('.table-search');
        
        if (existingSearch || table.rows.length <= 5) return;
        
        const searchDiv = document.createElement('div');
        searchDiv.className = 'table-search mb-3';
        searchDiv.innerHTML = `
            <input type="text" class="form-control" placeholder="Search table..." 
                   style="max-width: 300px;">
        `;
        
        table.parentNode.insertBefore(searchDiv, table);
        
        const searchInput = searchDiv.querySelector('input');
        searchInput.addEventListener('input', function() {
            filterTable(table, this.value);
        });
    }

    function filterTable(table, searchTerm) {
        const rows = table.querySelectorAll('tbody tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }

    // Modal enhancements
    function initializeModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', function() {
                const firstInput = modal.querySelector('input, textarea, select');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        });
    }

    // Utility functions
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    function formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    }

    // Loading state management
    function showLoading(element) {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
        element.style.opacity = '0.6';
    }

    function hideLoading(element) {
        element.classList.remove('loading');
        element.style.pointerEvents = '';
        element.style.opacity = '';
    }

    // Form submission with loading state
    function handleFormSubmission(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Processing...
                `;
            }
        });
    }

    // Auto-refresh functionality for admin pages
    function initializeAutoRefresh() {
        if (window.location.pathname.includes('/admin')) {
            // Auto-refresh every 2 minutes
            setTimeout(() => {
                window.location.reload();
            }, 120000);
        }
    }

    // Keyboard shortcuts
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.table-search input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const modalInstance = bootstrap.Modal.getInstance(openModal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
            }
        });
    }

    // Initialize additional features
    initializeAutoRefresh();
    initializeKeyboardShortcuts();

    // Export utility functions for global use
    window.AlphaWorkdesk = {
        showAlert,
        formatCurrency,
        formatDate,
        showLoading,
        hideLoading,
        debounce
    };

})();

// Additional specific functionality for expense forms
function addExpenseItem() {
    const template = document.getElementById('expenseItemTemplate');
    if (!template) return;
    
    const clone = template.content.cloneNode(true);
    const itemsContainer = document.getElementById('expenseItems');
    const itemCount = itemsContainer.children.length;
    
    // Update item number
    clone.querySelector('.item-number').textContent = itemCount + 1;
    
    // Set unique names for form fields
    const inputs = clone.querySelectorAll('input, select');
    inputs.forEach(input => {
        const baseName = input.className.replace('form-control ', '').replace('item-', '');
        input.name = `items[${itemCount}][${baseName}]`;
    });
    
    itemsContainer.appendChild(clone);
    feather.replace();
    
    // Scroll to new item
    itemsContainer.lastElementChild.scrollIntoView({ behavior: 'smooth' });
}

function removeExpenseItem(button) {
    const item = button.closest('.expense-item');
    item.remove();
    
    // Update item numbers and field names
    updateExpenseItemNumbers();
    
    // Recalculate total
    if (typeof calculateTotalAmount === 'function') {
        calculateTotalAmount();
    }
}

function updateExpenseItemNumbers() {
    const items = document.querySelectorAll('.expense-item');
    items.forEach((item, index) => {
        item.querySelector('.item-number').textContent = index + 1;
        
        const inputs = item.querySelectorAll('input, select');
        inputs.forEach(input => {
            const fieldName = input.className.includes('item-description') ? 'description' :
                           input.className.includes('item-purpose') ? 'purpose' :
                           input.className.includes('item-quantity') ? 'quantity' :
                           input.className.includes('item-rate') ? 'rate' :
                           input.className.includes('item-voucher') ? 'voucher' : '';
            
            if (fieldName) {
                input.name = `items[${index}][${fieldName}]`;
            }
        });
    });
}
