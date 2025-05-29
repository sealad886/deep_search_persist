# Color space conversion utilities
def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")

    try:
        return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"Invalid hex color: {hex_color}")


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex string."""
    r, g, b = [max(0, min(255, int(x))) for x in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r, g, b):
    """
    Convert RGB values to HSL (Hue, Saturation, Lightness).

    Args:
        r, g, b: RGB values (0-255)

    Returns:
        Tuple (h, s, l) where h is in degrees (0-360), s and l are 0-1
    """
    # Normalize RGB values to 0-1
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val

    # Calculate lightness
    l: float = (max_val + min_val) / 2.0

    if delta == 0:
        # Achromatic (no color)
        h = 0
        s = 0
    else:
        # Calculate saturation
        if l < 0.5:
            s = delta / (max_val + min_val)
        else:
            s = delta / (2.0 - max_val - min_val)

        # Calculate hue
        if max_val == r:
            h = ((g - b) / delta + (6 if g < b else 0)) / 6.0
        elif max_val == g:
            h = ((b - r) / delta + 2) / 6.0
        else:  # max_val == b
            h = ((r - g) / delta + 4) / 6.0

        h *= 360  # Convert to degrees

    return h, s, l


def hsl_to_rgb(h, s, lx):
    """
    Convert HSL values to RGB.

    Args:
        h: Hue in degrees (0-360)
        s: Saturation (0-1)
        l: Lightness (0-1)

    Returns:
        Tuple (r, g, b) with values 0-255
    """
    # Normalize hue to 0-1
    h = (h % 360) / 360.0

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        return p + (q - p) * (2 / 3 - t) * 6 if t < 2 / 3 else p

    if s == 0:
        # Achromatic
        r = g = b = lx
    else:
        q = lx * (1 + s) if lx < 0.5 else lx + s - lx * s
        p = 2 * lx - q

        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    # Convert to 0-255 range
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rgb_to_linear(rgb_component):
    """Convert sRGB component to linear RGB for luminance calculation."""
    # Normalize to 0-1 range
    c = rgb_component / 255.0

    # Apply gamma correction (sRGB to linear)
    return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)


def get_relative_luminance(hex_color):
    """Calculate relative luminance according to WCAG 2.1 specification."""
    r, g, b = hex_to_rgb(hex_color)

    # Convert to linear RGB
    r_linear = rgb_to_linear(r)
    g_linear = rgb_to_linear(g)
    b_linear = rgb_to_linear(b)

    # Calculate relative luminance using WCAG formula
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
