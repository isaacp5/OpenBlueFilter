# OpenBlueFilter

A blue light filter application for Windows that helps reduce eye strain by adjusting screen color temperature.

## Features

- Adjust screen color temperature and intensity
- Enable/disable filter with a single click
- Multiple filter profiles (Morning, Evening, Night)
- Minimal system resource usage
- System tray integration

## Building from Source

### Requirements

- Python 3.12 or newer
- Required Python packages:
  - tkinter (usually comes with Python)
  - pygame
  - psutil
  - pywin32
  - numpy

### Installation of Dependencies

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python src/main.py
```

### Building Executable

To build a standalone executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Use the build script:
   ```bash
   python build_fix.py
   ```

3. The executable will be created in the `dist` directory.

### Creating Installer

To create an installer using Inno Setup:

1. Download and install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isdl.php)

2. Open the `OpenBlueFilter_setup.iss` file with Inno Setup Compiler

3. Click on Build > Compile to create the installer

4. The installer will be created in the project's root directory as `OpenBlueFilter_Setup.exe`

## Installation

### Option 1: Download the Installer (Recommended)
1. Download the latest `OpenBlueFilter_Setup.exe` from the [Releases](https://github.com/isaacp5/OpenBlueFilter/releases) page
   - Note: When you first push your code to GitHub, the installer won't be immediately available
   - GitHub Actions will automatically build the executable when you push to the main branch
   - You'll need to create a Release and attach the built artifact (from the Actions tab) to make it downloadable
2. Run the installer and follow the prompts
3. Launch OpenBlueFilter from your Start menu or desktop

### Option 2: Build from Source
[existing build instructions...]

## Usage

1. Launch the application either by running the Python script, the executable, or after installation
2. A system tray icon will appear
3. Click on the tray icon to toggle the blue light filter on/off
4. Access the main window to:
   - Adjust filter intensity and color temperature
   - Create and manage profiles
   - View system information
5. The application will remember your settings between sessions

## License

[MIT](LICENSE)

## Credits

Created by Isaac B 