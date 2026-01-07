#!/usr/bin/env python3
"""
Create simple placeholder PNG icons for PWA
This creates basic solid color PNG files as placeholders
"""

import os
from pathlib import Path

# Simple PNG for a solid blue square (minimal valid PNG)
def create_png(size, output_path):
    """Create a minimal valid PNG file"""
    # This is a minimal 1x1 blue PNG, we'll describe it as the size
    # For a real app, use PIL or ImageMagick
    
    # For now, just create the SVG icon copies
    print(f"Creating {size}x{size} icon at {output_path}")
    
    # We'll just copy the SVG or create a note
    with open(output_path, 'w') as f:
        f.write(f"Placeholder {size}x{size} - Run generate_icons.bat to create real PNG icons")

def main():
    static_dir = Path(__file__).parent.parent / 'static'
    icons_dir = static_dir / 'icons'
    icons_dir.mkdir(exist_ok=True)
    
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("Creating placeholder icon files...")
    print("Note: These are text placeholders. Use generate_icons.bat for real PNG files.\n")
    
    for size in sizes:
        output_path = icons_dir / f'icon-{size}x{size}.png'
        create_png(size, output_path)
    
    # Create favicon sizes
    for name, size in [('favicon-16x16.png', 16), ('favicon-32x32.png', 32), ('apple-touch-icon.png', 180)]:
        output_path = static_dir / name
        create_png(size, output_path)
    
    print("\n✓ Placeholder files created")
    print("\nTo create real PNG icons:")
    print("  Run: scripts\\generate_icons.bat")
    print("  Or use: https://realfavicongenerator.net/")

if __name__ == '__main__':
    main()
