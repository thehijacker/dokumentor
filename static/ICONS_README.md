# Icon Generation

## Quick Setup (Temporary - SVG Favicon Only)

The app currently uses SVG favicon which works in modern browsers. To generate full PWA icon set:

## Option 1: Using ImageMagick (Recommended)

```powershell
# Install ImageMagick with brew/choco/apt
cd static

# Generate all sizes
magick favicon.svg -resize 16x16 favicon-16x16.png
magick favicon.svg -resize 32x32 favicon-32x32.png
magick favicon.svg -resize 180x180 apple-touch-icon.png

# Generate PWA icons
foreach ($size in 72,96,128,144,152,192,384,512) {
    magick favicon.svg -resize ${size}x${size} icons/icon-${size}x${size}.png
}
```

## Option 2: Using Python Script

```powershell
cd scripts
pip install Pillow cairosvg
python generate_icons.py
```

## Option 3: Online Tool

1. Open https://realfavicongenerator.net/
2. Upload `static/favicon.svg`
3. Download generated package
4. Extract to `static/` directory

## Current Status

✓ SVG favicon (modern browsers)
✓ PWA manifest configured
✓ Service worker registered
⚠ PNG icons needed for full PWA support (optional)
