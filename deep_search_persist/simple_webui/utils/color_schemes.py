"""
Advanced Color Scheme System for Data Visualization
Based on Atlassian's color theory and accessibility guidelines.

Implements qualitative, sequential, and diverging color palettes
with accessibility considerations and color blindness support.
"""

from typing import Any
from .color_convert import hex_to_rgb, rgb_to_hex, rgb_to_hsl, hsl_to_rgb
from .hue_spacing_calculator import generate_accessible_palette


# Core Color Theory Implementation
class ColorPalette:
    """Base class for color palette generation following data visualization best practices."""

    def __init__(self, name: str, description: str, base_hue: str, accessibility_rating: str = "AA"):
        self.name = name
        self.description = description
        self.base_hue = base_hue
        self.accessibility_rating = accessibility_rating

    def generate_qualitative_colors(self, count=6):
        """
        Generate distinct categorical colors for qualitative data visualization.

        Uses perceptually uniform color distribution in HSL space, optimized for
        categorical distinction and color-blind accessibility.

        Args:
            count: Number of distinct colors to generate (max 12 recommended)

        Returns:
            List of hex color strings
        """
        if count <= 0:
            return []

        # Parse base hue
        try:
            base_r, base_g, base_b = hex_to_rgb(self.base_hue)
            base_h, base_s, base_l = rgb_to_hsl(base_r, base_g, base_b)
        except ValueError:
            # Fallback to a neutral base
            base_h, base_s, base_l = 200, 0.6, 0.5

        colors = []

        # For small counts, use predefined high-contrast colors
        if count <= 2:
            # High contrast pair
            colors = [self.base_hue]
            if count == 2:
                # Add complementary color
                comp_h = (base_h + 180) % 360
                comp_color = hsl_to_rgb(comp_h, base_s, base_l)
                colors.append(rgb_to_hex(comp_color))
        else:
            # Use golden angle for optimal perceptual distribution
            golden_angle = 137.5

            for i in range(count):
                if i == 0:
                    # First color is base hue
                    h = base_h
                    s = base_s
                    lx = base_l
                else:
                    # Distribute hues using golden angle for better perception
                    h = (base_h + i * golden_angle) % 360

                    # Vary saturation and lightness for additional distinction
                    s = base_s + (0.1 * (i % 3 - 1))  # Slight saturation variation
                    lx = base_l + (0.1 * ((i // 3) % 3 - 1))  # Slight lightness variation

                    # Clamp values
                    s = max(0.3, min(0.9, s))
                    lx = max(0.3, min(0.7, lx))

                rgb = hsl_to_rgb(h, s, lx)
                colors.append(rgb_to_hex(rgb))

        return colors[:count]

    def generate_sequential_colors(self, steps=5):
        """
        Generate lightness-varying colors for sequential/ordered data visualization.

        Creates a perceptually uniform progression from light to dark variants
        of the base color, suitable for representing ordered data.

        Args:
            steps: Number of color steps in the sequence

        Returns:
            List of hex color strings from light to dark
        """
        if steps <= 0:
            return []

        try:
            base_r, base_g, base_b = hex_to_rgb(self.base_hue)
            base_h, base_s, base_l = rgb_to_hsl(base_r, base_g, base_b)
        except ValueError:
            # Fallback to a neutral progression
            base_h, base_s, base_l = 200, 0.6, 0.5

        colors = []

        if steps == 1:
            return [self.base_hue]

        # Define lightness range for good contrast and readability
        min_lightness = 0.15  # Dark enough for contrast
        max_lightness = 0.85  # Light enough to distinguish from white

        # Adjust saturation slightly across the range for better perception
        base_saturation = max(0.4, min(0.8, base_s))

        for i in range(steps):
            # Calculate lightness progression
            if steps == 1:
                lightness = base_l
            else:
                # Linear interpolation from light to dark
                progress = i / (steps - 1)
                lightness = max_lightness - progress * (max_lightness - min_lightness)

            # Slightly increase saturation for darker colors to maintain vibrancy
            saturation = base_saturation + (1 - lightness) * 0.1
            saturation = max(0.2, min(0.9, saturation))

            rgb = hsl_to_rgb(base_h, saturation, lightness)
            colors.append(rgb_to_hex(rgb))

        return colors


# Data Visualization Color Schemes
# Following Atlassian guidelines for accessibility and effectiveness
COLOR_SCHEMES: dict[str, Any] = {
    # Default: Warm & Earthy (Data-driven design)
    "Warm Earth": {
        "type": "qualitative",
        "description": "Warm, earthy tones optimized for data visualization accessibility",
        "colors": {
            # Primary data colors (high contrast, colorblind-safe)
            "primary": "#8B4513",  # Saddle Brown (main data)
            "secondary": "#D2691E",  # Chocolate (secondary data)
            "tertiary": "#CD853F",  # Peru (tertiary data)
            # Supporting colors
            "accent": "#DEB887",  # Burlywood (highlights)
            "success": "#228B22",  # Forest Green (positive indicators)
            "warning": "#FF8C00",  # Dark Orange (attention)
            "error": "#DC143C",  # Crimson (errors)
            # Neutral palette (backgrounds, text)
            "background": "#FAF8F5",  # Warm white
            "surface": "#FFFFFF",  # Pure white
            "surface_dark": "#F5F5DC",  # Beige
            "border": "#D3D3D3",  # Light gray
            "border_focus": "#8B4513",  # Primary for focus states
            # Text hierarchy (accessibility compliant)
            "text_primary": "#2F2F2F",  # Near black (primary text)
            "text_secondary": "#5D4E37",  # Dark olive (secondary text)
            "text_muted": "#808080",  # Gray (muted text)
            "text_inverse": "#FFFFFF",  # White text on dark
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #8B4513 0%, #D2691E 100%)",
            "accent": "linear-gradient(135deg, #DEB887 0%, #F5DEB3 100%)",
            "success": "linear-gradient(135deg, #228B22 0%, #32CD32 100%)",
        },
    },
    # Professional Blue (Sequential palette)
    "Ocean Analytics": {
        "type": "sequential",
        "description": "Professional blue palette for analytical interfaces",
        "colors": {
            "primary": "#1E3A8A",  # Blue 900
            "secondary": "#3B82F6",  # Blue 500
            "tertiary": "#60A5FA",  # Blue 400
            "accent": "#DBEAFE",  # Blue 100
            "success": "#059669",  # Emerald 600
            "warning": "#D97706",  # Amber 600
            "error": "#DC2626",  # Red 600
            "background": "#F8FAFC",  # Slate 50
            "surface": "#FFFFFF",
            "surface_dark": "#F1F5F9",  # Slate 100
            "border": "#E2E8F0",  # Slate 200
            "border_focus": "#3B82F6",
            "text_primary": "#0F172A",  # Slate 900
            "text_secondary": "#334155",  # Slate 700
            "text_muted": "#64748B",  # Slate 500
            "text_inverse": "#FFFFFF",
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%)",
            "accent": "linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%)",
            "success": "linear-gradient(135deg, #059669 0%, #10B981 100%)",
        },
    },
    # Nature Green (Qualitative palette)
    "Forest Insights": {
        "type": "qualitative",
        "description": "Nature-inspired green palette for growth and sustainability data",
        "colors": {
            "primary": "#166534",  # Green 800
            "secondary": "#16A34A",  # Green 600
            "tertiary": "#4ADE80",  # Green 400
            "accent": "#BBFCA2",  # Green 200
            "success": "#15803D",  # Green 700
            "warning": "#CA8A04",  # Yellow 600
            "error": "#B91C1C",  # Red 700
            "background": "#F0FDF4",  # Green 50
            "surface": "#FFFFFF",
            "surface_dark": "#ECFDF5",  # Green 50
            "border": "#D1FAE5",  # Green 100
            "border_focus": "#16A34A",
            "text_primary": "#14532D",  # Green 900
            "text_secondary": "#166534",  # Green 800
            "text_muted": "#4B5563",  # Gray 600
            "text_inverse": "#FFFFFF",
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #166534 0%, #16A34A 100%)",
            "accent": "linear-gradient(135deg, #BBFCA2 0%, #D9F99D 100%)",
            "success": "linear-gradient(135deg, #15803D 0%, #16A34A 100%)",
        },
    },
    # Innovation Purple (Diverging palette)
    "Innovation Hub": {
        "type": "diverging",
        "description": "Creative purple palette for innovative research platforms",
        "colors": {
            "primary": "#7C3AED",  # Violet 600
            "secondary": "#A855F7",  # Purple 500
            "tertiary": "#C084FC",  # Purple 400
            "accent": "#E9D5FF",  # Purple 200
            "success": "#059669",  # Emerald 600
            "warning": "#D97706",  # Amber 600
            "error": "#DC2626",  # Red 600
            "background": "#FEFEFF",  # Almost white with purple tint
            "surface": "#FFFFFF",
            "surface_dark": "#FAF5FF",  # Purple 50
            "border": "#E5E7EB",  # Gray 200
            "border_focus": "#A855F7",
            "text_primary": "#1F2937",  # Gray 800
            "text_secondary": "#4B5563",  # Gray 600
            "text_muted": "#6B7280",  # Gray 500
            "text_inverse": "#FFFFFF",
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)",
            "accent": "linear-gradient(135deg, #E9D5FF 0%, #DDD6FE 100%)",
            "success": "linear-gradient(135deg, #059669 0%, #10B981 100%)",
        },
    },
    # High Contrast (Accessibility focused)
    "High Contrast": {
        "type": "accessibility",
        "description": "Maximum contrast palette for accessibility compliance (WCAG AAA)",
        "colors": {
            "primary": "#000000",  # Pure black
            "secondary": "#1F2937",  # Dark gray
            "tertiary": "#374151",  # Medium gray
            "accent": "#FFF000",  # Bright yellow (high contrast)
            "success": "#006400",  # Dark green
            "warning": "#FF8C00",  # Dark orange
            "error": "#8B0000",  # Dark red
            "background": "#FFFFFF",  # Pure white
            "surface": "#FFFFFF",
            "surface_dark": "#F9F9F9",  # Very light gray
            "border": "#000000",  # Black borders
            "border_focus": "#0000FF",  # Blue focus
            "text_primary": "#000000",  # Black text
            "text_secondary": "#1F2937",  # Dark gray
            "text_muted": "#374151",  # Medium gray
            "text_inverse": "#FFFFFF",  # White on dark
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #000000 0%, #1F2937 100%)",
            "accent": "linear-gradient(135deg, #FFF000 0%, #FFFF99 100%)",
            "success": "linear-gradient(135deg, #006400 0%, #228B22 100%)",
        },
    },
    # Sunset Analytics (Warm diverging)
    "Sunset Analytics": {
        "type": "diverging",
        "description": "Warm sunset palette for engaging data storytelling",
        "colors": {
            "primary": "#DC2626",  # Red 600
            "secondary": "#EA580C",  # Orange 600
            "tertiary": "#F59E0B",  # Amber 500
            "accent": "#FED7AA",  # Orange 200
            "success": "#16A34A",  # Green 600
            "warning": "#D97706",  # Amber 600
            "error": "#B91C1C",  # Red 700
            "background": "#FFFBF5",  # Warm white
            "surface": "#FFFFFF",
            "surface_dark": "#FEF3E2",  # Orange 50
            "border": "#FED7AA",  # Orange 200
            "border_focus": "#EA580C",
            "text_primary": "#1C1917",  # Stone 900
            "text_secondary": "#57534E",  # Stone 600
            "text_muted": "#78716C",  # Stone 500
            "text_inverse": "#FFFFFF",
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #DC2626 0%, #EA580C 100%)",
            "accent": "linear-gradient(135deg, #FED7AA 0%, #FDBA74 100%)",
            "success": "linear-gradient(135deg, #16A34A 0%, #22C55E 100%)",
        },
    },
}


def generate_perceptual_palette(base_hue: str, count: int, min_step: float = 25.0) -> list[str]:
    """
    Generate perceptually uniform color palette using CAM16-UCS spacing.
    
    Args:
        base_hue: Base color as hex string (e.g., "#FF5733")
        count: Number of colors to generate
        min_step: Minimum perceptual distance between colors
        
    Returns:
        List of hex color strings with optimal perceptual spacing
    """
    return generate_accessible_palette(base_hue, count, min_step)


def get_color_scheme(scheme_name="Warm Earth"):
    """Get a color scheme with fallback to default."""
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["Warm Earth"])


def create_scheme_choices():
    """Create dropdown choices with descriptive labels."""
    choices = []
    for name, scheme in COLOR_SCHEMES.items():
        choices.append(f"{name} - {scheme['description']}")
    return choices


def get_scheme_description(scheme_name):
    """Get description for a color scheme."""
    scheme = get_color_scheme(scheme_name)
    return scheme["description"]


def generate_css_variables(scheme_name="Warm Earth"):
    """Generate CSS custom properties for the selected scheme."""
    scheme = get_color_scheme(scheme_name)
    colors = scheme["colors"]
    gradients = scheme["gradients"]

    css_vars = ":root {\n"

    # Color variables
    for key, value in colors.items():
        css_vars += f"    --color-{key.replace('_', '-')}: {value};\n"

    # Gradient variables
    for key, value in gradients.items():
        css_vars += f"    --gradient-{key}: {value};\n"

    # Semantic color mappings for common UI elements
    css_vars += """
    /* Semantic mappings */
    --btn-primary-bg: var(--color-primary);
    --btn-primary-hover: var(--color-secondary);
    --btn-secondary-bg: var(--color-secondary);
    --card-bg: var(--color-surface);
    --card-border: var(--color-border);
    --input-border: var(--color-border);
    --input-focus: var(--color-border-focus);
    --text-heading: var(--color-text-primary);
    --text-body: var(--color-text-secondary);
    --text-caption: var(--color-text-muted);
"""

    css_vars += "}\n"
    return css_vars


def create_complete_css(scheme_name="Warm Earth"):
    """Generate complete CSS for the UI with the selected color scheme."""
    scheme = get_color_scheme(scheme_name)

    css = f"""
/* Color Scheme: {scheme_name} */
/* {scheme['description']} */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

{generate_css_variables(scheme_name)}

/* Global Styles */
* {{
    box-sizing: border-box;
}}

.gradio-container {{
    background: var(--color-background) !important;
    color: var(--color-text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    transition: all 0.2s ease-in-out;
}}

/* Header Styling */
.header-container {{
    background: var(--gradient-primary) !important;
    color: var(--color-text-inverse) !important;
    padding: 1.5rem !important;
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}}

.app-title {{
    font-size: 1.875rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
}}

.app-subtitle {{
    font-size: 1rem !important;
    opacity: 0.9 !important;
    margin-top: 0.5rem !important;
}}

/* Cards and Containers */
.settings-card, .output-card {{
    background: var(--color-surface) !important;
    border: 2px solid var(--color-border) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
    transition: border-color 0.2s ease-in-out !important;
}}

.settings-card:hover, .output-card:hover {{
    border-color: var(--color-border-focus) !important;
}}

/* Button Styling */
button {{
    background: var(--color-secondary) !important;
    color: var(--color-text-inverse) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}}

button:hover {{
    background: var(--color-primary) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}}

.start-button {{
    background: var(--gradient-primary) !important;
    font-size: 1.125rem !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
}}

/* Input Styling */
.gr-textbox, .gr-dropdown, input, textarea, select {{
    border: 2px solid var(--color-border) !important;
    border-radius: 8px !important;
    background: var(--color-surface) !important;
    color: var(--color-text-primary) !important;
    transition: all 0.2s ease-in-out !important;
}}

.gr-textbox:focus, .gr-dropdown:focus, input:focus, textarea:focus, select:focus {{
    border-color: var(--color-border-focus) !important;
    box-shadow: 0 0 0 3px rgba(var(--color-primary), 0.1) !important;
    outline: none !important;
}}

/* Output Areas */
.thinking-output, .report-output {{
    background: var(--color-surface) !important;
    border: 2px solid var(--color-border) !important;
    border-radius: 8px !important;
    color: var(--color-text-primary) !important;
    font-family: 'Inter', monospace !important;
    line-height: 1.6 !important;
}}

/* Status Indicators */
.status-text {{
    background: var(--color-surface-dark) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 6px !important;
    padding: 0.75rem !important;
}}

/* Tab Styling */
.main-tabs .tab-nav {{
    background: var(--color-surface) !important;
    border-bottom: 2px solid var(--color-border) !important;
}}

.main-tabs .tab-nav button {{
    background: transparent !important;
    color: var(--color-text-secondary) !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
}}

.main-tabs .tab-nav button.selected {{
    color: var(--color-primary) !important;
    border-bottom-color: var(--color-primary) !important;
}}

/* Color Scheme Dropdown */
.color-scheme-dropdown {{
    min-width: 200px !important;
}}

.scheme-description {{
    background: var(--color-accent) !important;
    padding: 0.75rem !important;
    border-radius: 6px !important;
    border-left: 4px solid var(--color-primary) !important;
    margin-top: 0.5rem !important;
    font-style: italic !important;
    color: var(--color-text-secondary) !important;
}}

/* Accessibility Enhancements */
@media (prefers-reduced-motion: reduce) {{
    * {{
        transition: none !important;
        animation: none !important;
    }}
}}

/* Focus indicators for keyboard navigation */
*:focus {{
    outline: 2px solid var(--color-primary) !important;
    outline-offset: 2px !important;
}}

/* High contrast mode support */
@media (prefers-contrast: high) {{
    .settings-card, .output-card {{
        border-width: 3px !important;
    }}
    
    button {{
        border: 2px solid var(--color-text-inverse) !important;
    }}
}}
"""

    return css
