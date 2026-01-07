#!/bin/bash
# Quick setup script for Linux/Mac

set -e

echo "========================================"
echo "Dokumentor - Setup"
echo "========================================"
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

# Create directories
echo "Creating directories..."
mkdir -p data documents watch_folder logs uploads data/models
echo ""

# Copy env file
echo "Setting up environment file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from template"
        echo "Please edit .env with your configuration"
    else
        echo "Warning: .env.example not found"
    fi
else
    echo ".env file already exists"
fi
echo ""

# Check system dependencies
echo "Checking system dependencies..."
if ! command -v tesseract &> /dev/null; then
    echo "Warning: Tesseract OCR is not installed"
    echo "Install with: sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-slv"
fi

if ! command -v pdfinfo &> /dev/null; then
    echo "Warning: Poppler utils is not installed"
    echo "Install with: sudo apt-get install poppler-utils"
fi
echo ""

# Initialize database
echo "Initializing database..."
python -c "from backend.database import init_db; init_db()" || echo "Warning: Database initialization failed"
echo ""

# Done
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your settings (optional)"
echo "  2. Edit config.yaml to customize (optional)"
echo "  3. Activate venv: source venv/bin/activate"
echo "  4. Run: python app.py"
echo "  5. Open: http://localhost:5000"
echo ""
echo "For Docker deployment:"
echo "  docker-compose up -d"
echo ""
