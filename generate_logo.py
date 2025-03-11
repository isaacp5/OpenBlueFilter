#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import math

def create_logo(size=256, enabled=False):
    """
    Create the OpenBlueFilter logo with anti-aliasing for higher quality
    
    Args:
        size: Size of the logo in pixels
        enabled: Whether to create the enabled or disabled version
    """
    # Create a larger image for better quality, then resize down
    large_size = size * 2
    
    # Create a transparent image with RGBA mode
    img = Image.new('RGBA', (large_size, large_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    if enabled:
        outer_color = (60, 120, 200, 255)  # Blue when enabled
        inner_color = (255, 160, 80, 200)  # Warm orange (filtered)
    else:
        outer_color = (100, 100, 100, 255)  # Gray when disabled
        inner_color = (220, 220, 220, 200)  # Light gray
    
    # Calculate dimensions
    center = large_size // 2
    outer_radius = int(large_size * 0.45)
    inner_radius = int(large_size * 0.35)
    line_length = int(large_size * 0.25)
    line_width = int(large_size * 0.03)
    
    # Draw outer circle with anti-aliasing
    draw.ellipse(
        (center - outer_radius, center - outer_radius, 
         center + outer_radius, center + outer_radius),
        outline=outer_color,
        width=int(large_size * 0.05)
    )
    
    # Draw inner filter effect with gradient
    for r in range(inner_radius, 0, -1):
        alpha = 150 - int(150 * (inner_radius - r) / inner_radius)
        color = inner_color[:3] + (alpha,)
        draw.ellipse(
            (center - r, center - r, center + r, center + r),
            fill=color,
            outline=None
        )
    
    # Draw filter lines
    for i in range(3):
        angle = math.radians(60 * (i + 1))
        x1 = center + int(math.cos(angle) * (inner_radius - line_width))
        y1 = center + int(math.sin(angle) * (inner_radius - line_width))
        x2 = center + int(math.cos(angle) * (inner_radius + line_length))
        y2 = center + int(math.sin(angle) * (inner_radius + line_length))
        
        # Draw thicker lines for better visibility
        for offset in range(-line_width, line_width + 1):
            draw.line(
                (x1, y1 + offset, x2, y2 + offset),
                fill=outer_color,
                width=3
            )
    
    # Apply a slight blur for smoother edges
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Resize down to the desired size for a cleaner look
    img = img.resize((size, size), Image.LANCZOS)
    
    return img

def main():
    # Ensure resources directory exists
    resources_dir = os.path.join(os.path.dirname(__file__), 'resources')
    os.makedirs(resources_dir, exist_ok=True)
    
    # Create standard icon
    std_icon = create_logo(size=256, enabled=False)
    std_icon.save(os.path.join(resources_dir, 'icon.png'))
    
    # Create enabled icon
    enabled_icon = create_logo(size=256, enabled=True)
    enabled_icon.save(os.path.join(resources_dir, 'icon_enabled.png'))
    
    # Create smaller icons for UI
    std_icon_small = create_logo(size=64, enabled=False)
    std_icon_small.save(os.path.join(resources_dir, 'icon_small.png'))
    
    enabled_icon_small = create_logo(size=64, enabled=True)
    enabled_icon_small.save(os.path.join(resources_dir, 'icon_enabled_small.png'))
    
    print("Logo files generated successfully in the resources directory")

if __name__ == "__main__":
    main() 