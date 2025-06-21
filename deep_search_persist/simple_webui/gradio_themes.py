"""
Simplified Gradio Native Theme System
Using Gradio's built-in theming capabilities for better performance and reliability.
"""

import gradio as gr
from typing import Dict, Any


def create_aurora_theme() -> gr.Theme:
    """Aurora Professional - Modern blue-purple gradient theme."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple", 
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Primary colors - Aurora blues and purples
        color_accent="#1E40AF",
        color_accent_soft="#3B82F6",
        
        # Background colors
        body_background_fill="#FAFBFC",
        background_fill_primary="#FFFFFF",
        background_fill_secondary="#F8FAFC",
        
        # Button styling
        button_primary_background_fill="#1E40AF",
        button_primary_background_fill_hover="#3B82F6",
        button_primary_text_color="#FFFFFF",
        button_secondary_background_fill="#7C3AED",
        button_secondary_background_fill_hover="#8B5CF6",
        
        # Input styling
        input_background_fill="#FFFFFF",
        input_border_color="#E2E8F0",
        input_border_color_focus="#3B82F6",
        
        # Text colors
        body_text_color="#0F172A",
        body_text_color_subdued="#334155",
        
        # Block styling
        block_background_fill="#FFFFFF",
        block_border_color="#E2E8F0",
        block_radius="12px",
        block_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        
        # Panel styling
        panel_background_fill="#F8FAFC",
        panel_border_color="#E2E8F0",
    )


def create_emerald_theme() -> gr.Theme:
    """Emerald Research - Clean green theme for focused work."""
    return gr.themes.Soft(
        primary_hue="emerald",
        secondary_hue="cyan",
        neutral_hue="slate", 
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Primary colors - Sophisticated greens
        color_accent="#047857",
        color_accent_soft="#059669",
        
        # Background colors
        body_background_fill="#F0FDF4",
        background_fill_primary="#FFFFFF",
        background_fill_secondary="#ECFDF5",
        
        # Button styling
        button_primary_background_fill="#047857",
        button_primary_background_fill_hover="#059669",
        button_primary_text_color="#FFFFFF",
        button_secondary_background_fill="#0E7490",
        button_secondary_background_fill_hover="#0891B2",
        
        # Input styling
        input_background_fill="#FFFFFF",
        input_border_color="#D1FAE5",
        input_border_color_focus="#059669",
        
        # Text colors
        body_text_color="#064E3B",
        body_text_color_subdued="#065F46",
        
        # Block styling
        block_background_fill="#FFFFFF",
        block_border_color="#D1FAE5",
        block_radius="12px",
        block_shadow="0 4px 6px -1px rgba(5, 150, 105, 0.1)",
        
        # Panel styling
        panel_background_fill="#ECFDF5",
        panel_border_color="#D1FAE5",
    )


def create_coral_theme() -> gr.Theme:
    """Coral Innovation - Vibrant coral-orange theme for creativity."""
    return gr.themes.Soft(
        primary_hue="orange",
        secondary_hue="pink",
        neutral_hue="stone",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Primary colors - Vibrant coral and orange
        color_accent="#EA580C",
        color_accent_soft="#F97316",
        
        # Background colors
        body_background_fill="#FFFBF5",
        background_fill_primary="#FFFFFF",
        background_fill_secondary="#FEF3E2",
        
        # Button styling
        button_primary_background_fill="#EA580C",
        button_primary_background_fill_hover="#F97316",
        button_primary_text_color="#FFFFFF",
        button_secondary_background_fill="#DB2777",
        button_secondary_background_fill_hover="#EC4899",
        
        # Input styling
        input_background_fill="#FFFFFF",
        input_border_color="#FED7AA",
        input_border_color_focus="#F97316",
        
        # Text colors
        body_text_color="#1C1917",
        body_text_color_subdued="#44403C",
        
        # Block styling
        block_background_fill="#FFFFFF",
        block_border_color="#FED7AA",
        block_radius="12px",
        block_shadow="0 4px 6px -1px rgba(249, 115, 22, 0.1)",
        
        # Panel styling
        panel_background_fill="#FEF3E2",
        panel_border_color="#FED7AA",
    )


def create_midnight_theme() -> gr.Theme:
    """Midnight Focus - Sophisticated dark theme for focus."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Primary colors - Sophisticated dark with vibrant accents
        color_accent="#60A5FA",
        color_accent_soft="#93C5FD",
        
        # Background colors - Dark theme
        body_background_fill="#0F172A",
        background_fill_primary="#1E293B",
        background_fill_secondary="#334155",
        
        # Button styling
        button_primary_background_fill="#60A5FA",
        button_primary_background_fill_hover="#93C5FD",
        button_primary_text_color="#0F172A",
        button_secondary_background_fill="#A78BFA",
        button_secondary_background_fill_hover="#C4B5FD",
        
        # Input styling
        input_background_fill="#1E293B",
        input_border_color="#475569",
        input_border_color_focus="#60A5FA",
        
        # Text colors - High contrast for dark theme
        body_text_color="#F8FAFC",
        body_text_color_subdued="#E2E8F0",
        
        # Block styling
        block_background_fill="#1E293B",
        block_border_color="#475569",
        block_radius="12px",
        block_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.4)",
        
        # Panel styling
        panel_background_fill="#334155",
        panel_border_color="#475569",
    )


def create_platinum_theme() -> gr.Theme:
    """Platinum Elegance - Minimal high-contrast theme."""
    return gr.themes.Soft(
        primary_hue="gray",
        secondary_hue="emerald",
        neutral_hue="gray",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Primary colors - Elegant grayscale with selective color
        color_accent="#374151",
        color_accent_soft="#4B5563",
        
        # Background colors - Ultra-clean minimalism
        body_background_fill="#FFFFFF",
        background_fill_primary="#FFFFFF",
        background_fill_secondary="#F9FAFB",
        
        # Button styling
        button_primary_background_fill="#374151",
        button_primary_background_fill_hover="#4B5563",
        button_primary_text_color="#FFFFFF",
        button_secondary_background_fill="#047857",
        button_secondary_background_fill_hover="#059669",
        
        # Input styling
        input_background_fill="#FFFFFF",
        input_border_color="#E5E7EB",
        input_border_color_focus="#4B5563",
        
        # Text colors - Maximum contrast and clarity
        body_text_color="#111827",
        body_text_color_subdued="#374151",
        
        # Block styling
        block_background_fill="#FFFFFF",
        block_border_color="#E5E7EB",
        block_radius="8px",
        block_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
        
        # Panel styling
        panel_background_fill="#F9FAFB",
        panel_border_color="#E5E7EB",
    )


# Theme registry
GRADIO_THEMES: Dict[str, Any] = {
    "Aurora Professional": create_aurora_theme,
    "Emerald Research": create_emerald_theme,
    "Coral Innovation": create_coral_theme,
    "Midnight Focus": create_midnight_theme,
    "Platinum Elegance": create_platinum_theme,
}


def get_theme_choices() -> list[str]:
    """Get list of available theme names."""
    return list(GRADIO_THEMES.keys())


def get_theme(theme_name: str) -> gr.Theme:
    """Get a Gradio theme by name."""
    if theme_name in GRADIO_THEMES:
        return GRADIO_THEMES[theme_name]()
    return GRADIO_THEMES["Aurora Professional"]()


def get_theme_description(theme_name: str) -> str:
    """Get description for a theme."""
    descriptions = {
        "Aurora Professional": "Modern aurora-inspired gradient with professional polish",
        "Emerald Research": "Clean emerald green for focused research and analysis", 
        "Coral Innovation": "Vibrant coral and warm orange for innovative thinking",
        "Midnight Focus": "Sophisticated dark theme for distraction-free deep work",
        "Platinum Elegance": "Ultra-clean minimal design with maximum accessibility",
    }
    return descriptions.get(theme_name, "Professional theme")


# Persistence functions
COLOR_SCHEME_FILE = "/tmp/gradio_color_scheme.txt"


def get_saved_theme() -> str:
    """Get the saved theme from file."""
    try:
        import os
        if os.path.exists(COLOR_SCHEME_FILE):
            with open(COLOR_SCHEME_FILE, 'r') as f:
                theme = f.read().strip()
                if theme in GRADIO_THEMES:
                    return theme
    except Exception:
        pass
    return "Aurora Professional"


def save_theme(theme_name: str) -> None:
    """Save the theme to file."""
    try:
        with open(COLOR_SCHEME_FILE, 'w') as f:
            f.write(theme_name)
    except Exception:
        pass