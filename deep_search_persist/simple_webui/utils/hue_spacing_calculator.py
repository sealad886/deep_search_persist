"""
Hue Spacing Calculator for Accessibility-Optimized Color Generation
Provides utilities for calculating perceptually uniform hue distributions using CAM16-UCS.
"""

from typing import List, Dict, Any, Tuple
from .cam16ucs import optimize_hue_spacing, cam16_to_ucs, calculate_ucs_distance
from .color_convert import hex_to_rgb, rgb_to_hex, rgb_to_hsl, hsl_to_rgb

# Import centralized logger from deep_search_persist
from ...deep_search_persist.logging.logging_config import logger


def calculate_perceptual_hue_steps(base_hue: float, count: int, 
                                   min_step: float = 25.0,
                                   lightness: float = 50.0,
                                   chroma: float = 40.0) -> List[float]:
    """
    Calculate perceptually uniform hue steps for accessibility.
    # flake8: noqa: W293
    Args:
        base_hue: Starting hue angle (0-360 degrees)
        count: Number of hues to generate
        min_step: Minimum perceptual distance in CAM16-UCS space
        lightness: Target lightness for calculations (0-100)
        chroma: Target chroma for calculations (0-100+)
        
    Returns:
        List of optimized hue angles
        
    Raises:
        ValueError: If input parameters are outside valid ranges
        TypeError: If input parameters are not numeric
    """
    # Input validation
    try:
        base_hue = float(base_hue)
        count = int(count)
        min_step = float(min_step)
        lightness = float(lightness)
        chroma = float(chroma)
    except (ValueError, TypeError) as e:
        raise TypeError(f"All parameters must be numeric: {e}")
    
    if count < 1:
        raise ValueError(f"Count must be at least 1, got: {count}")
    if min_step < 0:
        raise ValueError(f"Minimum step must be non-negative, got: {min_step}")
    if not (0 <= lightness <= 100):
        raise ValueError(f"Lightness must be in 0-100 range, got: {lightness}")
    if chroma < 0:
        raise ValueError(f"Chroma must be non-negative, got: {chroma}")
    
    # Normalize hue to 0-360 range
    base_hue = base_hue % 360.0
    
    if count <= 1:
        return [base_hue]
    
    return optimize_hue_spacing(base_hue, count, min_step)


def generate_accessible_palette(base_color: str, count: int,
                                min_perceptual_distance: float = 25.0,
                                preserve_lightness: bool = True) -> List[str]:
    """
    Generate an accessibility-optimized color palette using perceptual spacing.
    
    Args:
        base_color: Base color as hex string (e.g., "#FF5733")
        count: Number of colors to generate
        min_perceptual_distance: Minimum perceptual distance between colors
        preserve_lightness: Whether to maintain consistent lightness
        
    Returns:
        List of hex color strings with optimal perceptual spacing
    """
    if count <= 1:
        return [base_color]
    
    try:
        # Parse base color
        r, g, b = hex_to_rgb(base_color)
        h, s, lightness = rgb_to_hsl(r, g, b)
        
        # Calculate optimal hue distribution
        target_lightness = lightness * 100  # Convert to 0-100 scale
        target_chroma = s * 100     # Convert to 0-100 scale
        
        hues = calculate_perceptual_hue_steps(
            h, count, min_perceptual_distance, target_lightness, target_chroma
        )
        
        # Generate colors with optimized hues
        colors = []
        for hue in hues:
            if preserve_lightness:
                # Keep original lightness and saturation for WCAG compliance
                rgb_color = hsl_to_rgb(hue, s, lightness)
            else:
                # REMOVED: Automatic lightness variation contradicts WCAG contrast requirements
                # Use original lightness to maintain accessibility compliance
                logger.info("Using original lightness to maintain WCAG compliance")
                rgb_color = hsl_to_rgb(hue, s, lightness)
            
            colors.append(rgb_to_hex(rgb_color))
        
        return colors
        
    except (ValueError, TypeError) as e:
        # Structured logging for error handling
        logger.error(f"Color conversion failed for base_color='{base_color}', count={count}: {str(e)}")
        logger.info("Falling back to simple hue distribution")
        return _fallback_palette_generation(base_color, count)


def validate_palette_accessibility(colors: List[str],
                                   min_distance: float = 20.0) -> Dict[str, Any]:
    """
    Validate the accessibility of a color palette using perceptual distance metrics.
    
    Args:
        colors: List of hex color strings
        min_distance: Minimum acceptable perceptual distance
        
    Returns:
        Dictionary with validation results and recommendations
    """
    if len(colors) < 2:
        return {
            "valid": True,
            "min_distance": float('inf'),
            "avg_distance": float('inf'),
            "violations": [],
            "recommendations": []
        }
    
    # Convert colors to CAM16-UCS for perceptual distance calculation
    ucs_colors = []
    
    for color in colors:
        try:
            r, g, b = hex_to_rgb(color)
            h, s, lightness = rgb_to_hsl(r, g, b)
            
            # Use actual lightness and chroma from color
            jch = (lightness * 100, s * 100, h)
            ucs = cam16_to_ucs(jch)
            ucs_colors.append(ucs)
            
        except (ValueError, TypeError) as e:
            # Log invalid colors for debugging
            logger.warning(f"Skipping invalid color '{color}': {str(e)}")
            continue
    
    if len(ucs_colors) < 2:
        return {
            "valid": False,
            "error": "Insufficient valid colors for analysis",
            "min_distance": 0.0,
            "avg_distance": 0.0,
            "violations": [],
            "recommendations": ["Check color format validity"]
        }
    
    # Calculate all pairwise distances
    distances = []
    violations = []
    
    for i in range(len(ucs_colors)):
        for j in range(i + 1, len(ucs_colors)):
            distance = calculate_ucs_distance(ucs_colors[i], ucs_colors[j])
            distances.append(distance)
            
            if distance < min_distance:
                violations.append({
                    "color1": colors[i],
                    "color2": colors[j],
                    "distance": round(distance, 2),
                    "required": min_distance
                })
    
    min_dist = min(distances) if distances else 0.0
    avg_dist = sum(distances) / len(distances) if distances else 0.0
    
    # Generate recommendations
    recommendations = []
    if violations:
        recommendations.append(f"Increase spacing between {len(violations)} color pairs")
        recommendations.append("Consider using CAM16-UCS optimized generation")
        
        if min_dist < min_distance * 0.5:
            recommendations.append("Colors are too similar - consider reducing palette size")
    
    if avg_dist < min_distance * 1.2:
        recommendations.append("Overall palette spacing could be improved")
    
    return {
        "valid": len(violations) == 0,
        "min_distance": round(min_dist, 2),
        "avg_distance": round(avg_dist, 2),
        "violations": violations,
        "recommendations": recommendations,
        "total_pairs": len(distances),
        "violation_count": len(violations)
    }


def optimize_existing_palette(colors: List[str],
                              target_distance: float = 25.0) -> List[str]:
    """
    Optimize an existing color palette for better perceptual spacing.
    
    Args:
        colors: List of hex color strings to optimize
        target_distance: Target perceptual distance between colors
        
    Returns:
        List of optimized hex color strings
    """
    if len(colors) <= 1:
        return colors
    
    try:
        # Extract hues from existing colors
        hues = []
        lightness_values = []
        saturation_values = []
        
        for color in colors:
            r, g, b = hex_to_rgb(color)
            h, s, lightness = rgb_to_hsl(r, g, b)
            hues.append(h)
            lightness_values.append(lightness)
            saturation_values.append(s)
        
        # Calculate average lightness and saturation
        avg_lightness = sum(lightness_values) / len(lightness_values)
        avg_saturation = sum(saturation_values) / len(saturation_values)
        
        # Optimize hue distribution
        base_hue = hues[0]  # Use first hue as base
        optimized_hues = calculate_perceptual_hue_steps(
            base_hue, len(colors), target_distance,
            avg_lightness * 100, avg_saturation * 100
        )
        
        # Generate optimized colors
        optimized_colors = []
        for i, hue in enumerate(optimized_hues):
            # Use original lightness and saturation for each color
            original_l = lightness_values[i] if i < len(lightness_values) else avg_lightness
            original_s = saturation_values[i] if i < len(saturation_values) else avg_saturation
            
            rgb_color = hsl_to_rgb(hue, original_s, original_l)
            optimized_colors.append(rgb_to_hex(rgb_color))
        
        return optimized_colors
        
    except (ValueError, TypeError, IndexError) as e:
        # Log optimization failure
        logger.error(f"Palette optimization failed: {str(e)}")
        logger.info("Returning original colors")
        return colors


def _fallback_palette_generation(base_color: str, count: int) -> List[str]:
    """
    Fallback palette generation using simple hue distribution.
    
    Args:
        base_color: Base color as hex string
        count: Number of colors to generate
        
    Returns:
        List of hex color strings
    """
    try:
        r, g, b = hex_to_rgb(base_color)
        h, s, lightness = rgb_to_hsl(r, g, b)
        
        colors = []
        step = 360.0 / count
        
        for i in range(count):
            hue = (h + i * step) % 360.0
            rgb_color = hsl_to_rgb(hue, s, lightness)
            colors.append(rgb_to_hex(rgb_color))
        
        return colors
        
    except (ValueError, TypeError) as e:
        # Log fallback usage
        logger.error(f"Fallback palette generation failed for '{base_color}': {str(e)}")
        logger.info(f"Using ultimate fallback: repeating base color {count} times")
        return [base_color] * count


def get_palette_statistics(colors: List[str]) -> Dict[str, Any]:
    """
    Get comprehensive statistics about a color palette's perceptual properties.
    
    Args:
        colors: List of hex color strings
        
    Returns:
        Dictionary with palette statistics
    """
    if not colors:
        return {"error": "Empty palette"}
    
    try:
        # Convert to HSL for analysis
        hsl_colors = []
        for color in colors:
            r, g, b = hex_to_rgb(color)
            h, s, lightness = rgb_to_hsl(r, g, b)
            hsl_colors.append((h, s, lightness))
        
        # Calculate statistics
        hues = [h for h, s, lightness in hsl_colors]
        saturations = [s for h, s, lightness in hsl_colors]
        lightnesses = [lightness for h, s, lightness in hsl_colors]
        
        # Hue distribution analysis
        hue_range = max(hues) - min(hues) if len(hues) > 1 else 0
        hue_std = _calculate_std(hues) if len(hues) > 1 else 0
        
        return {
            "color_count": len(colors),
            "hue_range": round(hue_range, 2),
            "hue_std_dev": round(hue_std, 2),
            "avg_saturation": round(sum(saturations) / len(saturations), 3),
            "avg_lightness": round(sum(lightnesses) / len(lightnesses), 3),
            "saturation_range": round(max(saturations) - min(saturations), 3),
            "lightness_range": round(max(lightnesses) - min(lightnesses), 3),
            "colors": colors
        }
        
    except (ValueError, TypeError) as e:
        logger.error(f"Palette statistics analysis failed: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}


def _calculate_std(values: List[float]) -> float:
    """Calculate standard deviation of a list of values."""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5
