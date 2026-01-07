#!/usr/bin/env python3
"""
Quick setup script for Dokumentor application
"""
import os
import sys
import subprocess

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """Check if Python version is 3.11+"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Error: Python 3.11 or higher is required")
        sys.exit(1)
    
    print("✅ Python version is compatible")

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    directories = [
        'data',
        'documents',
        'watch_folder',
        'logs',
        'uploads',
        'data/models'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")

def copy_env_file():
    """Copy example env file if it doesn't exist"""
    print_header("Setting up Environment File")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your configuration")
        else:
            print("⚠️  .env.example not found, skipping")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Python Dependencies")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def initialize_database():
    """Initialize the database"""
    print_header("Initializing Database")
    
    try:
        from backend.database import init_db
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    print("🎉 Dokumentor is ready to use!\n")
    print("Next steps:")
    print("  1. Edit the .env file with your configuration (if needed)")
    print("  2. Edit config.yaml to customize settings")
    print("  3. Run the application:")
    print("     python app.py")
    print("\n  4. Open your browser and navigate to:")
    print("     http://localhost:5000")
    print("\n  5. Create your first user account and start uploading documents!")
    print("\nFor Docker deployment:")
    print("  docker-compose up -d")
    print("\nFor more information, see README.md")
    print("="*60 + "\n")

def main():
    """Main setup function"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "Dokumentor Setup" + " "*31 + "║")
    print("╚" + "═"*58 + "╝")
    
    try:
        check_python_version()
        create_directories()
        copy_env_file()
        install_dependencies()
        initialize_database()
        print_next_steps()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
