import logging
import sys
from PyQt6.QtWidgets import QMainWindow

from .ui.main_window import MainWindow
from .ui.tray_icon import TrayIcon
from .utils.config import ConfigManager
from .filter_engine.filter_manager import get_filter_manager
from .profiles.profile_manager import ProfileManager

class OpenBlueFilterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Initializing OpenBlueFilter application")
        
        # Initialize components
        self._init_components()
        
        # Show the main window
        self.show()
        
        self.logger.info("Application initialized successfully")
    
    def _init_components(self):
        # Create configuration manager
        self.config_manager = ConfigManager()
        
        # Create filter manager
        self.filter_manager = get_filter_manager(self.config_manager)
        
        # Create profile manager
        self.profile_manager = ProfileManager(self.config_manager, self.filter_manager)
        
        # Ensure we have some default profiles
        self.profile_manager.create_default_profiles()
        
        # Create main window
        self.main_window = MainWindow(
            self.filter_manager,
            self.config_manager,
            self.profile_manager
        )
        
        # Create system tray icon
        self.tray_icon = TrayIcon(
            self.main_window,
            self.filter_manager,
            self.config_manager,
            self.profile_manager
        )
        
        # Apply initial settings
        self._apply_initial_settings()
    
    def _apply_initial_settings(self):
        # Check if filter should be enabled at startup
        if self.config_manager.get("filter_enabled", False):
            self.filter_manager.enable_filter()
            self.logger.info("Filter enabled at startup based on saved settings")
        
        # Apply the active profile
        active_profile = self.profile_manager.get_active_profile_name()
        if active_profile:
            self.profile_manager.activate_profile(active_profile)
            self.logger.info(f"Applied profile '{active_profile}' at startup")
    
    def show(self):
        self.main_window.show()
    
    def close(self):
        # Clean up and quit
        self.logger.info("Shutting down application")
        
        # Save configuration
        self.config_manager.save()
        
        # Disable the filter
        if self.filter_manager.is_enabled():
            self.filter_manager.disable_filter()
        
        # Close main window
        self.main_window.close()
        
        return super().close() 