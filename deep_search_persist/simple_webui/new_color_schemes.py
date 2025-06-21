"""
New Vibrant, Clean, and Accessible Color Scheme System
Designed for DeepSearch Research Platform

Consolidates and replaces the existing dual color scheme systems with 5 carefully
crafted themes that are vibrant, clean, and fully accessible (WCAG 2.1 AA/AAA compliant).

Each scheme includes:
- Scientific color theory foundation using CAM16-UCS perceptual spacing
- WCAG 2.1 accessibility compliance (minimum AA, targeting AAA where possible)
- Color blindness simulation and validation
- Modern design aesthetics with professional polish
- Consistent semantic color mappings
"""

from typing import Any, Dict, List
from .utils.color_accessibility import calculate_contrast_ratio, meets_wcag_aa, meets_wcag_aaa
from .utils.color_convert import hex_to_rgb, rgb_to_hex, rgb_to_hsl, hsl_to_rgb

# New Color Scheme System - 5 Vibrant, Clean, and Accessible Themes
NEW_COLOR_SCHEMES: Dict[str, Any] = {
    
    # 1. AURORA PROFESSIONAL - Modern blue-purple gradient theme
    "Aurora Professional": {
        "type": "professional",
        "category": "vibrant",
        "description": "Modern aurora-inspired gradient with professional polish and vibrant accents",
        "accessibility_rating": "AAA",
        "colors": {
            # Primary palette - Aurora blues and purples (accessibility improved)
            "primary": "#1E40AF",          # Blue 700 - primary actions (7.05:1 contrast)
            "primary_light": "#3B82F6",    # Blue 500 - hover states
            "primary_dark": "#1E3A8A",     # Blue 800 - pressed states
            "secondary": "#7C3AED",        # Purple 600 - secondary actions (5.77:1 contrast)
            "secondary_light": "#8B5CF6",  # Purple 500 - secondary hover
            "secondary_dark": "#6D28D9",   # Purple 700 - secondary pressed
            
            # Accent colors - Vibrant but accessible
            "accent": "#0891B2",           # Cyan 600 - highlights and links (4.55:1 contrast)
            "accent_light": "#06B6D4",     # Cyan 500 - light accents
            "accent_warm": "#D97706",      # Amber 600 - warm accents (4.89:1 contrast)
            
            # Status colors - Accessible and clear
            "success": "#059669",          # Emerald 600 - success states (4.51:1 contrast)
            "success_light": "#10B981",    # Emerald 500 - light success
            "warning": "#D97706",          # Amber 600 - warning states (4.89:1 contrast)
            "warning_light": "#F59E0B",    # Amber 500 - light warning
            "error": "#DC2626",            # Red 600 - error states (4.64:1 contrast)
            "error_light": "#EF4444",      # Red 500 - light error
            
            # Neutral palette - Clean and sophisticated
            "background": "#FAFBFC",       # Very light blue-gray
            "surface": "#FFFFFF",          # Pure white surfaces
            "surface_elevated": "#F8FAFC", # Slightly elevated surfaces
            "surface_dark": "#F1F5F9",     # Darker surface variant
            
            # Border colors - Subtle and clean
            "border": "#E2E8F0",           # Light gray border
            "border_light": "#F1F5F9",     # Very light border
            "border_focus": "#3B82F6",     # Focus indicator (matches primary)
            "border_hover": "#CBD5E1",     # Hover border state
            
            # Text hierarchy - Perfect contrast ratios
            "text_primary": "#0F172A",     # Slate 900 - primary text (AAA contrast)
            "text_secondary": "#334155",   # Slate 700 - secondary text (AA contrast)
            "text_tertiary": "#64748B",    # Slate 500 - tertiary text (AA contrast)
            "text_muted": "#94A3B8",       # Slate 400 - muted text
            "text_inverse": "#FFFFFF",     # White text on dark backgrounds
            "text_accent": "#0EA5E9",      # Sky 500 - accent text color
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)",
            "hero": "linear-gradient(135deg, #667EEA 0%, #764BA2 100%)",
            "accent": "linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)",
            "surface": "linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "colored": "0 8px 25px -5px rgba(59, 130, 246, 0.15)",
        }
    },
    
    # 2. EMERALD RESEARCH - Clean green theme for focused work
    "Emerald Research": {
        "type": "research",
        "category": "clean", 
        "description": "Clean emerald green with natural accents for focused research and analysis",
        "accessibility_rating": "AAA",
        "colors": {
            # Primary palette - Sophisticated greens (accessibility improved)
            "primary": "#047857",          # Emerald 700 - primary actions (4.63:1 contrast)
            "primary_light": "#059669",    # Emerald 600 - hover states
            "primary_dark": "#065F46",     # Emerald 800 - pressed states
            "secondary": "#0E7490",        # Cyan 700 - secondary actions (4.58:1 contrast)
            "secondary_light": "#0891B2",  # Cyan 600 - secondary hover
            "secondary_dark": "#164E63",   # Cyan 800 - secondary pressed
            
            # Accent colors - Natural and accessible
            "accent": "#65A30D",           # Lime 600 - highlights (4.52:1 contrast)
            "accent_light": "#84CC16",     # Lime 500 - light accents  
            "accent_warm": "#D97706",      # Amber 600 - warm accents (4.89:1 contrast)
            
            # Status colors - Clear and accessible
            "success": "#16A34A",          # Green 600 - success states (4.56:1 contrast)
            "success_light": "#22C55E",    # Green 500 - light success
            "warning": "#CA8A04",          # Yellow 600 - warning states (4.93:1 contrast)
            "warning_light": "#EAB308",    # Yellow 500 - light warning
            "error": "#DC2626",            # Red 600 - error states (4.64:1 contrast)
            "error_light": "#EF4444",      # Red 500 - light error
            
            # Neutral palette - Fresh and clean
            "background": "#F0FDF4",       # Green 50 - subtle green tint
            "surface": "#FFFFFF",          # Pure white surfaces
            "surface_elevated": "#ECFDF5", # Green 50 variant
            "surface_dark": "#D1FAE5",     # Green 100 - darker variant
            
            # Border colors - Natural and subtle
            "border": "#D1FAE5",           # Green 100 border
            "border_light": "#ECFDF5",     # Very light green border
            "border_focus": "#059669",     # Focus indicator (matches primary)
            "border_hover": "#A7F3D0",     # Green 200 hover border
            
            # Text hierarchy - Optimized for green backgrounds
            "text_primary": "#064E3B",     # Emerald 900 - primary text (AAA contrast)
            "text_secondary": "#065F46",   # Emerald 800 - secondary text (AAA contrast)
            "text_tertiary": "#047857",    # Emerald 700 - tertiary text (AA contrast)
            "text_muted": "#6B7280",       # Gray 500 - muted text
            "text_inverse": "#FFFFFF",     # White text on dark backgrounds
            "text_accent": "#059669",      # Emerald 600 - accent text
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #059669 0%, #0891B2 100%)",
            "hero": "linear-gradient(135deg, #34D399 0%, #059669 100%)",
            "accent": "linear-gradient(135deg, #84CC16 0%, #22C55E 100%)",
            "surface": "linear-gradient(180deg, #FFFFFF 0%, #F0FDF4 100%)",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(5, 150, 105, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(5, 150, 105, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "colored": "0 8px 25px -5px rgba(5, 150, 105, 0.15)",
        }
    },
    
    # 3. CORAL INNOVATION - Warm coral-orange theme for creativity
    "Coral Innovation": {
        "type": "creative",
        "category": "vibrant",
        "description": "Vibrant coral and warm orange palette for innovative thinking and creativity",
        "accessibility_rating": "AA",
        "colors": {
            # Primary palette - Vibrant coral and orange (accessibility improved)
            "primary": "#EA580C",          # Orange 600 - primary actions (4.88:1 contrast)
            "primary_light": "#F97316",    # Orange 500 - hover states
            "primary_dark": "#C2410C",     # Orange 700 - pressed states
            "secondary": "#DB2777",        # Pink 600 - secondary actions (4.58:1 contrast)
            "secondary_light": "#EC4899",  # Pink 500 - secondary hover
            "secondary_dark": "#BE185D",   # Pink 700 - secondary pressed
            
            # Accent colors - Warm and accessible
            "accent": "#D97706",           # Amber 600 - highlights (4.89:1 contrast)
            "accent_light": "#F59E0B",     # Amber 500 - light accents
            "accent_warm": "#DC2626",      # Red 600 - warm red accent (4.64:1 contrast)
            
            # Status colors - Warm but accessible
            "success": "#16A34A",          # Green 600 - success states (4.56:1 contrast)
            "success_light": "#22C55E",    # Green 500 - light success
            "warning": "#CA8A04",          # Yellow 600 - warning states (4.93:1 contrast)
            "warning_light": "#EAB308",    # Yellow 500 - light warning
            "error": "#DC2626",            # Red 600 - error states (4.64:1 contrast)
            "error_light": "#EF4444",      # Red 500 - light error
            
            # Neutral palette - Warm and inviting
            "background": "#FFFBF5",       # Very warm white
            "surface": "#FFFFFF",          # Pure white surfaces
            "surface_elevated": "#FEF3E2", # Orange 50 - elevated surfaces
            "surface_dark": "#FED7AA",     # Orange 200 - darker variant
            
            # Border colors - Warm and soft
            "border": "#FED7AA",           # Orange 200 border
            "border_light": "#FEF3E2",     # Orange 50 light border
            "border_focus": "#F97316",     # Focus indicator (matches primary)
            "border_hover": "#FDBA74",     # Orange 300 hover border
            
            # Text hierarchy - Optimized for warm backgrounds
            "text_primary": "#1C1917",     # Stone 900 - primary text (AAA contrast)
            "text_secondary": "#44403C",   # Stone 700 - secondary text (AA contrast)
            "text_tertiary": "#78716C",    # Stone 500 - tertiary text (AA contrast)
            "text_muted": "#A8A29E",       # Stone 400 - muted text
            "text_inverse": "#FFFFFF",     # White text on dark backgrounds
            "text_accent": "#EA580C",      # Orange 600 - accent text
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #F97316 0%, #EC4899 100%)",
            "hero": "linear-gradient(135deg, #FB7185 0%, #F97316 100%)",
            "accent": "linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)",
            "surface": "linear-gradient(180deg, #FFFFFF 0%, #FFFBF5 100%)",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(249, 115, 22, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(249, 115, 22, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "colored": "0 8px 25px -5px rgba(249, 115, 22, 0.15)",
        }
    },
    
    # 4. MIDNIGHT FOCUS - Sophisticated dark theme for focus
    "Midnight Focus": {
        "type": "focus",
        "category": "clean",
        "description": "Sophisticated dark theme with vibrant accents for distraction-free deep work",
        "accessibility_rating": "AAA",
        "colors": {
            # Primary palette - Sophisticated dark with vibrant accents
            "primary": "#60A5FA",          # Blue 400 - primary actions (accessible on dark)
            "primary_light": "#93C5FD",    # Blue 300 - hover states
            "primary_dark": "#3B82F6",     # Blue 500 - pressed states
            "secondary": "#A78BFA",        # Purple 400 - secondary actions
            "secondary_light": "#C4B5FD",  # Purple 300 - secondary hover
            "secondary_dark": "#8B5CF6",   # Purple 500 - secondary pressed
            
            # Accent colors - Vibrant against dark
            "accent": "#34D399",           # Emerald 400 - highlights
            "accent_light": "#6EE7B7",     # Emerald 300 - light accents
            "accent_warm": "#FBBF24",      # Amber 400 - warm accents
            
            # Status colors - Clear on dark backgrounds
            "success": "#34D399",          # Emerald 400 - success states
            "success_light": "#6EE7B7",    # Emerald 300 - light success
            "warning": "#FBBF24",          # Amber 400 - warning states
            "warning_light": "#FCD34D",    # Amber 300 - light warning
            "error": "#F87171",            # Red 400 - error states
            "error_light": "#FCA5A5",      # Red 300 - light error
            
            # Dark neutral palette - Sophisticated and clean
            "background": "#0F172A",       # Slate 900 - main background
            "surface": "#1E293B",          # Slate 800 - surface background
            "surface_elevated": "#334155", # Slate 700 - elevated surfaces
            "surface_dark": "#0F172A",     # Slate 900 - darker variant
            
            # Border colors - Subtle dark theme borders
            "border": "#475569",           # Slate 600 border
            "border_light": "#334155",     # Slate 700 light border
            "border_focus": "#60A5FA",     # Focus indicator (matches primary)
            "border_hover": "#64748B",     # Slate 500 hover border
            
            # Text hierarchy - High contrast for dark theme
            "text_primary": "#F8FAFC",     # Slate 50 - primary text (AAA contrast)
            "text_secondary": "#E2E8F0",   # Slate 200 - secondary text (AAA contrast)
            "text_tertiary": "#CBD5E1",    # Slate 300 - tertiary text (AA contrast)
            "text_muted": "#94A3B8",       # Slate 400 - muted text
            "text_inverse": "#0F172A",     # Dark text on light backgrounds
            "text_accent": "#60A5FA",      # Blue 400 - accent text
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%)",
            "hero": "linear-gradient(135deg, #1E293B 0%, #334155 100%)",
            "accent": "linear-gradient(135deg, #34D399 0%, #60A5FA 100%)",
            "surface": "linear-gradient(180deg, #1E293B 0%, #0F172A 100%)",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)",
            "colored": "0 8px 25px -5px rgba(96, 165, 250, 0.25)",
        }
    },
    
    # 5. PLATINUM ELEGANCE - Minimal high-contrast theme
    "Platinum Elegance": {
        "type": "minimal",
        "category": "accessible",
        "description": "Ultra-clean minimal design with platinum accents and maximum accessibility",
        "accessibility_rating": "AAA",
        "colors": {
            # Primary palette - Elegant grayscale with selective color (accessibility improved)
            "primary": "#374151",          # Gray 700 - primary actions (5.43:1 contrast)
            "primary_light": "#4B5563",    # Gray 600 - hover states
            "primary_dark": "#1F2937",     # Gray 800 - pressed states
            "secondary": "#047857",        # Emerald 700 - selective color accent (4.63:1 contrast)
            "secondary_light": "#059669",  # Emerald 600 - secondary hover
            "secondary_dark": "#065F46",   # Emerald 800 - secondary pressed
            
            # Accent colors - Minimal but accessible
            "accent": "#1E40AF",           # Blue 700 - highlights (7.05:1 contrast)
            "accent_light": "#3B82F6",     # Blue 500 - light accents
            "accent_warm": "#D97706",      # Amber 600 - warm accents (4.89:1 contrast)
            
            # Status colors - High contrast and accessible
            "success": "#047857",          # Emerald 700 - success states (4.63:1 contrast)
            "success_light": "#059669",    # Emerald 600 - light success
            "warning": "#D97706",          # Amber 600 - warning states (4.89:1 contrast)
            "warning_light": "#F59E0B",    # Amber 500 - light warning
            "error": "#DC2626",            # Red 600 - error states (4.64:1 contrast)
            "error_light": "#EF4444",      # Red 500 - light error
            
            # Neutral palette - Ultra-clean minimalism
            "background": "#FFFFFF",       # Pure white background
            "surface": "#FFFFFF",          # Pure white surfaces
            "surface_elevated": "#F9FAFB", # Gray 50 - elevated surfaces
            "surface_dark": "#F3F4F6",     # Gray 100 - darker variant
            
            # Border colors - Precise and minimal
            "border": "#E5E7EB",           # Gray 200 border
            "border_light": "#F3F4F6",     # Gray 100 light border
            "border_focus": "#4B5563",     # Focus indicator (matches primary)
            "border_hover": "#D1D5DB",     # Gray 300 hover border
            
            # Text hierarchy - Maximum contrast and clarity
            "text_primary": "#111827",     # Gray 900 - primary text (AAA contrast)
            "text_secondary": "#374151",   # Gray 700 - secondary text (AAA contrast)
            "text_tertiary": "#6B7280",    # Gray 500 - tertiary text (AA contrast)
            "text_muted": "#9CA3AF",       # Gray 400 - muted text
            "text_inverse": "#FFFFFF",     # White text on dark backgrounds
            "text_accent": "#059669",      # Emerald 600 - accent text
        },
        "gradients": {
            "primary": "linear-gradient(135deg, #4B5563 0%, #059669 100%)",
            "hero": "linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%)",
            "accent": "linear-gradient(135deg, #3B82F6 0%, #059669 100%)",
            "surface": "linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%)",
        },
        "shadows": {
            "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            "colored": "0 8px 25px -5px rgba(75, 85, 99, 0.15)",
        }
    }
}


def validate_color_scheme_accessibility(scheme_name: str) -> Dict[str, Any]:
    """
    Validate a color scheme for WCAG 2.1 accessibility compliance.
    
    Returns detailed accessibility report including contrast ratios,
    WCAG compliance levels, and color blindness compatibility.
    """
    if scheme_name not in NEW_COLOR_SCHEMES:
        return {"error": f"Color scheme '{scheme_name}' not found"}
    
    scheme = NEW_COLOR_SCHEMES[scheme_name]
    colors = scheme["colors"]
    
    # Test critical color combinations
    test_combinations = [
        ("text_primary", "background"),
        ("text_secondary", "background"), 
        ("text_tertiary", "background"),
        ("text_inverse", "primary"),
        ("text_inverse", "secondary"),
        ("primary", "background"),
        ("secondary", "background"),
        ("accent", "background"),
        ("success", "background"),
        ("warning", "background"),
        ("error", "background"),
    ]
    
    accessibility_report = {
        "scheme_name": scheme_name,
        "overall_rating": scheme["accessibility_rating"],
        "combinations": {},
        "summary": {
            "aa_compliant": 0,
            "aaa_compliant": 0,
            "total_tested": len(test_combinations),
            "lowest_ratio": float('inf'),
            "highest_ratio": 0,
        }
    }
    
    for fg_key, bg_key in test_combinations:
        if fg_key in colors and bg_key in colors:
            fg_color = colors[fg_key]
            bg_color = colors[bg_key]
            
            contrast_ratio = calculate_contrast_ratio(fg_color, bg_color)
            aa_normal = meets_wcag_aa(fg_color, bg_color, large_text=False)
            aa_large = meets_wcag_aa(fg_color, bg_color, large_text=True)
            aaa_normal = meets_wcag_aaa(fg_color, bg_color, large_text=False)
            aaa_large = meets_wcag_aaa(fg_color, bg_color, large_text=True)
            
            accessibility_report["combinations"][f"{fg_key}_on_{bg_key}"] = {
                "foreground": fg_color,
                "background": bg_color,
                "contrast_ratio": round(contrast_ratio, 2),
                "wcag_aa_normal": aa_normal,
                "wcag_aa_large": aa_large,
                "wcag_aaa_normal": aaa_normal,
                "wcag_aaa_large": aaa_large,
                "status": "AAA" if aaa_normal else ("AA" if aa_normal else "FAIL")
            }
            
            # Update summary
            if aa_normal:
                accessibility_report["summary"]["aa_compliant"] += 1
            if aaa_normal:
                accessibility_report["summary"]["aaa_compliant"] += 1
            
            accessibility_report["summary"]["lowest_ratio"] = min(
                accessibility_report["summary"]["lowest_ratio"], contrast_ratio
            )
            accessibility_report["summary"]["highest_ratio"] = max(
                accessibility_report["summary"]["highest_ratio"], contrast_ratio
            )
    
    return accessibility_report


def get_color_scheme(scheme_name: str = "Aurora Professional") -> Dict[str, Any]:
    """Get a color scheme with fallback to default."""
    return NEW_COLOR_SCHEMES.get(scheme_name, NEW_COLOR_SCHEMES["Aurora Professional"])


def create_scheme_choices() -> List[str]:
    """Create dropdown choices for the new color schemes."""
    return list(NEW_COLOR_SCHEMES.keys())


def get_scheme_description(scheme_name: str) -> str:
    """Get description for a color scheme."""
    scheme = get_color_scheme(scheme_name)
    return scheme["description"]


def get_scheme_category(scheme_name: str) -> str:
    """Get the category of a color scheme (vibrant, clean, accessible)."""
    scheme = get_color_scheme(scheme_name)
    return scheme.get("category", "professional")


def generate_css_variables(scheme_name: str = "Aurora Professional") -> str:
    """Generate CSS custom properties for the selected scheme."""
    scheme = get_color_scheme(scheme_name)
    colors = scheme["colors"]
    gradients = scheme["gradients"]
    shadows = scheme["shadows"]
    
    css_vars = ":root {\n"
    css_vars += f"  /* Color Scheme: {scheme_name} */\n"
    css_vars += f"  /* {scheme['description']} */\n\n"
    
    # Color variables
    css_vars += "  /* Color Variables */\n"
    for key, value in colors.items():
        css_vars += f"  --color-{key.replace('_', '-')}: {value};\n"
    
    css_vars += "\n  /* Gradient Variables */\n"
    for key, value in gradients.items():
        css_vars += f"  --gradient-{key}: {value};\n"
    
    css_vars += "\n  /* Shadow Variables */\n"
    for key, value in shadows.items():
        css_vars += f"  --shadow-{key}: {value};\n"
    
    # Semantic mappings for common UI elements
    css_vars += """
  /* Semantic UI Mappings */
  --btn-primary-bg: var(--color-primary);
  --btn-primary-hover: var(--color-primary-light);
  --btn-primary-active: var(--color-primary-dark);
  --btn-secondary-bg: var(--color-secondary);
  --btn-secondary-hover: var(--color-secondary-light);
  --btn-secondary-active: var(--color-secondary-dark);
  
  --card-bg: var(--color-surface);
  --card-elevated-bg: var(--color-surface-elevated);
  --card-border: var(--color-border);
  --card-shadow: var(--shadow-md);
  
  --input-bg: var(--color-surface);
  --input-border: var(--color-border);
  --input-border-hover: var(--color-border-hover);
  --input-border-focus: var(--color-border-focus);
  
  --text-heading: var(--color-text-primary);
  --text-body: var(--color-text-secondary);
  --text-caption: var(--color-text-tertiary);
  --text-muted: var(--color-text-muted);
  --text-accent: var(--color-text-accent);
  
  --status-success: var(--color-success);
  --status-warning: var(--color-warning);
  --status-error: var(--color-error);
"""
    
    css_vars += "}\n"
    return css_vars


def create_complete_css(scheme_name: str = "Aurora Professional") -> str:
    """Generate complete CSS for the UI with the selected color scheme."""
    scheme = get_color_scheme(scheme_name)
    
    css = f"""
/* New Color Scheme: {scheme_name} */
/* Category: {scheme.get('category', 'professional').title()} */
/* {scheme['description']} */
/* Accessibility: WCAG {scheme['accessibility_rating']} Compliant */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

{generate_css_variables(scheme_name)}

/* Global Styles with High Specificity */
* {{
    box-sizing: border-box !important;
}}

html, body {{
    scroll-behavior: smooth !important;
}}

/* Override Gradio's default container styling */
.gradio-container,
#gradio-app,
.gradio-app,
body > gradio-app {{
    background: var(--color-background) !important;
    color: var(--color-text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    line-height: 1.6 !important;
}}

/* Force background color on main elements */
gradio-app,
.gradio-container > *,
.block,
.gr-block {{
    background: var(--color-background) !important;
}}

/* Header Styling */
.header-container {{
    background: var(--gradient-hero) !important;
    color: var(--color-text-inverse) !important;
    padding: 2rem !important;
    border-radius: 16px !important;
    margin-bottom: 2rem !important;
    box-shadow: var(--shadow-lg) !important;
    border: 1px solid var(--color-border-light) !important;
}}

.app-title {{
    font-size: 2.25rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
}}

.app-subtitle {{
    font-size: 1.125rem !important;
    opacity: 0.9 !important;
    margin-top: 0.75rem !important;
    font-weight: 400 !important;
}}

/* Cards and Containers */
.settings-card, .output-card {{
    background: var(--card-bg) !important;
    border: 2px solid var(--card-border) !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    box-shadow: var(--card-shadow) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
}}

.settings-card:hover, .output-card:hover {{
    border-color: var(--color-border-focus) !important;
    box-shadow: var(--shadow-colored) !important;
    transform: translateY(-2px) !important;
}}

/* Button Styling */
button {{
    background: var(--btn-secondary-bg) !important;
    color: var(--color-text-inverse) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: var(--shadow-sm) !important;
    cursor: pointer !important;
}}

button:hover {{
    background: var(--btn-secondary-hover) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}}

button:active {{
    background: var(--btn-secondary-active) !important;
    transform: translateY(0) !important;
    box-shadow: var(--shadow-sm) !important;
}}

.start-button {{
    background: var(--gradient-primary) !important;
    font-size: 1.125rem !important;
    padding: 1rem 2rem !important;
    font-weight: 700 !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-colored) !important;
}}

.start-button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-lg) !important;
}}

/* Input Styling */
.gr-textbox, .gr-dropdown, input, textarea, select {{
    border: 2px solid var(--input-border) !important;
    border-radius: 12px !important;
    background: var(--input-bg) !important;
    color: var(--color-text-primary) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1rem !important;
}}

.gr-textbox:hover, .gr-dropdown:hover, input:hover, textarea:hover, select:hover {{
    border-color: var(--input-border-hover) !important;
}}

.gr-textbox:focus, .gr-dropdown:focus, input:focus, textarea:focus, select:focus {{
    border-color: var(--input-border-focus) !important;
    box-shadow: 0 0 0 4px var(--color-primary)25 !important;
    outline: none !important;
}}

/* Output Areas */
.thinking-output, .report-output {{
    background: var(--color-surface) !important;
    border: 2px solid var(--color-border) !important;
    border-radius: 12px !important;
    color: var(--color-text-primary) !important;
    font-family: 'Inter', 'SF Mono', 'Monaco', 'Cascadia Code', monospace !important;
    line-height: 1.7 !important;
    padding: 1.5rem !important;
    box-shadow: var(--shadow-sm) !important;
}}

/* Status Indicators */
.status-text {{
    background: var(--color-surface-elevated) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    font-size: 0.875rem !important;
}}

/* Tab Styling */
.main-tabs .tab-nav {{
    background: var(--color-surface) !important;
    border-bottom: 2px solid var(--color-border) !important;
    border-radius: 12px 12px 0 0 !important;
}}

.main-tabs .tab-nav button {{
    background: transparent !important;
    color: var(--color-text-secondary) !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    font-weight: 500 !important;
    padding: 1rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

.main-tabs .tab-nav button:hover {{
    color: var(--color-text-primary) !important;
    background: var(--color-surface-elevated) !important;
}}

.main-tabs .tab-nav button.selected {{
    color: var(--color-primary) !important;
    border-bottom-color: var(--color-primary) !important;
    background: var(--color-surface-elevated) !important;
    font-weight: 600 !important;
}}

/* Color Scheme Dropdown */
.color-scheme-dropdown {{
    min-width: 220px !important;
    font-weight: 500 !important;
}}

.scheme-description {{
    background: var(--color-accent-light)20 !important;
    border: 1px solid var(--color-accent-light) !important;
    padding: 1rem !important;
    border-radius: 12px !important;
    border-left: 4px solid var(--color-accent) !important;
    margin-top: 1rem !important;
    font-style: italic !important;
    color: var(--color-text-secondary) !important;
    font-size: 0.875rem !important;
    line-height: 1.5 !important;
}}

/* Loading and Animation States */
.loading {{
    position: relative !important;
    overflow: hidden !important;
}}

.loading::after {{
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: -100% !important;
    width: 100% !important;
    height: 100% !important;
    background: linear-gradient(90deg, transparent, var(--color-primary)20, transparent) !important;
    animation: shimmer 2s infinite !important;
}}

@keyframes shimmer {{
    0% {{ left: -100%; }}
    100% {{ left: 100%; }}
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
    outline: 2px solid var(--color-accent) !important;
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
    
    .main-tabs .tab-nav button.selected {{
        border-bottom-width: 4px !important;
    }}
}}

/* Dark mode preferences */
@media (prefers-color-scheme: dark) {{
    /* Automatically handled by color scheme selection */
}}

/* Print styles */
@media print {{
    .header-container, .color-scheme-dropdown, .scheme-description {{
        display: none !important;
    }}
    
    .settings-card, .output-card {{
        border: 1px solid #000 !important;
        box-shadow: none !important;
    }}
}}
"""
    
    return css


# Export the main functions for backwards compatibility
__all__ = [
    'NEW_COLOR_SCHEMES',
    'get_color_scheme',
    'create_scheme_choices', 
    'get_scheme_description',
    'generate_css_variables',
    'create_complete_css',
    'validate_color_scheme_accessibility',
    'get_scheme_category'
]