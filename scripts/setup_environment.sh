#!/usr/bin/env python3
"""
POSIVA Analytics Platform - Environment Setup Script
Verifies installation and creates necessary directories
"""

import sys
import os
from pathlib import Path
import subprocess

def check_python_version():
    """Check if Python version is 3.10+"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required. You have {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def create_directories():
    """Create necessary project directories"""
    print("\nCreating project directories...")
    dirs = [
        "data/raw/stdf",
        "data/raw/logs",
        "data/staging",
        "data/processed",
        "data/features",
        "logs",
        "models/mlruns",
        "reports/auto/daily",
        "reports/auto/weekly",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to preserve empty directories
        gitkeep = Path(dir_path) / ".gitkeep"
        gitkeep.touch(exist_ok=True)
    
    print("✅ Directories created")

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    print("\nSetting up environment variables...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your settings")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ .env.example not found")

def check_imports():
    """Check if key packages can be imported"""
    print("\nChecking key package imports...")
    packages = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("plotly", "plotly"),
        ("streamlit", "streamlit"),
        ("sklearn", "scikit-learn"),
    ]
    
    all_ok = True
    for module, package in packages:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (not installed)")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Some packages missing. Install with:")
        print("   pip install -r requirements.txt")
    
    return all_ok

def initialize_git():
    """Initialize git repository if not already initialized"""
    print("\nChecking git repository...")
    git_dir = Path(".git")
    
    if not git_dir.exists():
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            print("✅ Git repository initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize git: {e}")
    else:
        print("✅ Git repository already initialized")

def main():
    """Main setup function"""
    print("=" * 60)
    print("POSIVA Analytics Platform - Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment file
    create_env_file()
    
    # Check package imports
    packages_ok = check_imports()
    
    # Initialize git
    initialize_git()
    
    print("\n" + "=" * 60)
    if packages_ok:
        print("✅ Setup complete! You're ready to start.")
        print("\nNext steps:")
        print("1. Edit .env file with your settings")
        print("2. Place data files in data/raw/")
        print("3. Run: jupyter lab")
        print("4. Open: notebooks/00_setup_and_environment.ipynb")
    else:
        print("⚠️  Setup incomplete. Install missing packages:")
        print("   pip install -r requirements.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()
