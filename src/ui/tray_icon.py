import logging
import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QObject

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent, filter_manager, config_manager, profile_manager):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.filter_manager = filter_manager
        self.config_manager = config_manager
        self.profile_manager = profile_manager
        self.main_window = parent
        
        # Initialize the tray icon
        self._create_tray_icon()
        
        # Connect activation signal (double click on tray icon)
        self.activated.connect(self._on_tray_icon_activated)
    
    def _create_tray_icon(self):
        # Create tray icon with different icons for enabled/disabled states
        self._update_icon()
        
        # Create the tray menu
        self._create_tray_menu()
        
        # Show the tray icon
        self.show()
        self.logger.info("System tray icon initialized")
    
    def _create_tray_menu(self):
        # Create menu
        menu = QMenu(self.main_window)
        
        # Toggle filter action
        self.toggle_action = QAction("Disable Filter" if self.filter_manager.is_enabled() else "Enable Filter", self.main_window)
        self.toggle_action.triggered.connect(self._toggle_filter)
        menu.addAction(self.toggle_action)
        
        # Add separator
        menu.addSeparator()
        
        # Profiles submenu
        profiles_menu = menu.addMenu("Profiles")
        self._populate_profiles_menu(profiles_menu)
        
        # Add separator
        menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self.main_window)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)
        
        # Exit action
        exit_action = QAction("Exit", self.main_window)
        exit_action.triggered.connect(self._exit_application)
        menu.addAction(exit_action)
        
        # Set the menu for the tray icon
        self.setContextMenu(menu)
    
    def _populate_profiles_menu(self, menu):
        # Clear existing items
        menu.clear()
        
        # Get current profiles and active profile
        profiles = self.profile_manager.get_all_profiles()
        active_profile = self.profile_manager.get_active_profile_name()
        
        # Add profile actions
        for profile_name in profiles:
            action = QAction(profile_name, self.main_window)
            action.setCheckable(True)
            action.setChecked(profile_name == active_profile)
            
            # Use a lambda with default args to capture the profile name
            action.triggered.connect(lambda checked, name=profile_name: self._activate_profile(name))
            menu.addAction(action)
    
    def _update_icon(self):
        # Set the appropriate icon based on filter state
        icon_name = "icon_enabled.png" if self.filter_manager.is_enabled() else "icon.png"
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "resources", icon_name)
        
        # Use default icon if the specific icon doesn't exist
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "resources", "icon.png")
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"Icon file not found: {icon_path}")
    
    def _on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Show/hide main window on double click
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.activateWindow()
    
    def _toggle_filter(self):
        # Toggle the filter state
        self.filter_manager.toggle()
        
        # Update the UI
        self._update_ui()
        
        # Show notification
        self.showMessage("OpenBlueFilter", 
                        "Blue light filter enabled" if self.filter_manager.is_enabled() else "Blue light filter disabled",
                        QSystemTrayIcon.MessageIcon.Information, 
                        2000)
    
    def _activate_profile(self, profile_name):
        # Activate the selected profile
        self.profile_manager.activate_profile(profile_name)
        
        # Update UI if filter is enabled
        if self.filter_manager.is_enabled():
            self.filter_manager.apply_config()
        
        # Recreate the menu to update checkmarks
        self._create_tray_menu()
        
        # Show notification
        self.showMessage("OpenBlueFilter", 
                        f"Profile '{profile_name}' activated",
                        QSystemTrayIcon.MessageIcon.Information, 
                        2000)
    
    def _open_settings(self):
        # Show main window with settings
        self.main_window.show()
        self.main_window.activateWindow()
    
    def _exit_application(self):
        # First disable the filter
        if self.filter_manager.is_enabled():
            self.filter_manager.disable_filter()
        
        # Save any pending changes
        self.config_manager.save()
        
        # Quit the application
        self.main_window.close()
    
    def _update_ui(self):
        # Update tray icon
        self._update_icon()
        
        # Update toggle action text
        if self.toggle_action:
            self.toggle_action.setText("Disable Filter" if self.filter_manager.is_enabled() else "Enable Filter")
        
        # Recreate the menu
        self._create_tray_menu()
    
    def update(self):
        # Update the tray icon and menu
        self._update_ui() 