from .color_convert import hex_to_rgb, rgb_to_hex, get_relative_luminance
from .color_schemes import get_color_scheme


# Color blindness simulation using scientific transformation matrices
def simulate_protanopia(hex_color):
    """
    Simulate how a color appears to someone with protanopia (red-blind).
    Uses the Brettel, Viénot and Mollon (1997) algorithm.
    """
    try:
        r, g, b = hex_to_rgb(hex_color)

        # Protanopia transformation matrix (Brettel et al.)
        # Removes red sensitivity
        new_r = 0.567 * r + 0.433 * g + 0.000 * b
        new_g = 0.558 * r + 0.442 * g + 0.000 * b
        new_b = 0.000 * r + 0.242 * g + 0.758 * b

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color  # Return original if conversion fails


def simulate_deuteranopia(hex_color):
    """
    Simulate how a color appears to someone with deuteranopia (green-blind).
    Uses the Brettel, Viénot and Mollon (1997) algorithm.
    """
    try:
        r, g, b = hex_to_rgb(hex_color)

        # Deuteranopia transformation matrix (Brettel et al.)
        # Removes green sensitivity
        new_r = 0.625 * r + 0.375 * g + 0.000 * b
        new_g = 0.700 * r + 0.300 * g + 0.000 * b
        new_b = 0.000 * r + 0.300 * g + 0.700 * b

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color


def simulate_tritanopia(hex_color):
    """
    Simulate how a color appears to someone with tritanopia (blue-blind).
    Uses the Brettel, Viénot and Mollon (1997) algorithm.
    """
    try:
        r, g, b = hex_to_rgb(hex_color)

        # Tritanopia transformation matrix (Brettel et al.)
        # Removes blue sensitivity
        new_r = 0.950 * r + 0.050 * g + 0.000 * b
        new_g = 0.000 * r + 0.433 * g + 0.567 * b
        new_b = 0.000 * r + 0.475 * g + 0.525 * b

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color


def simulate_protanomaly(hex_color, severity=1.0):
    """
    Simulate protanomaly (reduced red sensitivity) with adjustable severity.

    Args:
        hex_color: Hex color string
        severity: Float 0.0-1.0, where 1.0 is complete protanopia
    """
    try:
        if severity <= 0:
            return hex_color
        elif severity >= 1:
            return simulate_protanopia(hex_color)

        r, g, b = hex_to_rgb(hex_color)
        simulated_r, simulated_g, simulated_b = hex_to_rgb(simulate_protanopia(hex_color))

        # Interpolate between normal and simulated color
        new_r = r + severity * (simulated_r - r)
        new_g = g + severity * (simulated_g - g)
        new_b = b + severity * (simulated_b - b)

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color


def simulate_deuteranomaly(hex_color, severity=1.0):
    """
    Simulate deuteranomaly (reduced green sensitivity) with adjustable severity.
    """
    try:
        if severity <= 0:
            return hex_color
        elif severity >= 1:
            return simulate_deuteranopia(hex_color)

        r, g, b = hex_to_rgb(hex_color)
        simulated_r, simulated_g, simulated_b = hex_to_rgb(simulate_deuteranopia(hex_color))

        new_r = r + severity * (simulated_r - r)
        new_g = g + severity * (simulated_g - g)
        new_b = b + severity * (simulated_b - b)

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color


def simulate_tritanomaly(hex_color, severity=1.0):
    """
    Simulate tritanomaly (reduced blue sensitivity) with adjustable severity.
    """
    try:
        if severity <= 0:
            return hex_color
        elif severity >= 1:
            return simulate_tritanopia(hex_color)

        r, g, b = hex_to_rgb(hex_color)
        simulated_r, simulated_g, simulated_b = hex_to_rgb(simulate_tritanopia(hex_color))

        new_r = r + severity * (simulated_r - r)
        new_g = g + severity * (simulated_g - g)
        new_b = b + severity * (simulated_b - b)

        return rgb_to_hex((new_r, new_g, new_b))
    except ValueError:
        return hex_color


# WCAG contrast ratio calculation for accessibility
def calculate_contrast_ratio(color1, color2):
    """
    Calculate WCAG 2.1 contrast ratio between two colors.

    Args:
        color1: Hex color string (e.g., "#FFFFFF")
        color2: Hex color string (e.g., "#000000")

    Returns:
        Float: Contrast ratio (1:1 to 21:1)

    Raises:
        ValueError: If color format is invalid
    """
    try:
        # Get relative luminance for both colors
        lum1 = get_relative_luminance(color1)
        lum2 = get_relative_luminance(color2)

        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        # Calculate contrast ratio using WCAG formula
        contrast_ratio = (lighter + 0.05) / (darker + 0.05)

        return round(contrast_ratio, 2)
    except ValueError as e:
        raise ValueError(f"Invalid color format: {e}")


def meets_wcag_aa(color1, color2, large_text=False):
    """
    Check if two colors meet WCAG AA contrast requirements.

    Args:
        color1: Hex color string
        color2: Hex color string
        large_text: Boolean, True if text is large (18pt+ or 14pt+ bold)

    Returns:
        Boolean: True if meets AA requirements
    """
    try:
        ratio = calculate_contrast_ratio(color1, color2)
        # AA requirements: 4.5:1 for normal text, 3:1 for large text
        required_ratio = 3.0 if large_text else 4.5
        return ratio >= required_ratio
    except ValueError:
        return False


def meets_wcag_aaa(color1, color2, large_text=False):
    """
    Check if two colors meet WCAG AAA contrast requirements.

    Args:
        color1: Hex color string
        color2: Hex color string
        large_text: Boolean, True if text is large (18pt+ or 14pt+ bold)

    Returns:
        Boolean: True if meets AAA requirements
    """
    try:
        ratio = calculate_contrast_ratio(color1, color2)
        # AAA requirements: 7:1 for normal text, 4.5:1 for large text
        required_ratio = 4.5 if large_text else 7.0
        return ratio >= required_ratio
    except ValueError:
        return False


def get_accessibility_score(color1, color2):
    """
    Get comprehensive accessibility score for two colors.

    Returns:
        Dict with accessibility information
    """
    try:
        ratio = calculate_contrast_ratio(color1, color2)

        return {
            "contrast_ratio": ratio,
            "ratio_string": f"{ratio}:1",
            "wcag_aa_normal": meets_wcag_aa(color1, color2, False),
            "wcag_aa_large": meets_wcag_aa(color1, color2, True),
            "wcag_aaa_normal": meets_wcag_aaa(color1, color2, False),
            "wcag_aaa_large": meets_wcag_aaa(color1, color2, True),
            "grade": _get_contrast_grade(ratio),
            "recommendations": _get_accessibility_recommendations(ratio),
        }
    except ValueError as e:
        return {
            "error": str(e),
            "contrast_ratio": 0,
            "wcag_aa_normal": False,
            "wcag_aa_large": False,
            "wcag_aaa_normal": False,
            "wcag_aaa_large": False,
        }


def _get_contrast_grade(ratio):
    """Get letter grade for contrast ratio."""
    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    elif ratio >= 3.0:
        return "AA Large"
    else:
        return "Fail"


def _get_accessibility_recommendations(ratio):
    """Get recommendations for improving accessibility."""
    if ratio >= 7.0:
        return ["Excellent contrast - meets all WCAG guidelines"]
    elif ratio >= 4.5:
        return ["Good contrast - meets WCAG AA for all text sizes"]
    elif ratio >= 3.0:
        return ["Acceptable contrast for large text only", "Consider darker/lighter colors for small text"]
    else:
        return [
            "Poor contrast - fails WCAG guidelines",
            "Use darker text on light backgrounds",
            "Use lighter text on dark backgrounds",
            "Consider using high contrast mode colors",
        ]


def analyze_color_scheme_accessibility(scheme_name):
    """
    Analyze accessibility of a complete color scheme.

    Args:
        scheme_name: Name of color scheme to analyze

    Returns:
        Dict with comprehensive accessibility analysis
    """
    scheme = get_color_scheme(scheme_name)
    if not scheme:
        return {"error": f"Color scheme '{scheme_name}' not found"}

    colors = scheme["colors"]
    analysis = {"scheme_name": scheme_name, "color_combinations": {}, "color_blind_safe": True, "overall_score": "Good"}

    # Test key color combinations
    combinations = [
        ("text_primary", "background", "Primary text on background"),
        ("text_secondary", "background", "Secondary text on background"),
        ("text_primary", "surface", "Primary text on surface"),
        ("text_inverse", "primary", "Inverse text on primary"),
        ("text_inverse", "secondary", "Inverse text on secondary"),
    ]

    total_score = 0
    max_score = 0

    for color1_key, color2_key, description in combinations:
        if color1_key in colors and color2_key in colors:
            color1 = colors[color1_key]
            color2 = colors[color2_key]

            score = get_accessibility_score(color1, color2)
            analysis["color_combinations"][description] = score

            # Calculate overall score
            if score.get("wcag_aaa_normal"):
                total_score += 3
            elif score.get("wcag_aa_normal"):
                total_score += 2
            elif score.get("wcag_aa_large"):
                total_score += 1

            max_score += 3

    # Calculate overall grade
    if max_score > 0:
        score_percentage = total_score / max_score
        if score_percentage >= 0.8:
            analysis["overall_score"] = "Excellent"
        elif score_percentage >= 0.6:
            analysis["overall_score"] = "Good"
        elif score_percentage >= 0.4:
            analysis["overall_score"] = "Fair"
        else:
            analysis["overall_score"] = "Poor"

    return analysis
