import logging
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QGroupBox, QPushButton, QLabel, QComboBox, 
                           QCheckBox, QTimeEdit, QLineEdit, QTabWidget,
                           QDialog, QDialogButtonBox, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QIcon, QFont

from .widgets.slider_widget import PercentageSlider, TemperatureSlider

class MainWindow(QMainWindow):
    def __init__(self, filter_manager, config_manager, profile_manager, scheduler):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.filter_manager = filter_manager
        self.config_manager = config_manager
        self.profile_manager = profile_manager
        self.scheduler = scheduler
        
        # Initialize UI
        self._init_ui()
        
        # Load settings from config
        self._load_settings()
    
    def _init_ui(self):
        self.setWindowTitle("OpenBlueFilter")
        self.setMinimumSize(500, 400)
        
        # Set the application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create Settings Tab
        settings_tab = QWidget()
        tab_widget.addTab(settings_tab, "Settings")
        
        # Create Profiles Tab
        profiles_tab = QWidget()
        tab_widget.addTab(profiles_tab, "Profiles")
        
        # Create Schedule Tab
        schedule_tab = QWidget()
        tab_widget.addTab(schedule_tab, "Schedule")
        
        # Create About Tab
        about_tab = QWidget()
        tab_widget.addTab(about_tab, "About")
        
        # Set up tab contents
        self._setup_settings_tab(settings_tab)
        self._setup_profiles_tab(profiles_tab)
        self._setup_schedule_tab(schedule_tab)
        self._setup_about_tab(about_tab)
        
        # Control buttons at the bottom
        control_layout = QHBoxLayout()
        
        self.toggle_button = QPushButton("Enable Filter" if not self.filter_manager.is_enabled() else "Disable Filter")
        self.toggle_button.clicked.connect(self._toggle_filter)
        control_layout.addWidget(self.toggle_button)
        
        self.minimize_button = QPushButton("Minimize to Tray")
        self.minimize_button.clicked.connect(self.hide)
        control_layout.addWidget(self.minimize_button)
        
        main_layout.addLayout(control_layout)
    
    def _setup_settings_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # Filter Settings Group
        filter_group = QGroupBox("Filter Settings")
        filter_layout = QVBoxLayout(filter_group)
        
        # Intensity slider (0-100%)
        self.intensity_slider = PercentageSlider("Filter Intensity:", 0, 100, 50)
        self.intensity_slider.valueChangedFloat.connect(self._on_intensity_changed)
        filter_layout.addWidget(self.intensity_slider)
        
        # Color Temperature Slider (1000K to 6500K)
        self.temp_slider = TemperatureSlider("Color Temperature:", 1000, 6500, 3500)
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        filter_layout.addWidget(self.temp_slider)
        
        # Add description for temperature
        temp_info = QLabel("Lower values = warmer (more orange/red), Higher values = cooler (more blue)")
        temp_info.setStyleSheet("font-size: 10px; color: gray;")
        filter_layout.addWidget(temp_info)
        
        layout.addWidget(filter_group)
        
        # System Integration Group
        system_group = QGroupBox("System Integration")
        system_layout = QVBoxLayout(system_group)
        
        # Start with system checkbox
        self.start_with_system_checkbox = QCheckBox("Start with system")
        self.start_with_system_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set("start_with_system", state == Qt.CheckState.Checked.value)
        )
        system_layout.addWidget(self.start_with_system_checkbox)
        
        layout.addWidget(system_group)
        
        # Add spacer at the bottom
        layout.addStretch()
    
    def _setup_profiles_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # Profiles Group
        profiles_group = QGroupBox("Profiles")
        profiles_layout = QVBoxLayout(profiles_group)
        
        # Profile selection
        profile_selector_layout = QHBoxLayout()
        profile_selector_layout.addWidget(QLabel("Active Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self._on_profile_selected)
        profile_selector_layout.addWidget(self.profile_combo, 1)
        
        profiles_layout.addLayout(profile_selector_layout)
        
        # Profile action buttons
        profile_actions_layout = QHBoxLayout()
        
        self.new_profile_button = QPushButton("New")
        self.new_profile_button.clicked.connect(self._create_new_profile)
        profile_actions_layout.addWidget(self.new_profile_button)
        
        self.save_profile_button = QPushButton("Save")
        self.save_profile_button.clicked.connect(self._save_current_profile)
        profile_actions_layout.addWidget(self.save_profile_button)
        
        self.delete_profile_button = QPushButton("Delete")
        self.delete_profile_button.clicked.connect(self._delete_current_profile)
        profile_actions_layout.addWidget(self.delete_profile_button)
        
        profiles_layout.addLayout(profile_actions_layout)
        
        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        profiles_layout.addWidget(line)
        
        # Current Profile Settings
        profiles_layout.addWidget(QLabel("Profile Settings:"))
        
        # Profile Intensity slider (0-100%)
        self.profile_intensity_slider = PercentageSlider("Filter Intensity:", 0, 100, 50)
        profiles_layout.addWidget(self.profile_intensity_slider)
        
        # Profile Color Temperature Slider (1000K to 6500K)
        self.profile_temp_slider = TemperatureSlider("Color Temperature:", 1000, 6500, 3500)
        profiles_layout.addWidget(self.profile_temp_slider)
        
        layout.addWidget(profiles_group)
        
        # Add spacer at the bottom
        layout.addStretch()
    
    def _setup_schedule_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # Schedule Group
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # Enable schedule checkbox
        self.schedule_enabled_checkbox = QCheckBox("Enable automatic scheduling")
        self.schedule_enabled_checkbox.stateChanged.connect(self._on_schedule_enabled_changed)
        schedule_layout.addWidget(self.schedule_enabled_checkbox)
        
        # Time settings
        times_layout = QHBoxLayout()
        
        # Start time
        times_layout.addWidget(QLabel("Enable at:"))
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.timeChanged.connect(self._on_start_time_changed)
        times_layout.addWidget(self.start_time_edit)
        
        # End time
        times_layout.addWidget(QLabel("Disable at:"))
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.timeChanged.connect(self._on_end_time_changed)
        times_layout.addWidget(self.end_time_edit)
        
        schedule_layout.addLayout(times_layout)
        
        # Sunset/sunrise checkbox
        self.sunset_checkbox = QCheckBox("Adjust automatically based on sunset/sunrise")
        self.sunset_checkbox.stateChanged.connect(
            lambda state: self.config_manager.set("auto_adjust_with_sunset", state == Qt.CheckState.Checked.value)
        )
        schedule_layout.addWidget(self.sunset_checkbox)
        
        # Location settings for sunset/sunrise
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))
        
        location_layout.addWidget(QLabel("Latitude:"))
        self.latitude_edit = QLineEdit()
        self.latitude_edit.setPlaceholderText("e.g. 40.7128")
        self.latitude_edit.textChanged.connect(
            lambda text: self.config_manager.set("location.latitude", float(text) if text.strip() else None)
        )
        location_layout.addWidget(self.latitude_edit)
        
        location_layout.addWidget(QLabel("Longitude:"))
        self.longitude_edit = QLineEdit()
        self.longitude_edit.setPlaceholderText("e.g. -74.0060")
        self.longitude_edit.textChanged.connect(
            lambda text: self.config_manager.set("location.longitude", float(text) if text.strip() else None)
        )
        location_layout.addWidget(self.longitude_edit)
        
        schedule_layout.addLayout(location_layout)
        
        layout.addWidget(schedule_group)
        
        # Add spacer at the bottom
        layout.addStretch()
    
    def _setup_about_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # Logo/title
        title = QLabel("OpenBlueFilter")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Description
        description = QLabel(
            "An open-source blue light filter application that reduces eye strain\n"
            "and improves sleep quality by filtering blue light from your display."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Spacer
        layout.addStretch()
        
        # Copyright/License
        copyright_text = QLabel("© 2023 OpenBlueFilter Team\nLicensed under the MIT License")
        copyright_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_text)
        
        # Website link
        website = QLabel("<a href='https://github.com/openbluefilter'>Visit GitHub Repository</a>")
        website.setOpenExternalLinks(True)
        website.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(website)
    
    def _load_settings(self):
        # Load intensity
        intensity = self.config_manager.get("intensity", 0.5)
        self.intensity_slider.setValueFloat(intensity)
        
        # Load color temperature
        color_temp = self.config_manager.get("color_temperature", 3500)
        self.temp_slider.setValue(color_temp)
        
        # Load system integration settings
        start_with_system = self.config_manager.get("start_with_system", False)
        self.start_with_system_checkbox.setChecked(start_with_system)
        
        # Load schedule settings
        schedule_enabled = self.config_manager.get("schedule_enabled", False)
        self.schedule_enabled_checkbox.setChecked(schedule_enabled)
        
        # Parse time strings (HH:MM format)
        start_time_str = self.config_manager.get("schedule_start", "20:00")
        end_time_str = self.config_manager.get("schedule_end", "07:00")
        
        try:
            start_hour, start_minute = map(int, start_time_str.split(':'))
            self.start_time_edit.setTime(QTime(start_hour, start_minute))
        except ValueError:
            self.logger.warning(f"Invalid start time format: {start_time_str}")
            
        try:
            end_hour, end_minute = map(int, end_time_str.split(':'))
            self.end_time_edit.setTime(QTime(end_hour, end_minute))
        except ValueError:
            self.logger.warning(f"Invalid end time format: {end_time_str}")
        
        # Load sunset/sunrise settings
        auto_adjust = self.config_manager.get("auto_adjust_with_sunset", False)
        self.sunset_checkbox.setChecked(auto_adjust)
        
        # Load location
        latitude = self.config_manager.get("location.latitude")
        if latitude is not None:
            self.latitude_edit.setText(str(latitude))
            
        longitude = self.config_manager.get("location.longitude")
        if longitude is not None:
            self.longitude_edit.setText(str(longitude))
        
        # Load profiles
        self._load_profiles()
    
    def _load_profiles(self):
        # Clear existing items
        self.profile_combo.clear()
        
        # Get all profiles and add to combo box
        profiles = self.profile_manager.get_all_profiles()
        for profile_name in profiles:
            self.profile_combo.addItem(profile_name)
        
        # Set current active profile
        active_profile = self.profile_manager.get_active_profile_name()
        if active_profile and active_profile in profiles:
            index = self.profile_combo.findText(active_profile)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
                
                # Load the profile settings into the profile sliders
                profile = profiles[active_profile]
                self.profile_intensity_slider.setValueFloat(profile.get("intensity", 0.5))
                self.profile_temp_slider.setValue(profile.get("color_temperature", 3500))
    
    def _toggle_filter(self):
        # Toggle the filter state
        self.filter_manager.toggle()
        
        # Update UI
        is_enabled = self.filter_manager.is_enabled()
        self.toggle_button.setText("Disable Filter" if is_enabled else "Enable Filter")
    
    def _on_intensity_changed(self, value):
        # Update filter intensity
        self.filter_manager.set_intensity(value)
    
    def _on_temp_changed(self, value):
        # Update color temperature
        self.filter_manager.set_color_temperature(value)
    
    def _on_profile_selected(self, profile_name):
        if not profile_name:
            return
            
        # Get the profile
        profiles = self.profile_manager.get_all_profiles()
        if profile_name in profiles:
            # Activate the profile
            self.profile_manager.activate_profile(profile_name)
            
            # Update the profile sliders
            profile = profiles[profile_name]
            self.profile_intensity_slider.setValueFloat(profile.get("intensity", 0.5))
            self.profile_temp_slider.setValue(profile.get("color_temperature", 3500))
            
            # Also update the main sliders
            self.intensity_slider.setValueFloat(profile.get("intensity", 0.5))
            self.temp_slider.setValue(profile.get("color_temperature", 3500))
    
    def _create_new_profile(self):
        # Open a dialog to get the new profile name
        dialog = QDialog(self)
        dialog.setWindowTitle("New Profile")
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Profile Name:"))
        
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            profile_name = name_input.text().strip()
            if profile_name:
                # Create the profile with current settings
                intensity = self.intensity_slider.valueFloat()
                color_temp = self.temp_slider.value()
                
                self.profile_manager.save_profile(profile_name, intensity, color_temp)
                
                # Update the profile list
                self._load_profiles()
                
                # Select the new profile
                index = self.profile_combo.findText(profile_name)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
    
    def _save_current_profile(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
            
        # Get current slider values
        intensity = self.profile_intensity_slider.valueFloat()
        color_temp = self.profile_temp_slider.value()
        
        # Save the profile
        self.profile_manager.save_profile(profile_name, intensity, color_temp)
        
        # Update the main sliders if this is the active profile
        active_profile = self.profile_manager.get_active_profile_name()
        if profile_name == active_profile:
            self.intensity_slider.setValueFloat(intensity)
            self.temp_slider.setValue(color_temp)
            
            # Update the filter
            if self.filter_manager.is_enabled():
                self.filter_manager.set_intensity(intensity)
                self.filter_manager.set_color_temperature(color_temp)
    
    def _delete_current_profile(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Delete the profile
            self.profile_manager.delete_profile(profile_name)
            
            # Update the profile list
            self._load_profiles()
    
    def _on_schedule_enabled_changed(self, state):
        is_enabled = state == Qt.CheckState.Checked.value
        self.config_manager.set("schedule_enabled", is_enabled)
        self.scheduler.update_schedule()
    
    def _on_start_time_changed(self, time):
        time_str = time.toString("HH:mm")
        self.config_manager.set("schedule_start", time_str)
        self.scheduler.update_schedule()
    
    def _on_end_time_changed(self, time):
        time_str = time.toString("HH:mm")
        self.config_manager.set("schedule_end", time_str)
        self.scheduler.update_schedule()
    
    def closeEvent(self, event):
        # Save configuration
        self.config_manager.save()
        event.accept() 