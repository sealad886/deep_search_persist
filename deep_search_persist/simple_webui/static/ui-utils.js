/**
 * UI Utility Functions for DeepSearch Research Platform
 * General purpose JavaScript utilities for the Gradio interface
 */

/**
 * Initialize all UI utilities after page load
 */
function initializeUIUtils() {
    // Add any general UI initializations here
    console.log('DeepSearch UI utilities initialized');
}

/**
 * Utility function to safely query elements with retry
 * @param {string} selector - CSS selector
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} delay - Delay between retries in ms
 * @returns {Promise<Element|null>} The found element or null
 */
function waitForElement(selector, maxRetries = 10, delay = 100) {
    return new Promise((resolve) => {
        let retries = 0;
        
        function check() {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
            } else if (retries < maxRetries) {
                retries++;
                setTimeout(check, delay);
            } else {
                resolve(null);
            }
        }
        
        check();
    });
}

/**
 * Add smooth scrolling behavior to specific elements
 */
function addSmoothScrolling() {
    document.documentElement.style.scrollBehavior = 'smooth';
}

/**
 * Handle keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + Enter to trigger research (if in research tab)
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            const researchButton = document.querySelector('.start-button button');
            if (researchButton && !researchButton.disabled) {
                event.preventDefault();
                researchButton.click();
            }
        }
        
        // Escape to clear focus
        if (event.key === 'Escape') {
            if (document.activeElement) {
                document.activeElement.blur();
            }
        }
    });
}

/**
 * Add loading states to buttons
 * @param {Element} button - Button element
 * @param {boolean} loading - Whether to show loading state
 */
function setButtonLoading(button, loading) {
    if (loading) {
        button.style.opacity = '0.7';
        button.style.pointerEvents = 'none';
        button.setAttribute('aria-busy', 'true');
    } else {
        button.style.opacity = '1';
        button.style.pointerEvents = 'auto';
        button.setAttribute('aria-busy', 'false');
    }
}

/**
 * Enhanced notification system
 * @param {string} message - Notification message
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Use Gradio's built-in notification system if available
    if (window.gradio && window.gradio.Info) {
        switch (type) {
            case 'success':
                window.gradio.Info(`✅ ${message}`);
                break;
            case 'error':
                window.gradio.Error(`❌ ${message}`);
                break;
            case 'warning':
                window.gradio.Warning(`⚠️ ${message}`);
                break;
            default:
                window.gradio.Info(`ℹ️ ${message}`);
        }
    } else {
        // Fallback to console
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

/**
 * Accessibility improvements
 */
function improveAccessibility() {
    // Add focus indicators for keyboard navigation
    const style = document.createElement('style');
    style.textContent = `
        *:focus {
            outline: 2px solid var(--color-primary, #8B4513) !important;
            outline-offset: 2px !important;
        }
        
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        @media (prefers-contrast: high) {
            .settings-card, .output-card {
                border-width: 3px !important;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Add aria-labels to unlabeled interactive elements
    setTimeout(() => {
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            if (button.textContent.trim()) {
                button.setAttribute('aria-label', button.textContent.trim());
            }
        });
    }, 1000);
}

/**
 * Performance monitoring
 */
function monitorPerformance() {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.duration > 50) {
                    console.warn('Long task detected:', entry.duration + 'ms');
                }
            });
        });
        
        try {
            observer.observe({entryTypes: ['longtask']});
        } catch (e) {
            // Longtask API not supported
        }
    }
}

/**
 * Initialize all utilities
 */
function initAll() {
    initializeUIUtils();
    addSmoothScrolling();
    setupKeyboardShortcuts();
    improveAccessibility();
    monitorPerformance();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
} else {
    initAll();
}

// Also initialize after delay for Gradio
setTimeout(initAll, 1000);

// Export utilities
window.UIUtils = {
    waitForElement,
    setButtonLoading,
    showNotification,
    improveAccessibility,
    setupKeyboardShortcuts
};