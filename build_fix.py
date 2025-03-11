import os
import sys
import shutil
import subprocess

def clean_dist():
    """Clean the dist directory"""
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    for file in os.listdir("."):
        if file.endswith(".spec") and file != "OpenBlueFilter.spec":
            os.remove(file)

def build_executable():
    """Build the executable with the correct import structure"""
    print("Building executable...")
    
    # Create a temporary main.py file in the root directory
    with open("main_temp.py", "w") as f:
        f.write("""
import sys
import os

# Add the current directory to the path so modules can be found
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    sys.path.insert(0, application_path)

# Import and run the main function from the src module
from src.main import main

if __name__ == "__main__":
    main()
""")
    
    # Run PyInstaller with the temporary main file
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=OpenBlueFilter",
        "--icon=resources/icon.png",
        "main_temp.py"
    ]
    
    subprocess.run(cmd)
    
    # Remove the temporary file
    os.remove("main_temp.py")
    
    print("Build completed!")

def main():
    clean_dist()
    build_executable()
    print("Done! The executable is located in the dist directory.")

if __name__ == "__main__":
    main() 