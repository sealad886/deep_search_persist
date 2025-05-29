"""
CAM16-UCS Color Space Implementation
Provides perceptually uniform color space conversions for accessibility-focused color generation.

Based on:
- CIECAM02/CAM16 color appearance model
- CAM16-UCS uniform color space
- Optimized for hue step accessibility requirements
"""

import math
from typing import Tuple, List
from dataclasses import dataclass

# Import centralized logger from deep_search_persist
from ...deep_search_persist.logging.logging_config import logger


@dataclass
class ViewingConditions:
    """Standard viewing conditions for CAM16 calculations."""
    
    # Standard illuminant D65 white point
    white_point: Tuple[float, float, float] = (95.047, 100.0, 108.883)
    # Average luminance (cd/m²)
    la: float = 64.0
    # Background luminance factor
    yb: float = 20.0
    # Surround conditions (1=average, 0.9=dim, 0.8=dark)
    c: float = 0.69
    nc: float = 1.0
    f: float = 1.0


# CAM16 transformation matrices and constants
XYZ_TO_CAM16_RGB = [
    [0.401288, 0.650173, -0.051461],
    [-0.250268, 1.204414, 0.045854],
    [-0.002079, 0.048952, 0.953127]
]

CAM16_RGB_TO_XYZ = [
    [1.8620678, -1.0112547, 0.1491867],
    [0.3875265, 0.6214474, -0.0089739],
    [-0.0158415, -0.0344411, 1.0502856]
]


def _matrix_multiply(matrix: List[List[float]], vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Multiply 3x3 matrix by 3x1 vector."""
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
        matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
    )


def _adapt_luminance(component: float, fl: float) -> float:
    """Apply luminance adaptation function."""
    abs_component = abs(component)
    adapted = (400.0 * (fl * abs_component / 100.0)) / (27.13 + (fl * abs_component / 100.0))
    return math.copysign(adapted, component)


def _inverse_adapt_luminance(adapted: float, fl: float) -> float:
    """Inverse luminance adaptation function."""
    abs_adapted = abs(adapted)
    component = (100.0 / fl) * (27.13 * abs_adapted) / (400.0 - abs_adapted)
    return math.copysign(component, adapted)


def xyz_to_cam16(xyz: Tuple[float, float, float],
                 viewing_conditions: ViewingConditions = ViewingConditions()) -> Tuple[float, float, float]:
    """
    Convert XYZ to CAM16 color appearance coordinates.
    
    Args:
        xyz: XYZ color coordinates (0-100 scale)
        viewing_conditions: Viewing conditions for adaptation
        
    Returns:
        Tuple of (J, C, h) where:
        - J: Lightness (0-100)
        - C: Chroma (0-100+)
        - h: Hue angle (0-360 degrees)
        
    Raises:
        ValueError: If XYZ values are outside valid range (0-100)
        TypeError: If input values are not numeric
    """
    # Input validation
    if not isinstance(xyz, (tuple, list)) or len(xyz) != 3:
        raise TypeError("XYZ input must be a tuple or list of 3 numeric values")
    
    try:
        x, y, z = float(xyz[0]), float(xyz[1]), float(xyz[2])
    except (ValueError, TypeError) as e:
        raise TypeError(f"XYZ values must be numeric: {e}")
    
    # Validate XYZ ranges (0-100 scale)
    if not all(0 <= val <= 100 for val in [x, y, z]):
        raise ValueError(f"XYZ values must be in 0-100 range, got: ({x:.2f}, {y:.2f}, {z:.2f})")
    
    # Convert to CAM16 RGB
    rgb = _matrix_multiply(XYZ_TO_CAM16_RGB, (x, y, z))
    
    # Calculate adaptation factor
    k = 1.0 / (5.0 * viewing_conditions.la + 1.0)
    fl = (0.2 * (k ** 4) * (5.0 * viewing_conditions.la) +
          0.1 * ((1.0 - k ** 4) ** 2) * ((5.0 * viewing_conditions.la) ** (1.0/3.0)))
    
    # Adapt to viewing conditions
    adapted_rgb = tuple(_adapt_luminance(c, fl) for c in rgb)
    
    # Calculate preliminary values
    a = adapted_rgb[0] - 12.0 * adapted_rgb[1] / 11.0 + adapted_rgb[2] / 11.0
    b = (adapted_rgb[0] + adapted_rgb[1] - 2.0 * adapted_rgb[2]) / 9.0
    
    # Calculate hue angle
    h = math.degrees(math.atan2(b, a)) % 360.0
    
    # Calculate eccentricity and hue composition
    h_rad = math.radians(h)
    et = 0.25 * (math.cos(h_rad + 2.0) + 3.8)
    
    # Calculate achromatic response
    a_achromatic = (2.0 * adapted_rgb[0] + adapted_rgb[1] + adapted_rgb[2] / 20.0 - 0.305) * viewing_conditions.nc
    
    # Calculate lightness
    j = 100.0 * (a_achromatic / viewing_conditions.yb) ** (viewing_conditions.c * viewing_conditions.f)
    
    # Calculate chroma with numerical stability
    numerator = (50000.0 / 13.0 * viewing_conditions.nc * viewing_conditions.f *
                 et * math.sqrt(a * a + b * b))
    denominator = adapted_rgb[0] + adapted_rgb[1] + 21.0 * adapted_rgb[2] / 20.0 + 1e-10  # Prevent division by zero
    t = numerator / denominator
    c = (t ** 0.9) * math.sqrt(j / 100.0) * (1.64 - 0.29 ** viewing_conditions.yb) ** 0.73
    
    return (j, c, h)


def cam16_to_xyz(jch: Tuple[float, float, float],
                 viewing_conditions: ViewingConditions = ViewingConditions()) -> Tuple[float, float, float]:
    """
    Convert CAM16 color appearance coordinates to XYZ.
    
    Args:
        jch: CAM16 coordinates (J, C, h)
        viewing_conditions: Viewing conditions for adaptation
        
    Returns:
        XYZ color coordinates (0-100 scale)
        
    Raises:
        ValueError: If JCH values are outside valid ranges
        TypeError: If input values are not numeric
    """
    # Input validation
    if not isinstance(jch, (tuple, list)) or len(jch) != 3:
        raise TypeError("JCH input must be a tuple or list of 3 numeric values")
    
    try:
        j, c, h = float(jch[0]), float(jch[1]), float(jch[2])
    except (ValueError, TypeError) as e:
        raise TypeError(f"JCH values must be numeric: {e}")
    
    # Validate JCH ranges
    if not (0 <= j <= 100):
        raise ValueError(f"Lightness (J) must be in 0-100 range, got: {j:.2f}")
    if c < 0:
        raise ValueError(f"Chroma (C) must be non-negative, got: {c:.2f}")
    if not (0 <= h <= 360):
        # Normalize hue to 0-360 range
        h = h % 360.0
        logger.debug(f"Normalized hue angle to: {h:.2f}")
    
    if j == 0:
        return (0.0, 0.0, 0.0)
    
    # Calculate adaptation factor
    k = 1.0 / (5.0 * viewing_conditions.la + 1.0)
    fl = (0.2 * (k ** 4) * (5.0 * viewing_conditions.la) +
          0.1 * ((1.0 - k ** 4) ** 2) * ((5.0 * viewing_conditions.la) ** (1.0/3.0)))
    
    # Calculate intermediate values
    h_rad = math.radians(h)
    et = 0.25 * (math.cos(h_rad + 2.0) + 3.8)
    
    a_achromatic = viewing_conditions.yb * (j / 100.0) ** (1.0 / (viewing_conditions.c * viewing_conditions.f))
    
    t = c / (math.sqrt(j / 100.0) * (1.64 - 0.29 ** viewing_conditions.yb) ** 0.73)
    t = t ** (1.0 / 0.9)
    
    # Calculate a and b
    alpha = c * math.cos(h_rad)
    beta = c * math.sin(h_rad)
    
    # Solve for adapted RGB with numerical stability
    denom_factor = (50000.0 / 13.0 * viewing_conditions.nc * viewing_conditions.f * et)
    if abs(denom_factor) < 1e-10:  # More robust zero check
        logger.warning("Near-zero denominator factor in CAM16 to XYZ conversion")
        return (0.0, 0.0, 0.0)
    
    # Calculate adapted RGB components
    r_adapted = (460.0 * a_achromatic + 451.0 * alpha + 288.0 * beta) / 1403.0
    g_adapted = (460.0 * a_achromatic - 891.0 * alpha - 261.0 * beta) / 1403.0
    b_adapted = (460.0 * a_achromatic - 220.0 * alpha - 6300.0 * beta) / 1403.0
    
    # Inverse adaptation
    rgb_components = (_inverse_adapt_luminance(r_adapted, fl),
                      _inverse_adapt_luminance(g_adapted, fl),
                      _inverse_adapt_luminance(b_adapted, fl))
    
    # Convert back to XYZ
    xyz = _matrix_multiply(CAM16_RGB_TO_XYZ, rgb_components)
    
    return xyz


def cam16_to_ucs(jch: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Convert CAM16 JCh to CAM16-UCS coordinates.
    
    Args:
        jch: CAM16 coordinates (J, C, h)
        
    Returns:
        CAM16-UCS coordinates (J', a', b')
    """
    j, c, h = jch
    
    # Apply UCS transformation
    j_prime = (1.7 * j) / (1.0 + 0.007 * j)
    m_prime = (1.0 / 0.0228) * math.log(1.0 + 0.0228 * c)
    
    # Convert to Cartesian coordinates
    h_rad = math.radians(h)
    a_prime = m_prime * math.cos(h_rad)
    b_prime = m_prime * math.sin(h_rad)
    
    return (j_prime, a_prime, b_prime)


def ucs_to_cam16(ucs: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Convert CAM16-UCS coordinates to CAM16 JCh.
    
    Args:
        ucs: CAM16-UCS coordinates (J', a', b')
        
    Returns:
        CAM16 coordinates (J, C, h)
    """
    j_prime, a_prime, b_prime = ucs
    
    # Inverse UCS transformation
    j = j_prime / (1.7 - 0.007 * j_prime)
    
    m_prime = math.sqrt(a_prime * a_prime + b_prime * b_prime)
    c = (math.exp(0.0228 * m_prime) - 1.0) / 0.0228
    
    h = math.degrees(math.atan2(b_prime, a_prime)) % 360.0
    
    return (j, c, h)


def calculate_ucs_distance(ucs1: Tuple[float, float, float],
                           ucs2: Tuple[float, float, float]) -> float:
    """
    Calculate perceptual distance between two colors in CAM16-UCS space.
    
    Args:
        ucs1: First color in CAM16-UCS coordinates
        ucs2: Second color in CAM16-UCS coordinates
        
    Returns:
        Perceptual distance (ΔE)
    """
    j1, a1, b1 = ucs1
    j2, a2, b2 = ucs2
    
    delta_j = j1 - j2
    delta_a = a1 - a2
    delta_b = b1 - b2
    
    return math.sqrt(delta_j * delta_j + delta_a * delta_a + delta_b * delta_b)


def optimize_hue_spacing(base_hue: float, count: int, min_step: float = 25.0) -> List[float]:
    """
    Generate perceptually uniform hue steps using CAM16-UCS optimization.
    
    Args:
        base_hue: Starting hue angle (0-360 degrees)
        count: Number of hues to generate
        min_step: Minimum perceptual distance between colors
        
    Returns:
        List of optimized hue angles
    """
    if count <= 1:
        return [base_hue]
    
    # Start with evenly spaced hues
    hues = []
    step = 360.0 / count
    
    for i in range(count):
        hue = (base_hue + i * step) % 360.0
        hues.append(hue)
    
    # Convert to CAM16-UCS for optimization
    # Use standard lightness and chroma for comparison
    standard_j = 50.0  # Mid-lightness
    standard_c = 40.0  # Moderate chroma
    
    ucs_colors = []
    for hue in hues:
        jch = (standard_j, standard_c, hue)
        ucs = cam16_to_ucs(jch)
        ucs_colors.append(ucs)
    
    # Iterative optimization to ensure minimum spacing
    max_iterations = 50
    for iteration in range(max_iterations):
        adjusted = False
        
        for i in range(len(hues)):
            for j in range(i + 1, len(hues)):
                distance = calculate_ucs_distance(ucs_colors[i], ucs_colors[j])
                
                if distance < min_step:
                    # Adjust hues to increase distance
                    hue_diff = abs(hues[i] - hues[j])
                    if hue_diff > 180:
                        hue_diff = 360 - hue_diff
                    
                    adjustment = (min_step - distance) * 0.5
                    
                    if hues[i] < hues[j]:
                        hues[i] = (hues[i] - adjustment) % 360.0
                        hues[j] = (hues[j] + adjustment) % 360.0
                    else:
                        hues[i] = (hues[i] + adjustment) % 360.0
                        hues[j] = (hues[j] - adjustment) % 360.0
                    
                    # Recalculate UCS coordinates
                    jch_i = (standard_j, standard_c, hues[i])
                    jch_j = (standard_j, standard_c, hues[j])
                    ucs_colors[i] = cam16_to_ucs(jch_i)
                    ucs_colors[j] = cam16_to_ucs(jch_j)
                    
                    adjusted = True
        
        if not adjusted:
            break
    
    return sorted(hues)
