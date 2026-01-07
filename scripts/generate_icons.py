#!/usr/bin/env python3
"""
Generate PWA icon set from SVG favicon
Requires: pip install Pillow cairosvg
"""

import os
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'Pillow', 'cairosvg'])
    from PIL import Image
    import cairosvg

# Icon sizes needed for PWA
SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]

def generate_icons():
    """Generate PNG icons from SVG"""
    static_dir = Path(__file__).parent.parent / 'static'
    svg_path = static_dir / 'favicon.svg'
    icons_dir = static_dir / 'icons'
    
    # Create icons directory
    icons_dir.mkdir(exist_ok=True)
    
    print(f"Reading SVG from: {svg_path}")
    
    # Read SVG content
    with open(svg_path, 'r') as f:
        svg_content = f.read()
    
    # Generate each size
    for size in SIZES:
        output_path = icons_dir / f'icon-{size}x{size}.png'
        print(f"Generating {size}x{size}...")
        
        # Convert SVG to PNG
        cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            write_to=str(output_path),
            output_width=size,
            output_height=size
        )
    
    # Generate standard favicon sizes
    print("Generating favicon-16x16.png...")
    cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        write_to=str(static_dir / 'favicon-16x16.png'),
        output_width=16,
        output_height=16
    )
    
    print("Generating favicon-32x32.png...")
    cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        write_to=str(static_dir / 'favicon-32x32.png'),
        output_width=32,
        output_height=32
    )
    
    print("Generating apple-touch-icon.png...")
    cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        write_to=str(static_dir / 'apple-touch-icon.png'),
        output_width=180,
        output_height=180
    )
    
    print("✓ All icons generated successfully!")

if __name__ == '__main__':
    generate_icons()
