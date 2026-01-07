@echo off
REM Generate PWA icons from SVG using ImageMagick
REM Install ImageMagick: choco install imagemagick

echo Generating favicons and PWA icons...
cd /d "%~dp0..\static"

REM Check if ImageMagick is installed
where magick >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: ImageMagick not found!
    echo Install with: choco install imagemagick
    echo Or download from: https://imagemagick.org/script/download.php
    pause
    exit /b 1
)

REM Generate favicons
echo Generating favicon-16x16.png...
magick favicon.svg -resize 16x16 favicon-16x16.png

echo Generating favicon-32x32.png...
magick favicon.svg -resize 32x32 favicon-32x32.png

echo Generating apple-touch-icon.png...
magick favicon.svg -resize 180x180 apple-touch-icon.png

REM Generate PWA icons
echo Generating PWA icons...
for %%s in (72 96 128 144 152 192 384 512) do (
    echo   - icon-%%sx%%s.png
    magick favicon.svg -resize %%sx%%s icons\icon-%%sx%%s.png
)

echo.
echo ✓ All icons generated successfully!
echo.
pause
