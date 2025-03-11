#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_prerequisites():
    """Check if all required tools are installed"""
    print("Checking prerequisites...")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller is not installed. Please install it with 'pip install pyinstaller'")
        return False
    
    # Check if Inno Setup is installed (for Windows only)
    if sys.platform == 'win32':
        inno_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
        if not inno_path.exists():
            print("⚠ Inno Setup not found at the default location.")
            print("  If you want to create an installer, please install Inno Setup from:")
            print("  https://jrsoftware.org/isdl.php")
            print("  The executable will still be built without the installer.")
    
    return True

def clean_build_dir():
    """Clean up previous build directories"""
    print("Cleaning up previous build files...")
    for path in ["build", "dist"]:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✓ Removed {path} directory")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Run PyInstaller
    result = subprocess.run(["pyinstaller", "OpenBlueFilter.spec"], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✗ PyInstaller failed:")
        print(result.stderr)
        return False
    
    print("✓ PyInstaller completed successfully")
    return True

def create_installer():
    """Create installer using Inno Setup (Windows only)"""
    if sys.platform != 'win32':
        print("Skipping installer creation (not on Windows)")
        return True
    
    print("Creating installer with Inno Setup...")
    
    # Look for Inno Setup in the default installation path
    inno_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
    if not inno_path.exists():
        inno_path = Path("C:/Program Files/Inno Setup 6/ISCC.exe")
    
    if not inno_path.exists():
        print("⚠ Inno Setup not found. Skipping installer creation.")
        print("  The executable has been built in the dist folder.")
        return False
    
    # Run Inno Setup Compiler
    result = subprocess.run([str(inno_path), "installer.iss"], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✗ Inno Setup compilation failed:")
        print(result.stderr)
        return False
    
    print("✓ Installer created successfully")
    return True

def main():
    """Main build process"""
    print("===== OpenBlueFilter Build Script =====")
    
    if not check_prerequisites():
        sys.exit(1)
    
    clean_build_dir()
    
    if not build_executable():
        sys.exit(1)
    
    create_installer()
    
    print("\nBuild completed!")
    print("Files created in the 'dist' directory:")
    print("- OpenBlueFilter/OpenBlueFilter.exe: Executable with supporting files")
    print("- OpenBlueFilter_Portable.exe: Single-file executable")
    if sys.platform == 'win32':
        print("- OpenBlueFilter_Setup.exe: Installer (if Inno Setup was available)")
    
    print("\nTo distribute the application, you can:")
    print("1. Share the installer (OpenBlueFilter_Setup.exe)")
    print("2. Share the portable executable (OpenBlueFilter_Portable.exe)")
    print("3. Zip and share the entire OpenBlueFilter folder")

if __name__ == "__main__":
    main() 