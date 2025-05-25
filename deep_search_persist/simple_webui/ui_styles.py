"""
CSS styling definitions for the Gradio UI.
Contains all the styling rules for the modern, professional interface.
"""

# Base CSS styles (without color variables)
BASE_CSS = """
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Color scheme preview circles */
.color-preview {
    display: inline-block !important;
    width: 20px !important;
    height: 20px !important;
    border-radius: 50% !important;
    margin-right: 8px !important;
    border: 2px solid rgba(255, 255, 255, 0.8) !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    vertical-align: middle !important;
}

.scheme-option {
    display: flex !important;
    align-items: center !important;
    padding: 0.5rem !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

.scheme-option:hover {
    background: rgba(0, 0, 0, 0.05) !important;
}

.scheme-description {
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

/* Main container */
.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    background: var(--bg-color) !important;
}

/* Header styling */
.header-container {
    background: linear-gradient(135deg, var(--surface-color) 0%, #F9FAFB 100%) !important;
    border-bottom: 1px solid var(--border-color) !important;
    padding: 1.5rem 2rem !important;
    margin-bottom: 2rem !important;
    border-radius: 12px 12px 0 0 !important;
}

.app-title {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--primary-color) !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    gap: 1rem !important;
}

.app-subtitle {
    font-size: 1rem !important;
    color: var(--text-secondary) !important;
    margin-top: 0.5rem !important;
    font-weight: 400 !important;
}

/* Logo styling */
.app-logo {
    width: 48px !important;
    height: 48px !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.15) !important;
}

/* Tab styling */
.tab-nav button {
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px 8px 0 0 !important;
    border: none !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    transition: all 0.2s ease !important;
}

.tab-nav button[aria-selected="true"] {
    background: var(--surface-color) !important;
    color: var(--primary-color) !important;
    border-bottom: 2px solid var(--primary-color) !important;
}

.tab-nav button:hover {
    background: rgba(139, 69, 19, 0.05) !important;
    color: var(--primary-color) !important;
}

/* Input styling */
input, textarea, select {
    border: 1.5px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
    background: var(--surface-color) !important;
}

input:focus, textarea:focus, select:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(139, 69, 19, 0.1) !important;
    outline: none !important;
}

/* Button styling */
.gr-button {
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    border: none !important;
    transition: all 0.2s ease !important;
    font-size: 0.95rem !important;
}

.gr-button-primary {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.25) !important;
}

.gr-button-primary:hover {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-color) 100%) !important;
    box-shadow: 0 4px 16px rgba(139, 69, 19, 0.35) !important;
    transform: translateY(-1px) !important;
}

.gr-button-secondary {
    background: var(--surface-color) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border-color) !important;
}

.gr-button-secondary:hover {
    background: var(--accent-color) !important;
    border-color: var(--primary-color) !important;
}

.gr-button-stop {
    background: linear-gradient(135deg, var(--error-color) 0%, #DC2626 100%) !important;
    color: white !important;
}

/* Output containers */
.output-container {
    background: var(--surface-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

/* Code/monospace outputs */
.gr-textbox textarea[readonly] {
    font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace !important;
    font-size: 0.9rem !important;
    line-height: 1.5 !important;
    background: #F8F9FA !important;
}

/* Slider styling */
.gr-slider input[type="range"] {
    height: 6px !important;
    background: var(--border-color) !important;
    border-radius: 3px !important;
}

.gr-slider input[type="range"]::-webkit-slider-thumb {
    background: var(--primary-color) !important;
    border-radius: 50% !important;
    width: 20px !important;
    height: 20px !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(139, 69, 19, 0.3) !important;
}

/* Card layouts */
.settings-card, .output-card {
    background: var(--surface-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
}

/* Status indicators */
.status-success {
    color: var(--success-color) !important;
}

.status-error {
    color: var(--error-color) !important;
}

.status-warning {
    color: var(--warning-color) !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .gradio-container {
        padding: 1rem !important;
    }
    
    .header-container {
        padding: 1rem !important;
    }
    
    .app-title {
        font-size: 1.5rem !important;
    }
}

/* Loading indicators */
.loading {
    opacity: 0.7 !important;
    pointer-events: none !important;
}

/* Notification styling */
.gr-toast {
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
"""

def create_complete_css(scheme_name="Classic Brown"):
    """Create complete CSS with the selected color scheme."""
    from .color_schemes import generate_css_for_scheme
    return generate_css_for_scheme(scheme_name) + BASE_CSS