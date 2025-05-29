/**
 * Color Scheme Management for DeepSearch Research Platform
 * Handles dynamic color scheme switching and hover previews
 * Based on data visualization best practices from Atlassian guidelines
 */

// Color scheme definitions matching Python backend
const COLOR_SCHEMES = {
    "Warm Earth": {
        primary: "#8B4513",
        secondary: "#D2691E",
        accent: "#DEB887",
        background: "#FAF8F5",
        surface: "#FFFFFF",
        text: "#2F2F2F",
        textSecondary: "#5D4E37"
    },
    "Ocean Analytics": {
        primary: "#1E3A8A",
        secondary: "#3B82F6",
        accent: "#DBEAFE",
        background: "#F8FAFC",
        surface: "#FFFFFF",
        text: "#0F172A",
        textSecondary: "#334155"
    },
    "Forest Insights": {
        primary: "#166534",
        secondary: "#16A34A",
        accent: "#BBFCA2",
        background: "#F0FDF4",
        surface: "#FFFFFF",
        text: "#14532D",
        textSecondary: "#166534"
    },
    "Innovation Hub": {
        primary: "#7C3AED",
        secondary: "#A855F7",
        accent: "#E9D5FF",
        background: "#FEFEFF",
        surface: "#FFFFFF",
        text: "#1F2937",
        textSecondary: "#4B5563"
    },
    "High Contrast": {
        primary: "#000000",
        secondary: "#1F2937",
        accent: "#FFF000",
        background: "#FFFFFF",
        surface: "#FFFFFF",
        text: "#000000",
        textSecondary: "#1F2937"
    },
    "Sunset Analytics": {
        primary: "#DC2626",
        secondary: "#EA580C",
        accent: "#FED7AA",
        background: "#FFFBF5",
        surface: "#FFFFFF",
        text: "#1C1917",
        textSecondary: "#57534E"
    }
};

/**
 * Initialize color scheme hover preview functionality
 * Sets up event listeners for dropdown options
 */
function addColorSchemeHoverPreview() {
    setTimeout(() => {
        const dropdown = document.querySelector('#color-scheme-dropdown select, #color-scheme-dropdown .wrap');
        if (dropdown) {
            const options = dropdown.querySelectorAll('option');
            options.forEach(option => {
                option.addEventListener('mouseenter', function() {
                    const schemeName = this.textContent.split(' - ')[0];
                    previewColorScheme(schemeName);
                });
                option.addEventListener('mouseleave', function() {
                    restoreOriginalColors();
                });
            });
        }
    }, 1000);
}

/**
 * Preview a color scheme on hover
 * @param {string} schemeName - Name of the color scheme to preview
 */
function previewColorScheme(schemeName) {
    const colors = COLOR_SCHEMES[schemeName] || COLOR_SCHEMES["Warm Earth"];
    
    let previewStyle = document.getElementById('color-preview-style');
    if (!previewStyle) {
        previewStyle = document.createElement('style');
        previewStyle.id = 'color-preview-style';
        document.head.appendChild(previewStyle);
    }
    
    previewStyle.textContent = `
        .gradio-container { 
            background: ${colors.background} !important; 
            transition: all 0.3s ease; 
        }
        .header-container { 
            background: linear-gradient(135deg, ${colors.primary}, ${colors.secondary}) !important; 
        }
        button { 
            background: ${colors.secondary} !important; 
        }
        .settings-card, .output-card { 
            border-color: ${colors.accent} !important; 
        }
    `;
}

/**
 * Restore original colors after hover preview
 */
function restoreOriginalColors() {
    const previewStyle = document.getElementById('color-preview-style');
    if (previewStyle) {
        previewStyle.remove();
    }
}

/**
 * Apply a color scheme permanently
 * @param {string} scheme_name - Name of the color scheme to apply
 * @returns {string} The scheme name for chaining
 */
function injectColorScheme(scheme_name) {
    // Extract scheme name from dropdown format
    if (scheme_name.includes(' - ')) {
        scheme_name = scheme_name.split(' - ')[0];
    }
    
    // Remove existing custom CSS
    const existingStyle = document.getElementById('dynamic-color-scheme');
    if (existingStyle) {
        existingStyle.remove();
    }
    
    // Create new style element with updated CSS
    const styleElement = document.createElement('style');
    styleElement.id = 'dynamic-color-scheme';
    
    const colors = COLOR_SCHEMES[scheme_name] || COLOR_SCHEMES["Warm Earth"];
    
    // Generate comprehensive CSS with the new colors
    const css = `
        :root {
            --color-primary: ${colors.primary};
            --color-secondary: ${colors.secondary};
            --color-accent: ${colors.accent};
            --color-background: ${colors.background};
            --color-surface: ${colors.surface};
            --color-text-primary: ${colors.text};
            --color-text-secondary: ${colors.textSecondary};
        }
        
        .gradio-container {
            background: var(--color-background) !important;
            color: var(--color-text-primary) !important;
            transition: all 0.2s ease-in-out;
        }
        
        .start-button {
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary)) !important;
            border: none !important;
            color: white !important;
        }
        
        .settings-card, .output-card {
            background: var(--color-surface) !important;
            border: 2px solid var(--color-accent) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
        }
        
        .header-container {
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary)) !important;
            color: white !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            margin-bottom: 1.5rem !important;
        }
        
        button {
            background: var(--color-secondary) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        button:hover {
            background: var(--color-primary) !important;
            transform: translateY(-1px) !important;
        }
        
        .gr-textbox, .gr-dropdown, input, textarea, select {
            border: 2px solid var(--color-accent) !important;
            border-radius: 8px !important;
            background: var(--color-surface) !important;
            color: var(--color-text-primary) !important;
        }
        
        .gr-textbox:focus, .gr-dropdown:focus, input:focus, textarea:focus, select:focus {
            border-color: var(--color-primary) !important;
            box-shadow: 0 0 0 3px rgba(139, 69, 19, 0.1) !important;
        }
        
        .thinking-output, .report-output {
            background: var(--color-surface) !important;
            border: 2px solid var(--color-accent) !important;
            color: var(--color-text-primary) !important;
        }
        
        .scheme-description {
            background: var(--color-accent) !important;
            color: var(--color-text-secondary) !important;
            border-left: 4px solid var(--color-primary) !important;
        }
        
        .main-tabs .tab-nav button.selected {
            color: var(--color-primary) !important;
            border-bottom-color: var(--color-primary) !important;
        }
    `;
    
    styleElement.textContent = css;
    document.head.appendChild(styleElement);
    
    return scheme_name;
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    addColorSchemeHoverPreview();
});

// Also initialize after a short delay to handle Gradio's dynamic loading
setTimeout(addColorSchemeHoverPreview, 1000);

// Export functions for global access
window.addColorSchemeHoverPreview = addColorSchemeHoverPreview;
window.previewColorScheme = previewColorScheme;
window.restoreOriginalColors = restoreOriginalColors;
window.injectColorScheme = injectColorScheme;