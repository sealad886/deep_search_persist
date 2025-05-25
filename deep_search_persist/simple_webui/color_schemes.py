"""
Color scheme definitions for the Gradio UI.
Provides multiple professional color themes for the research platform.
"""

# Color scheme definitions
COLOR_SCHEMES = {
    "Classic Brown": {
        "primary": "#8B4513",
        "primary_light": "#A0522D", 
        "primary_dark": "#654321",
        "accent": "#D2B48C",
        "bg": "#FEFEFE",
        "surface": "#FFFFFF",
        "border": "#E5E7EB",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
        "description": "Warm, professional brown theme matching the logo"
    },
    "Ocean Blue": {
        "primary": "#0EA5E9",
        "primary_light": "#38BDF8",
        "primary_dark": "#0284C7", 
        "accent": "#BAE6FD",
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "border": "#E2E8F0",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "description": "Cool, trustworthy blue for clarity and focus"
    },
    "Forest Green": {
        "primary": "#059669",
        "primary_light": "#10B981",
        "primary_dark": "#047857",
        "accent": "#A7F3D0", 
        "bg": "#F0FDF4",
        "surface": "#FFFFFF",
        "border": "#D1FAE5",
        "text_primary": "#064E3B",
        "text_secondary": "#374151",
        "description": "Natural green theme for research and growth"
    },
    "Deep Purple": {
        "primary": "#7C3AED",
        "primary_light": "#8B5CF6",
        "primary_dark": "#6D28D9",
        "accent": "#DDD6FE",
        "bg": "#FAFAF9",
        "surface": "#FFFFFF", 
        "border": "#E5E7EB",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
        "description": "Creative purple for innovative thinking"
    },
    "Sunset Orange": {
        "primary": "#EA580C",
        "primary_light": "#FB923C",
        "primary_dark": "#C2410C",
        "accent": "#FED7AA",
        "bg": "#FFFBF5",
        "surface": "#FFFFFF",
        "border": "#F3E8FF",
        "text_primary": "#1C1917",
        "text_secondary": "#57534E", 
        "description": "Energetic orange for dynamic research"
    },
    "Midnight Blue": {
        "primary": "#1E40AF",
        "primary_light": "#3B82F6",
        "primary_dark": "#1E3A8A",
        "accent": "#DBEAFE",
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "border": "#E2E8F0",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "description": "Professional dark blue for serious research"
    },
    "Rose Gold": {
        "primary": "#E11D48",
        "primary_light": "#F43F5E", 
        "primary_dark": "#BE123C",
        "accent": "#FECDD3",
        "bg": "#FFFBFB",
        "surface": "#FFFFFF",
        "border": "#FEE2E2",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
        "description": "Elegant rose theme for sophisticated analysis"
    }
}

def generate_css_for_scheme(scheme_name):
    """Generate CSS with the selected color scheme."""
    scheme = COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["Classic Brown"])
    
    css_colors = f"""
/* Import modern fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

/* Dynamic color scheme variables */
:root {{
    --primary-color: {scheme["primary"]};
    --primary-light: {scheme["primary_light"]};
    --primary-dark: {scheme["primary_dark"]};
    --accent-color: {scheme["accent"]};
    --bg-color: {scheme["bg"]};
    --surface-color: {scheme["surface"]};
    --border-color: {scheme["border"]};
    --text-primary: {scheme["text_primary"]};
    --text-secondary: {scheme["text_secondary"]};
    --success-color: #10B981;
    --error-color: #EF4444;
    --warning-color: #F59E0B;
}}"""
    
    return css_colors

def create_scheme_choices():
    """Create dropdown choices for color schemes."""
    return list(COLOR_SCHEMES.keys())

def get_scheme_description(scheme_name):
    """Get description for a color scheme."""
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["Classic Brown"])["description"]