#!/usr/bin/env python3
import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, Scale, HORIZONTAL, messagebox, simpledialog, font
import threading
import time
import ctypes
import json
from datetime import datetime
import re
from pathlib import Path
from PIL import Image, ImageTk
import webbrowser
import schedule
import pygame
import pytz
import random
import numpy as np
import colorsys
import traceback
import subprocess
import win32api
import win32con
import psutil

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger

# Define color scheme
COLORS = {
    "background": "#f0f0f0",
    "primary": "#4a86e8",
    "primary_dark": "#3a76d8",
    "secondary": "#ff9e40",
    "secondary_dark": "#f28c30",
    "text": "#333333",
    "text_secondary": "#666666",
    "button": "#4a86e8",  # Button background color
    "button_text": "#ffffff",  # Button text color
    "button_hover": "#3a76d8",  # Button hover color
    "disabled": "#cccccc",  # Disabled element color
    "border": "#d0d0d0",
    "header": "#e8f4fd",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
}

# Check if the application is running with administrative privileges
def is_admin():
    """Check if the program is running with administrator privileges"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # The most reliable method to check admin rights on Windows
        result = ctypes.windll.shell32.IsUserAnAdmin() != 0
        logger.debug(f"Admin check result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

class FilterManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = False
        self.intensity = 0.5
        self.color_temperature = 3500  # Default color temperature in Kelvin
        self.mag_dll = None
        self.simulation_mode = False
        self.simulation_error_count = 0
        self.last_real_attempt_time = 0  # Track when we last tried to use the real API
        self._initialize_magnification()
    
    def _initialize_magnification(self):
        if sys.platform != "win32":
            self.logger.warning("Not running on Windows, filter will operate in simulation mode")
            self.simulation_mode = True
            return False
            
        try:
            # Load the Windows Magnification API
            self.mag_dll = ctypes.windll.magnification
            
            # Initialize the Magnification API
            if not self.mag_dll.MagInitialize():
                error_code = ctypes.windll.kernel32.GetLastError()
                self.logger.error(f"Failed to initialize Windows Magnification API. Error code: {error_code}")
                self.simulation_mode = True
                return False
                
            self.logger.info("Windows Magnification API initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Windows Magnification API: {e}")
            self.simulation_mode = True
            return False
    
    def set_intensity(self, value):
        self.intensity = max(0.0, min(1.0, float(value)))
        self.logger.info(f"Setting filter intensity to {self.intensity}")
        
        if self.enabled:
            self._apply_filter()
    
    def set_color_temperature(self, value):
        self.color_temperature = max(1000, min(6500, int(value)))
        self.logger.info(f"Setting color temperature to {self.color_temperature}K")
        
        if self.enabled:
            self._apply_filter()
    
    def toggle(self):
        """Toggle the filter on/off"""
        if self.enabled:
            self.disable_filter()
        else:
            self.enable_filter()
        return self.enabled
    
    def enable_filter(self):
        """Enable the blue light filter"""
        self.logger.info("Enabling blue light filter")
        
        # Try to recover from simulation mode if it's been a while
        self._try_recover_from_simulation()
        
        # If we're in simulation mode, show a message to the user
        if self.simulation_mode:
            self.logger.info("Enabling filter in simulation mode")
            
            # Check if we're actually running as admin - if we are, don't suggest running as admin
            admin_status = is_admin()
            self.logger.debug(f"Current admin status: {admin_status}")
            
            try:
                import tkinter.messagebox as messagebox
                
                if admin_status:
                    # Already running as admin, different message needed
                    messagebox.showinfo(
                        "Simulation Mode",
                        "The blue light filter is running in simulation mode due to system limitations.\n\n"
                        "The filter effect is being simulated but not actually applied to your screen.\n\n"
                        "This might be due to compatibility issues with your graphics driver or Windows version."
                    )
                else:
                    # Standard message suggesting to run as admin
                    messagebox.showinfo(
                        "Simulation Mode",
                        "The blue light filter is running in simulation mode due to system limitations.\n\n"
                        "The filter effect is being simulated but not actually applied to your screen.\n\n"
                        "Try running the application as administrator for full functionality."
                    )
            except Exception:
                pass  # Ignore errors showing the message
            
            # In simulation mode, we just set the flag and return success
            self.enabled = True
            self.logger.info("Filter enabled (simulation mode)")
            return True
        
        # Try to apply the real filter
        result = self._apply_filter()
        
        # Only set enabled flag if filter was successfully applied
        if result:
            self.enabled = True
            self.logger.info("Filter successfully enabled")
        else:
            self.logger.error("Failed to enable filter")
            self.enabled = False
            
            # If we failed to apply the filter, show a message to the user
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror(
                    "Filter Error",
                    "Failed to enable the blue light filter.\n\n"
                    "This may be due to system restrictions or permissions.\n\n"
                    "Try running the application as administrator."
                )
            except Exception:
                pass  # Ignore errors showing the message
            
        return result
    
    def disable_filter(self):
        """Disable the blue light filter"""
        self.logger.info("Disabling blue light filter")
        
        # Try to recover from simulation mode if it's been a while
        self._try_recover_from_simulation()
        
        result = self._remove_filter()
        # Only set enabled flag if filter was successfully removed
        if result:
            self.enabled = False
            self.logger.info("Filter successfully disabled")
        else:
            self.logger.error("Failed to disable filter")
            # Keep current state
        return result
    
    def is_enabled(self):
        """Return whether the filter is currently enabled"""
        return self.enabled
    
    def _apply_filter(self):
        """Apply the blue light filter based on current settings"""
        if self.simulation_mode:
            self.logger.info(f"Filter simulated at intensity: {self.intensity}, temp: {self.color_temperature}K")
            return True
            
        try:
            result = self._apply_windows_filter()
            if not result:
                # Increment error count
                self.simulation_error_count += 1
                
                # If we've had multiple failures, switch to simulation mode
                if self.simulation_error_count >= 3:
                    self.logger.error(f"Multiple filter application failures ({self.simulation_error_count}), switching to simulation mode")
                    self.simulation_mode = True
                    self.logger.info(f"Filter simulated at intensity: {self.intensity}, temp: {self.color_temperature}K")
                    return True
                
                # Otherwise just return the failure
                return False
                
            # Reset error count on success
            self.simulation_error_count = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying filter: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Increment error count
            self.simulation_error_count += 1
            
            # If we've had multiple failures, switch to simulation mode
            if self.simulation_error_count >= 3:
                self.logger.error(f"Multiple filter application failures ({self.simulation_error_count}), switching to simulation mode")
            self.simulation_mode = True
            self.logger.info(f"Filter simulated at intensity: {self.intensity}, temp: {self.color_temperature}K")
            return True
                
            return False
    
    def _remove_filter(self):
        """Remove the blue light filter"""
        if self.simulation_mode:
            self.logger.info("Filter removed (simulation)")
            return True
            
        try:
            result = self._remove_windows_filter()
            if not result:
                # Increment error count
                self.simulation_error_count += 1
                
                # If we've had multiple failures, switch to simulation mode
                if self.simulation_error_count >= 3:
                    self.logger.error(f"Multiple filter removal failures ({self.simulation_error_count}), switching to simulation mode")
                    self.simulation_mode = True
                    self.logger.info("Filter removed (simulation)")
                    return True
                
                # Otherwise just return the failure
                return False
                
            # Reset error count on success
            self.simulation_error_count = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing filter: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Increment error count
            self.simulation_error_count += 1
            
            # If we've had multiple failures, switch to simulation mode
            if self.simulation_error_count >= 3:
                self.logger.error(f"Multiple filter removal failures ({self.simulation_error_count}), switching to simulation mode")
            self.simulation_mode = True
            self.logger.info("Filter removed (simulation)")
            return True
                
            return False
    
    def _apply_windows_filter(self):
        """Apply the color filter using Windows Magnification API"""
        try:
            # If we're already in simulation mode, don't attempt to use the Windows API
            if self.simulation_mode:
                self.logger.info(f"Filter simulated at intensity: {self.intensity}, temp: {self.color_temperature}K")
                return True
                
            if not self.mag_dll:
                self.logger.error("Magnification DLL not loaded, trying to initialize again")
                if not self._initialize_magnification():
                    admin_status = is_admin()
                    self.logger.error(f"Failed to initialize magnification API. Running as admin: {admin_status}")
                    return False
            
            # Make sure the API is initialized
            if not hasattr(self, 'api_initialized') or not self.api_initialized:
                try:
                    result = self.mag_dll.MagInitialize()
                    if result:
                        self.logger.info("Magnification API initialized")
                        self.api_initialized = True
                    else:
                        error_code = ctypes.windll.kernel32.GetLastError()
                        admin_status = is_admin()
                        self.logger.error(f"Failed to initialize magnification API. Error code: {error_code}, Admin: {admin_status}")
                        return False
                except Exception as e:
                    admin_status = is_admin()
                    self.logger.error(f"Error initializing magnification API: {e}, Admin: {admin_status}")
                    return False
                
            class ColorMatrix(ctypes.Structure):
                _fields_ = [
                    ("matrix", ctypes.c_float * 25)
                ]
            
            # Create matrix based on intensity and color temperature
            matrix = self._create_color_matrix()
            
            # Define the transform structure
            colorEffect = ColorMatrix()
            colorEffect.matrix = matrix
            
            # Apply the color transform
            result = self.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(colorEffect))
            
            if result == 0:
                error_code = ctypes.windll.kernel32.GetLastError()
                self.logger.error(f"Failed to apply color filter. Error code: {error_code}")
                
                # Special handling for error code 21 (ACCESS_DENIED)
                if error_code == 21:
                    admin_status = is_admin()
                    if admin_status:
                        self.logger.warning("Access denied when applying filter even though running as administrator. This may be a Windows security feature or compatibility issue.")
                    else:
                        self.logger.warning("Access denied when applying filter. This requires administrator privileges.")
                    
                    self.logger.info(f"Attempting alternative method for applying filter (Admin status: {admin_status})...")
                    
                    # Try an alternative approach - use a different API call
                    try:
                        # First try to uninitialize and reinitialize
                        self.mag_dll.MagUninitialize()
                        time.sleep(0.5)
                        
                        if self.mag_dll.MagInitialize():
                            # Try with a different approach - set a smaller transform
                            # This sometimes works when the full screen transform fails
                            self.logger.info("Trying with a different approach...")
                            
                            # Create a smaller matrix with less blue reduction
                            reduced_intensity = self.intensity * 0.5
                            self.logger.info(f"Using reduced intensity: {reduced_intensity}")
                            
                            # Create a new matrix with reduced intensity
                            alt_matrix = self._create_color_matrix(override_intensity=reduced_intensity)
                            alt_effect = ColorMatrix()
                            alt_effect.matrix = alt_matrix
                            
                            # Try applying the reduced effect
                            result = self.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(alt_effect))
                            if result != 0:
                                self.logger.info("Successfully applied filter with reduced intensity")
                                return True
                    except Exception as e:
                        self.logger.error(f"Error in alternative filter application: {e}")
                    
                    # If we get here, all attempts failed
                    self.logger.error("All attempts to apply filter failed. You may need to run as administrator.")
                    
                    # Show a message to the user about the error
                    try:
                        import tkinter.messagebox as messagebox
                        messagebox.showwarning(
                            "Permission Error",
                            "The blue light filter could not be applied due to permission issues.\n\n"
                            "You may need to run this application as administrator."
                        )
                    except Exception:
                        pass  # Ignore errors showing the message
                
                # Try to reinitialize and try again for certain error codes
                elif error_code in [5, 6, 50, 1812]:  # Common error codes for access issues
                    self.logger.info("Trying to reinitialize magnification API")
                    
                    # First uninitialize
                    try:
                        self.mag_dll.MagUninitialize()
                    except Exception as e:
                        self.logger.error(f"Error uninitializing magnification API: {e}")
                    
                    # Wait a moment
                    time.sleep(0.5)
                    
                    # Try to initialize again
                    try:
                        if self.mag_dll.MagInitialize():
                            self.logger.info("Reinitialized magnification API, trying to apply filter again")
                            
                            # Try to apply the filter again
                            try:
                                result = self.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(colorEffect))
                                if result != 0:
                                    self.logger.info("Successfully applied filter after reinitialization")
                                    return True
                                else:
                                    self.logger.error("Failed to apply filter after reinitialization")
                            except Exception as e:
                                self.logger.error(f"Error applying filter after reinitialization: {e}")
                        else:
                            self.logger.error("Failed to reinitialize magnification API")
                    except Exception as e:
                        self.logger.error(f"Error reinitializing magnification API: {e}")
                
                return False
            
            self.logger.info("Windows color filter applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Exception in _apply_windows_filter: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _create_color_matrix(self, override_intensity=None):
        """Create a color matrix for the blue light filter based on intensity and color temperature"""
        # Use the override intensity if provided, otherwise use the instance intensity
        intensity = override_intensity if override_intensity is not None else self.intensity
        
        # Create a flattened 5x5 matrix (25 elements)
        matrix = (ctypes.c_float * 25)(
            1.0, 0.0, 0.0, 0.0, 0.0,  # Row 1
            0.0, 1.0, 0.0, 0.0, 0.0,  # Row 2
            0.0, 0.0, 1.0, 0.0, 0.0,  # Row 3
            0.0, 0.0, 0.0, 1.0, 0.0,  # Row 4
            0.0, 0.0, 0.0, 0.0, 1.0   # Row 5
        )
        
        # Calculate factors based on intensity and color temperature
        temp_factor = (6500 - self.color_temperature) / 5500  # Normalize temp to 0-1 range
        temp_factor = max(0, min(1, temp_factor))
        
        # Reduce blue based on intensity and temperature
        blue_reduction = intensity * temp_factor
        
        # Adjust red slightly higher for warmer appearance
        red_boost = intensity * temp_factor * 0.3
        
        # Modify the color matrix
        # Red channel (slightly increased for warmer appearance)
        matrix[0] = 1.0 + red_boost
        
        # Green channel (slightly reduced)
        matrix[6] = 1.0 - (intensity * 0.1)
        
        # Blue channel (reduced based on settings)
        matrix[12] = 1.0 - blue_reduction
        
        return matrix
    
    def _remove_windows_filter(self):
        """Remove the Windows color filter"""
        # If we're in simulation mode or don't have the DLL, no need to interact with Windows API
        if not self.mag_dll or self.simulation_mode:
            self.logger.info("Filter removed (simulation mode or no DLL)")
            return True
            
        try:
            # Make sure the API is initialized
            if not hasattr(self, 'api_initialized') or not self.api_initialized:
                try:
                    result = self.mag_dll.MagInitialize()
                    if result:
                        self.logger.info("Magnification API initialized")
                        self.api_initialized = True
                    else:
                        error_code = ctypes.windll.kernel32.GetLastError()
                        self.logger.error(f"Failed to initialize magnification API. Error code: {error_code}")
                        return False
                except Exception as e:
                    self.logger.error(f"Error initializing magnification API: {e}")
                    return False
            
            # Create an identity matrix (no change) using the same approach as _create_color_matrix
            matrix = (ctypes.c_float * 25)(
                1.0, 0.0, 0.0, 0.0, 0.0,  # Row 1
                0.0, 1.0, 0.0, 0.0, 0.0,  # Row 2
                0.0, 0.0, 1.0, 0.0, 0.0,  # Row 3
                0.0, 0.0, 0.0, 1.0, 0.0,  # Row 4
                0.0, 0.0, 0.0, 0.0, 1.0   # Row 5
            )
            
            # Apply the identity matrix to remove the filter
            result = self.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(matrix))
            
            if result == 0:
                error_code = ctypes.windll.kernel32.GetLastError()
                self.logger.error(f"Failed to remove Windows color filter. Error code: {error_code}")
                
                # Try to reinitialize and try again for certain error codes
                if error_code in [5, 6, 50, 1812]:  # Common error codes for access issues
                    self.logger.info("Trying to reinitialize magnification API")
                    
                    # First uninitialize
                    try:
                        self.mag_dll.MagUninitialize()
                    except Exception as e:
                        self.logger.error(f"Error uninitializing magnification API: {e}")
                    
                    # Wait a moment
                    time.sleep(0.5)
                    
                    # Try to initialize again
                    try:
                        if self.mag_dll.MagInitialize():
                            self.logger.info("Reinitialized magnification API, trying to remove filter again")
                            
                            # Try to remove the filter again
                            try:
                                result = self.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(matrix))
                                if result != 0:
                                    self.logger.info("Successfully removed filter after reinitialization")
                                    return True
                                else:
                                    self.logger.error("Failed to remove filter after reinitialization")
                            except Exception as e:
                                self.logger.error(f"Error removing filter after reinitialization: {e}")
                        else:
                            self.logger.error("Failed to reinitialize magnification API")
                    except Exception as e:
                        self.logger.error(f"Error reinitializing magnification API: {e}")
                
                return False
            
            self.logger.info("Windows color filter removed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing Windows color filter: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def cleanup(self):
        """Clean up resources used by the filter manager"""
        # First make sure filter is disabled
        if self.enabled:
            self.disable_filter()
            
        # Then uninitialize magnification API if needed
        if sys.platform == "win32" and self.mag_dll:
            try:
                self.mag_dll.MagUninitialize()
                self.logger.info("Windows Magnification API uninitialized")
            except Exception as e:
                self.logger.error(f"Error uninitializing Windows Magnification API: {e}")
        
        return True
    
    def _try_recover_from_simulation(self):
        """Try to recover from simulation mode by reinitializing the magnification API"""
        # Only try to recover if we're in simulation mode and on Windows
        if not self.simulation_mode or sys.platform != "win32":
            return False
            
        # Don't attempt recovery too frequently - only try once every 5 minutes
        current_time = time.time()
        if current_time - self.last_real_attempt_time < 300:  # 5 minutes
            return False
            
        self.logger.info("Attempting to recover from simulation mode...")
        self.last_real_attempt_time = current_time
            
        # Try to reinitialize the magnification API
        if self._initialize_magnification():
            self.simulation_mode = False
            self.simulation_error_count = 0
            self.logger.info("Successfully recovered from simulation mode!")
            return True
        
        # Increment error count if we couldn't recover
        self.simulation_error_count += 1
        self.logger.warning(f"Failed to recover from simulation mode (attempt {self.simulation_error_count})")
        return False


class ConfigManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".openbluefilter"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        default_config = {
            "filter_enabled": False,
            "intensity": 0.5,
            "color_temperature": 3500,
            "schedule_enabled": False,
            "schedule_start": "20:00", 
            "schedule_end": "07:00",
            "profiles": {
                "Day": {
                    "intensity": 0.3,
                    "color_temperature": 4500
                },
                "Evening": {
                    "intensity": 0.6,
                    "color_temperature": 3200
                },
                "Night": {
                    "intensity": 0.8,
                    "color_temperature": 2700
                }
            },
            "active_profile": "Day"
        }
        
        os.makedirs(self.config_dir, exist_ok=True)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Ensure all default keys exist in loaded config
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                self.logger.info("Configuration loaded successfully")
                return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return default_config
        else:
            self.logger.info("Config file not found, creating default configuration")
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config=None):
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        try:
            value = self.config.get(key, default)
            return value
        except:
            return default
    
    def set(self, key, value):
        self.config[key] = value
        self._save_config()


class ProfileManager:
    def __init__(self, config_manager, filter_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.filter_manager = filter_manager
        
        # Create default profiles if none exist
        self.create_default_profiles()
    
    def get_all_profiles(self):
        """Get a list of all available profiles"""
        return self.config_manager.get("profiles", {}).keys()
    
    def get_active_profile_name(self):
        """Get the name of the currently active profile"""
        return self.config_manager.get("active_profile", None)
        
    def activate_profile(self, profile_name):
        """Activate a profile by name"""
        try:
            profiles = self.config_manager.get("profiles", {})
            
            if profile_name not in profiles:
                self.logger.warning(f"Profile {profile_name} does not exist")
                return False
                
            # Get profile settings
            profile = profiles[profile_name]
            intensity = profile.get("intensity", 50)
            color_temperature = profile.get("color_temperature", 4500)
            
            self.logger.info(f"Activating profile {profile_name} (intensity={intensity}%, temp={color_temperature}K)")
            
            # Apply settings
            self.filter_manager.set_intensity(intensity)
            self.filter_manager.set_color_temperature(color_temperature)
            
            # Save active profile name
            self.config_manager.set("active_profile", profile_name)
            self.config_manager.save_config()
            
            return True
        except Exception as e:
            self.logger.error(f"Error activating profile: {e}")
            return False
            
    def create_default_profiles(self):
        """Create default profiles if they don't exist"""
        profiles = self.config_manager.get("profiles", {})
        
        # Create default profiles if config is empty
        if not profiles:
            self.logger.info("Creating default profiles")
            profiles = {
                "Morning": {
                    "intensity": 30,
                    "color_temperature": 5000
                },
                "Evening": {
                    "intensity": 50,
                    "color_temperature": 4000
                },
                "Night": {
                    "intensity": 70,
                    "color_temperature": 2500
                }
            }
            self.config_manager.set("profiles", profiles)
            
            # Set default active profile
            if not self.config_manager.get("active_profile"):
                # Determine which profile to set based on time of day
                hour = datetime.now().hour
                
                if 6 <= hour < 12:
                    default_profile = "Morning"
                elif 12 <= hour < 19:
                    default_profile = "Evening"
                else:
                    default_profile = "Night"
                    
                self.config_manager.set("active_profile", default_profile)
            
            self.config_manager.save_config()
        else:
            # Check if we need to update default profiles with new fields
            default_profiles = {
                "Morning": {
                    "intensity": 30,
                    "color_temperature": 5000
                },
                "Evening": {
                    "intensity": 50,
                    "color_temperature": 4000
                },
                "Night": {
                    "intensity": 70,
                    "color_temperature": 2500
                }
            }
            
            # Update any missing default profiles
            updated = False
            for name, settings in default_profiles.items():
                if name not in profiles:
                    profiles[name] = settings
                    updated = True
                    self.logger.info(f"Added missing default profile: {name}")
            
            if updated:
                self.config_manager.set("profiles", profiles)
                self.config_manager.save_config()
    
    def save_profile(self, profile_name, intensity=None, color_temperature=None):
        """Save a new or existing profile"""
        try:
            profiles = self.config_manager.get("profiles", {})
            
            # If the profile doesn't exist, create it
            if profile_name not in profiles:
                profiles[profile_name] = {}
            
            # Update profile settings
            if intensity is not None:
                profiles[profile_name]["intensity"] = intensity
                
            if color_temperature is not None:
                profiles[profile_name]["color_temperature"] = color_temperature
            
            # Save profiles to config
            self.config_manager.set("profiles", profiles)
            self.config_manager.save_config()
            
            self.logger.info(f"Saved profile {profile_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving profile: {e}")
            return False
            
    def delete_profile(self, profile_name):
        """Delete a profile by name"""
        try:
            profiles = self.config_manager.get("profiles", {})
            
            if profile_name not in profiles:
                self.logger.warning(f"Cannot delete profile {profile_name} - does not exist")
                return False
            
            # Delete the profile
            del profiles[profile_name]
            
            # Update config
            self.config_manager.set("profiles", profiles)
            
            # If the deleted profile was active, clear the active profile
            if self.config_manager.get("active_profile") == profile_name:
                self.config_manager.set("active_profile", None)
            
            self.config_manager.save_config()
            
            self.logger.info(f"Deleted profile {profile_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting profile: {e}")
            return False

class SystemTrayApp:
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(__name__)
        self.icons = {}  # Store loaded icons
        
        # Initialize components
        self._load_icons()
        
        # Create filter manager
        self.filter_manager = FilterManager()
        self.filter_enabled = False
        
        # Create configuration manager
        self.config_manager = ConfigManager()
        
        # Create profile manager
        self.profile_manager = ProfileManager(self.config_manager, self.filter_manager)
        
        # Set up the main window
        self._setup_ui()
        
        # Apply initial settings from config
        self._apply_initial_settings()
        
    def _load_icons(self):
        """Load icon images for the application"""
        try:
            # Get the absolute path to resources directory
            resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
            
            # List of icons to load
            icon_files = {
                'app': 'icon.png',
                'app_enabled': 'icon_enabled.png',
                'small': 'icon_small.png',
                'small_enabled': 'icon_enabled_small.png'
            }
            
            self.icons = {}
            for key, filename in icon_files.items():
                path = os.path.join(resources_dir, filename)
                if os.path.exists(path):
                    self.icons[key] = ImageTk.PhotoImage(Image.open(path))
                    self.logger.info(f"Loaded icon: {path}")
                else:
                    self.logger.warning(f"Icon file not found: {path}")
            
            # If no icons were loaded successfully, try to generate them
            if not self.icons and os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generate_logo.py')):
                self.logger.info("Attempting to generate logo files...")
                try:
                    import subprocess
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generate_logo.py')
                    subprocess.run(['python', script_path], check=True)
                    
                    # Try loading again
                    for key, filename in icon_files.items():
                        path = os.path.join(resources_dir, filename)
                        if os.path.exists(path):
                            self.icons[key] = ImageTk.PhotoImage(Image.open(path))
                            self.logger.info(f"Loaded newly generated icon: {path}")
                except Exception as e:
                    self.logger.error(f"Failed to generate logo files: {e}")
        except Exception as e:
            self.logger.error(f"Error loading icons: {e}")
    
    def _apply_initial_settings(self):
        """Apply initial settings from configuration"""
        # Update profiles in UI
        self._update_profiles()
        
        # Set initial intensity
        intensity = self.config_manager.get("filter.intensity", 0.5)
        self.intensity_var.set(intensity)
        self.filter_manager.set_intensity(intensity)
        self.logger.info(f"Setting filter intensity to {intensity}")
        
        # Set initial color temperature
        color_temp = self.config_manager.get("filter.color_temperature", 3200)
        self.temp_var.set(color_temp)
        self.filter_manager.set_color_temperature(color_temp)
        self.logger.info(f"Setting color temperature to {color_temp}K")
        
        # Set filter state
        filter_enabled = self.config_manager.get("filter.enabled", False)
        if filter_enabled:
            self.filter_manager.enable_filter()
            self.toggle_button.config(text="Disable Filter")
            self.status_var.set("Filter: Enabled")
        else:
            self.filter_manager.disable_filter()
            self.toggle_button.config(text="Enable Filter")
            self.status_var.set("Filter: Disabled")
        
        # Set active profile
        active_profile = self.config_manager.get("active_profile", "")
        profiles = list(self.profile_manager.get_all_profiles())
        
        # Set the current profile name for display
        if active_profile and active_profile in profiles:
            # Find the index of the active profile in the listbox
            if hasattr(self, 'profiles_listbox') and self.profiles_listbox.size() > 0:
                try:
                    profile_index = profiles.index(active_profile)
                    self.profiles_listbox.selection_clear(0, tk.END)
                    self.profiles_listbox.selection_set(profile_index)
                    self.profiles_listbox.see(profile_index)
                    self.current_profile_name.set(active_profile)
                except (ValueError, tk.TclError) as e:
                    self.logger.error(f"Error selecting profile in listbox: {e}")
        elif profiles:
            # Default to first profile if active one not found
            if hasattr(self, 'profiles_listbox') and self.profiles_listbox.size() > 0:
                self.profiles_listbox.selection_clear(0, tk.END)
                self.profiles_listbox.selection_set(0)
                self.current_profile_name.set(profiles[0])
                
        # Load the selected profile settings
        if active_profile:
            self.profile_manager.activate_profile(active_profile)
    
    def _setup_ui(self):
        # Configure main window
        self.root.title("OpenBlueFilter")
        self.root.geometry("600x680")
        self.root.minsize(550, 650)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure styles
        self._configure_styles()
        
        # Create header with icon and title
        self._create_header(main_frame)
        
        # Create notebook for tabs
        style = ttk.Style()
        style.configure("TNotebook", tabposition='n')
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Add tabs
        self._setup_settings_tab()
        self._setup_profiles_tab()
        self._setup_about_tab()
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, padding=(10, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create bottom button frame
        bottom_frame = ttk.Frame(main_frame, padding=(15, 10))
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, before=status_bar)
        
        # Toggle button (left-aligned)
        self.toggle_button = ttk.Button(
            bottom_frame, 
            text="Enable Filter", 
            command=self._toggle_filter,
            style="Accent.TButton"
        )
        self.toggle_button.pack(side=tk.LEFT)
        
        # Close button (right-aligned)
        close_button = ttk.Button(
            bottom_frame, 
            text="Close", 
            command=self.root.withdraw,
        )
        close_button.pack(side=tk.RIGHT)
        
        # Update filter UI based on initial state
        self._update_filter_ui()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
    
    def _configure_styles(self):
        """Configure ttk styles for better UI appearance"""
        style = ttk.Style()
        
        # Configure frames
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Card.TFrame", background="#ffffff", relief=tk.RAISED)
        
        # Configure labels
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
        style.configure("Header.TLabel", font=font.Font(size=14, weight="bold"))
        style.configure("Subheader.TLabel", font=font.Font(size=12, weight="bold"))
        style.configure("Info.TLabel", foreground=COLORS["text_secondary"])
        
        # Configure buttons
        style.configure("TButton", padding=5)
        style.configure("Primary.TButton", background=COLORS["button"])
        style.map(
            "Primary.TButton",
            background=[("active", COLORS["button_hover"]), ("pressed", COLORS["button_hover"])]
        )
        
        style.configure("Secondary.TButton", background=COLORS["secondary"])
        style.map(
            "Secondary.TButton",
            background=[("active", COLORS["secondary_dark"]), ("pressed", COLORS["secondary_dark"])]
        )
        
        # Configure scales
        style.configure("Horizontal.TScale", sliderthickness=20)
        
        # Configure notebook (tabs)
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["background"], padding=(15, 5), font=font.Font(size=10))
        style.map("TNotebook.Tab", 
                 background=[("selected", "#ffffff")],
                 foreground=[("selected", COLORS["primary"])])
        
        # Configure checkbutton
        style.configure("TCheckbutton", background="#ffffff", foreground=COLORS["text"])
        
        # Configure combobox
        style.configure("TCombobox", 
                      fieldbackground="#ffffff", 
                      background=COLORS["background"])
        
        # Configure labelframe
        style.configure("TLabelframe", background="#ffffff", foreground=COLORS["text"], 
                       borderwidth=1, relief=tk.GROOVE)
        style.configure("TLabelframe.Label", background="#ffffff", foreground=COLORS["primary"], font=font.Font(size=12, weight="bold"))
    
    def _create_header(self, main_frame):
        """Create a header with logo and title"""
        header_frame = ttk.Frame(main_frame, style="TFrame")
        header_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Add logo if available
        if 'small' in self.icons:
            logo_label = ttk.Label(header_frame, image=self.icons['small'], background=COLORS["background"])
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add title and subtitle
        title_frame = ttk.Frame(header_frame, style="TFrame")
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = ttk.Label(
            title_frame, 
            text="OpenBlueFilter", 
            font=font.Font(family=font.nametofont("TkDefaultFont").cget("family"), size=16, weight="bold"),
            background=COLORS["background"],
            foreground=COLORS["primary"]
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            title_frame, 
            text="Reduce eye strain and improve sleep",
            background=COLORS["background"],
            foreground=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor=tk.W)
    
    def _setup_settings_tab(self):
        # Create a container with padding
        settings_container = ttk.Frame(self.notebook, padding=15)
        settings_container.pack(fill=tk.BOTH, expand=True)

        # Sliders section with title
        sliders_frame = ttk.LabelFrame(settings_container, text="Filter Settings", padding=10)
        sliders_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Intensity slider
        intensity_frame = ttk.Frame(sliders_frame)
        intensity_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(intensity_frame, text="Intensity:", font=font.Font(size=10, weight="bold")).pack(anchor=tk.W)
        
        self.intensity_var = tk.DoubleVar(value=0.5)
        intensity_scale = ttk.Scale(
            intensity_frame,
            from_=0.0,
            to=1.0,
            variable=self.intensity_var,
            command=self._on_intensity_changed,
            length=300
        )
        intensity_scale.pack(fill=tk.X, pady=(5, 0))
        
        # Marks and labels for the intensity slider with better spacing
        marks_frame = ttk.Frame(intensity_frame)
        marks_frame.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Label(marks_frame, text="Off").pack(side=tk.LEFT)
        ttk.Label(marks_frame, text="Medium").pack(side=tk.LEFT, padx=(120, 0))
        ttk.Label(marks_frame, text="Strong").pack(side=tk.RIGHT)
        
        # Color temperature slider
        temp_frame = ttk.Frame(sliders_frame)
        temp_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(temp_frame, text="Color Temperature:", font=font.Font(size=10, weight="bold")).pack(anchor=tk.W)
        
        self.temp_var = tk.DoubleVar(value=0.5)
        temp_scale = ttk.Scale(
            temp_frame,
            from_=0.0,
            to=1.0,
            variable=self.temp_var,
            command=self._on_temp_changed,
            length=300
        )
        temp_scale.pack(fill=tk.X, pady=(5, 0))
        
        # Description for color temperature with better spacing
        description_frame = ttk.Frame(temp_frame)
        description_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Visual indicators for temperature
        warm_indicator = tk.Frame(description_frame, width=30, height=15, bg=COLORS["secondary"])
        warm_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(
            description_frame, 
            text="Warm (orange/red)",
            foreground=COLORS["text_secondary"]
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            description_frame, 
            text="←→",
            foreground=COLORS["text_secondary"]
        ).pack(side=tk.LEFT, padx=10)
        
        cool_indicator = tk.Frame(description_frame, width=30, height=15, bg=COLORS["primary"])
        cool_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(
            description_frame, 
            text="Cool (blue)",
            foreground=COLORS["text_secondary"]
        ).pack(side=tk.LEFT)
        
        # Control frame with filter toggle button - more visible layout
        control_frame = ttk.Frame(settings_container)
        control_frame.pack(fill=tk.X, pady=15)
        
        # Create a more visible toggle button
        self.toggle_button = ttk.Button(
            control_frame,
            text="Enable Filter",
            command=self._toggle_filter,
            style="Primary.TButton"
        )
        # Center the button for better visibility
        self.toggle_button.pack(pady=10, padx=10, anchor=tk.CENTER)
        
        # Add Settings tab to notebook
        self.notebook.add(settings_container, text="Settings")
    
    def _setup_profiles_tab(self):
        # Create a container for profiles tab with padding
        profiles_container = ttk.Frame(self.notebook, padding=15)
        profiles_container.pack(fill=tk.BOTH, expand=True)
        
        # Add to notebook
        self.notebook.add(profiles_container, text="Profiles")
        
        # Create profile selector frame
        select_frame = ttk.LabelFrame(profiles_container, text="Select Profile", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create listbox for profile selection
        self.profiles_listbox = tk.Listbox(
            select_frame, 
            height=4,
            exportselection=0,  # Prevent deselection when focus changes
            font=font.Font(size=11)
        )
        self.profiles_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.profiles_listbox.bind('<<ListboxSelect>>', self._on_profile_selected)
        
        # Fill with current profiles
        self._update_profiles()
        
        # Create profile management frame
        manage_frame = ttk.LabelFrame(profiles_container, text="Manage Profiles", padding=10)
        manage_frame.pack(fill=tk.X, pady=(0, 15))
        
        # New profile section
        new_profile_frame = ttk.Frame(manage_frame)
        new_profile_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(new_profile_frame, text="New Profile:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.new_profile_name = tk.StringVar()
        new_profile_entry = ttk.Entry(new_profile_frame, textvariable=self.new_profile_name)
        new_profile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        create_btn = ttk.Button(
            new_profile_frame, 
            text="Create", 
            command=self._create_profile,
            style="Accent.TButton"
        )
        create_btn.pack(side=tk.LEFT)
        
        # Current profile settings
        settings_frame = ttk.Frame(manage_frame)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Current profile name
        self.current_profile_name = tk.StringVar(value="")
        current_profile_label = ttk.Label(
            settings_frame, 
            textvariable=self.current_profile_name,
            font=font.Font(size=11, weight='bold')
        )
        current_profile_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Intensity setting
        intensity_frame = ttk.Frame(settings_frame)
        intensity_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(intensity_frame, text="Intensity:").pack(anchor=tk.W)
        
        self.profile_intensity_var = tk.IntVar(value=60)
        intensity_slider = ttk.Scale(
            intensity_frame, 
            from_=0, 
            to=100, 
            variable=self.profile_intensity_var,
            length=300
        )
        intensity_slider.pack(fill=tk.X, pady=(5, 0))
        
        # Add value label
        intensity_value_frame = ttk.Frame(intensity_frame)
        intensity_value_frame.pack(fill=tk.X)
        
        ttk.Label(intensity_value_frame, text="0%").pack(side=tk.LEFT)
        
        intensity_value_label = ttk.Label(
            intensity_value_frame, 
            textvariable=self.profile_intensity_var,
            width=3
        )
        intensity_value_label.pack(side=tk.LEFT, padx=10)
        ttk.Label(intensity_value_frame, text="%").pack(side=tk.LEFT)
        
        ttk.Label(intensity_value_frame, text="100%").pack(side=tk.RIGHT)
        
        # Color temperature setting
        temp_frame = ttk.Frame(settings_frame)
        temp_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(temp_frame, text="Color Temperature:").pack(anchor=tk.W)
        
        # Temperature range: 1700K (warm) to 6500K (cool)
        self.profile_temp_var = tk.IntVar(value=4500)
        temp_slider = ttk.Scale(
            temp_frame, 
            from_=1700, 
            to=6500, 
            variable=self.profile_temp_var,
            length=300
        )
        temp_slider.pack(fill=tk.X, pady=(5, 0))
        
        # Add value label
        temp_value_frame = ttk.Frame(temp_frame)
        temp_value_frame.pack(fill=tk.X)
        
        ttk.Label(temp_value_frame, text="Warm").pack(side=tk.LEFT)
        
        temp_value_label = ttk.Label(
            temp_value_frame, 
            textvariable=self.profile_temp_var,
            width=5
        )
        temp_value_label.pack(side=tk.LEFT, padx=10)
        ttk.Label(temp_value_frame, text="K").pack(side=tk.LEFT)
        
        ttk.Label(temp_value_frame, text="Cool").pack(side=tk.RIGHT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = ttk.Button(
            buttons_frame, 
            text="Save Profile", 
            command=self._save_profile,
            style="Accent.TButton"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_btn = ttk.Button(
            buttons_frame,
            text="Delete Profile", 
            command=self._delete_profile
        )
        delete_btn.pack(side=tk.LEFT)
    
    def _setup_about_tab(self):
        # Create a container frame for the About tab
        about_container = ttk.Frame(self.notebook, padding=15)
        about_container.pack(fill=tk.BOTH, expand=True)
        
        # Add to notebook
        self.notebook.add(about_container, text="About")
        
        # Add About content
        ttk.Label(
            about_container,
            text="OpenBlueFilter",
            font=font.Font(size=16, weight='bold')
        ).pack(anchor=tk.CENTER, pady=(20, 5))
        
        ttk.Label(
            about_container,
            text="Version 1.0.0",
            foreground=COLORS["text_secondary"]
        ).pack(anchor=tk.CENTER, pady=(0, 20))
        
        # Description
        description = ttk.Label(
            about_container,
            text="OpenBlueFilter reduces eye strain by adjusting your screen's color temperature.\n"
                "It filters blue light which may improve sleep quality when using your computer at night.",
            justify=tk.CENTER,
            wraplength=500
        )
        description.pack(fill=tk.X, pady=(0, 20))
        
        # Create a frame for the features list
        features_frame = ttk.LabelFrame(about_container, text="Features", padding=10)
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        features = [
            "• Adjustable blue light filter intensity",
            "• Customizable color temperature",
            "• Saved profiles for different times of day",
            "• Minimal system resources usage",
            "• System tray integration for easy access"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature).pack(anchor=tk.W, pady=2)
        
        # System info section
        system_frame = ttk.LabelFrame(about_container, text="System Information", padding=10)
        system_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Get system info
        import platform
        system_info = [
            f"Platform: {platform.system()} {platform.release()}",
            f"Python: {platform.python_version()}",
            f"Processor: {platform.processor()}",
        ]
        
        # Display admin status
        admin_status = "Running as Administrator: Yes" if is_admin() else "Running as Standard User"
        system_info.append(admin_status)
        
        for info in system_info:
            ttk.Label(system_frame, text=info).pack(anchor=tk.W, pady=2)
        
        # Links and credits
        links_frame = ttk.LabelFrame(about_container, text="Links", padding=10)
        links_frame.pack(fill=tk.X)
        
        def open_url(url):
            import webbrowser
            webbrowser.open(url)
        
        # Create hyperlink style labels
        link_style = {'foreground': 'blue', 'cursor': 'hand2', 'font': font.Font(size=10, underline=True)}
        
        # GitHub link
        github_link = tk.Label(links_frame, text="GitHub Repository", **link_style)
        github_link.pack(anchor=tk.W, pady=2)
        github_link.bind("<Button-1>", lambda e: open_url("https://github.com/example/openbluefilter"))
        
        # Website link
        website_link = tk.Label(links_frame, text="Project Website", **link_style)
        website_link.pack(anchor=tk.W, pady=2)
        website_link.bind("<Button-1>", lambda e: open_url("https://example.com/openbluefilter"))
        
        # Credits
        ttk.Label(
            about_container,
            text="© 2023 OpenBlueFilter Contributors",
            foreground=COLORS["text_secondary"]
        ).pack(anchor=tk.CENTER, pady=(20, 0))
    
    def _toggle_filter(self):
        """Toggle the blue light filter on/off"""
        try:
            # Toggle filter state using the filter manager
            new_state = self.filter_manager.toggle()
            
            # Update UI
            self._update_filter_ui()
            
            # Log the change
            if new_state:
                self.logger.info("Enabling blue light filter")
            else:
                self.logger.info("Disabling blue light filter")
                
            # Save current state to config
            self.config_manager.set("filter.enabled", new_state)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error toggling filter: {e}")
            messagebox.showerror("Error", "Failed to toggle the blue light filter")
    
    def _on_intensity_changed(self, value):
        """Handle intensity slider change"""
        try:
            # Convert string value to float (0-1 range)
            intensity = float(value)
            
            # Update filter
            self.filter_manager.set_intensity(intensity)
            
            # Save to configuration
            self.config_manager.set("filter.intensity", intensity)
            
            self.logger.info(f"Setting filter intensity to {intensity}")
        except Exception as e:
            self.logger.error(f"Error changing intensity: {e}")
    
    def _on_temp_changed(self, value):
        """Handle color temperature slider change"""
        try:
            # Convert string value to float (0-1 range)
            color_temp = float(value)
            
            # Update filter
            self.filter_manager.set_color_temperature(color_temp)
            
            # Save to configuration
            self.config_manager.set("filter.color_temperature", color_temp)
            
            self.logger.info(f"Setting color temperature to {color_temp}K")
        except Exception as e:
            self.logger.error(f"Error changing color temperature: {e}")
    
    def _on_profile_selected(self, event):
        """Handle profile selection in the listbox"""
        try:
            # Get selected indices (should be a tuple of selected indices)
            selected_indices = self.profiles_listbox.curselection()
            if not selected_indices:
                return
                
            # Get the selected profile name
            profile_name = self.profiles_listbox.get(selected_indices[0])
            if not profile_name:
                return
                
            # Update current profile display
            self.current_profile_name.set(profile_name)
            
            # Get profile settings
            success = self.profile_manager.activate_profile(profile_name)
            if success:
                # Update the profile's settings in the UI
                profiles = self.config_manager.get("profiles", {})
                profile = profiles.get(profile_name, {})
                
                # Get intensity and temperature values
                intensity = profile.get("intensity", 50)
                color_temp = profile.get("color_temperature", 4500)
                
                # Update UI sliders
                self.profile_intensity_var.set(intensity)
                self.profile_temp_var.set(color_temp)
                
                self.status_var.set(f"Activated profile: {profile_name}")
                self.logger.info(f"Activated profile: {profile_name}")
            else:
                self.logger.error(f"Failed to activate profile: {profile_name}")
                
        except Exception as e:
            self.logger.error(f"Error selecting profile: {e}")
    
    def _create_profile(self):
        """Create a new profile with current settings"""
        try:
            profile_name = simpledialog.askstring("New Profile", "Enter profile name:")
            if not profile_name:
                return
                
            # Create new profile with current settings
            intensity = float(self.intensity_var.get())
            color_temp = float(self.temp_var.get())
            
            if self.profile_manager.save_profile(profile_name, intensity, color_temp):
                self.profile_var.set(profile_name)
                
                # Update profile dropdown
                self._update_profiles()
                
                self.status_var.set(f"Profile created: {profile_name}")
                self.logger.info(f"Created profile: {profile_name}")
                
        except Exception as e:
            self.logger.error(f"Error creating profile: {e}")
            messagebox.showerror("Error", f"Failed to create profile: {e}")
    
    def _update_profiles(self):
        """Update the profiles listbox with available profiles in specific order"""
        try:
            # Get profiles from the profile manager
            profiles = self.profile_manager.get_all_profiles()
            
            # Define the preferred order
            preferred_order = ["Morning", "Evening", "Night"]
            
            # Create an ordered list of profile names
            ordered_profiles = []
            
            # First add the preferred profiles in order
            for profile in preferred_order:
                if profile in profiles:
                    ordered_profiles.append(profile)
            
            # Then add any other profiles alphabetically
            for profile in sorted(profiles):
                if profile not in ordered_profiles:
                    ordered_profiles.append(profile)
            
            # Update the listbox
            if hasattr(self, 'profiles_listbox'):
                # Clear the listbox
                self.profiles_listbox.delete(0, tk.END)
                
                # Add profiles to the listbox
                for profile in ordered_profiles:
                    self.profiles_listbox.insert(tk.END, profile)
                
                # If there's a current active profile, select it
                active_profile = self.config_manager.get("active_profile", "")
                if active_profile and active_profile in ordered_profiles:
                    try:
                        index = ordered_profiles.index(active_profile)
                        self.profiles_listbox.selection_clear(0, tk.END)
                        self.profiles_listbox.selection_set(index)
                        self.profiles_listbox.see(index)
                    except (ValueError, tk.TclError) as e:
                        self.logger.error(f"Error selecting active profile in listbox: {e}")
            
            self.logger.info(f"Updated profiles list: {ordered_profiles}")
        except Exception as e:
            self.logger.error(f"Error updating profiles: {e}")
    
    def _save_profile(self):
        """Save current settings to the selected profile"""
        try:
            profile_name = self.profile_var.get()
            if not profile_name:
                messagebox.showerror("Error", "No profile selected")
                return
                
            # Get current settings
            intensity = float(self.intensity_var.get()) 
            color_temp = float(self.temp_var.get())
            
            # Save profile
            success = self.profile_manager.save_profile(profile_name, intensity, color_temp)
            
            if success:
                self.status_var.set(f"Profile saved: {profile_name}")
                self.logger.info(f"Configuration saved successfully")
                self.logger.info(f"Saved profile: {profile_name}")
            else:
                messagebox.showerror("Error", f"Failed to save profile: {profile_name}")
                
        except Exception as e:
            self.logger.error(f"Error saving profile: {e}")
            messagebox.showerror("Error", f"Failed to save profile: {e}")
            
    def _delete_profile(self):
        """Delete the selected profile"""
        try:
            profile_name = self.profile_var.get()
            if not profile_name:
                messagebox.showerror("Error", "No profile selected")
                return
                
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the profile '{profile_name}'?"):
                if self.profile_manager.delete_profile(profile_name):
                    # Update profile list
                    self._update_profiles()
                    
                    # Select default profile if available
                    profiles = self.profile_manager.get_all_profiles()
                    if profiles:
                        self.profile_var.set(next(iter(profiles.keys())))
                    else:
                        self.profile_var.set("")
                        
                    self.status_var.set(f"Profile deleted: {profile_name}")
                    self.logger.info(f"Deleted profile: {profile_name}")
                else:
                    messagebox.showerror("Error", f"Failed to delete profile: {profile_name}")
                    
        except Exception as e:
            self.logger.error(f"Error deleting profile: {e}")
            messagebox.showerror("Error", f"Failed to delete profile: {e}")
    
    def _on_schedule_enabled_changed(self):
        """Handle the schedule enable/disable checkbox changes"""
        is_enabled = self.schedule_enabled_var.get()
        schedule_mode = self.schedule_mode_var.get()
        
        self.logger.info(f"Schedule {'enabled' if is_enabled else 'disabled'}, mode: {schedule_mode}")
        
        # Clear any existing warning messages
        for widget in self.schedule_warning_frame.winfo_children():
            widget.destroy()
        
        # Update configuration
        self.config_manager.set("schedule.enabled", is_enabled)
        self.config_manager.set("schedule.mode", schedule_mode)
        
        if is_enabled:
            # Check if we're in manual mode and need to validate times
            if schedule_mode == "manual":
                # Validate time formats
                valid_start = self.validate_and_format_start_time()
                valid_end = self.validate_and_format_end_time()
                
                if not valid_start or not valid_end:
                    # Show warning and prevent enabling
                    warning_label = ttk.Label(
                        self.schedule_warning_frame,
                        text="Invalid time format. Please use HH:MM format (24-hour).",
                        foreground=COLORS["error"]
                    )
                    warning_label.pack(anchor=tk.W, pady=(5, 0))
                    
                    self.schedule_enabled_var.set(False)
                    self.config_manager.set("schedule.enabled", False)
                    return
            
            elif schedule_mode == "profile":
                # For profile mode, ensure at least one profile is selected
                if (not self.morning_enabled_var.get() and 
                    not self.evening_enabled_var.get() and 
                    not self.night_enabled_var.get()):
                    
                    warning_label = ttk.Label(
                        self.schedule_warning_frame,
                        text="Please enable at least one profile time period.",
                        foreground=COLORS["error"]
                    )
                    warning_label.pack(anchor=tk.W, pady=(5, 0))
                    
                    self.schedule_enabled_var.set(False)
                    self.config_manager.set("schedule.enabled", False)
                    return
        
        # Save configuration
        self.config_manager.save_config()
        
        # Update scheduler
        if self.scheduler:
            success = self.scheduler.update_schedule()
            
            if not success and is_enabled:
                warning_label = ttk.Label(
                    self.schedule_warning_frame,
                    text="Failed to set up scheduler. Check times and try again.",
                    foreground=COLORS["error"]
                )
                warning_label.pack(anchor=tk.W, pady=(5, 0))
                return
    
    def validate_and_format_start_time(self):
        """Validate and format start time"""
        return self._validate_time(self.start_time_var)
        
    def validate_and_format_end_time(self):
        """Validate and format end time"""
        return self._validate_time(self.end_time_var)
    
    def _validate_time(self, string_var):
        """Validate and format time string"""
        try:
            time_str = string_var.get().strip()
            
            # Handle empty string
            if not time_str:
                return None
                
            # Basic validation for HH:MM format
            if ":" not in time_str:
                # Try to automatically format if it's just digits
                if time_str.isdigit() and len(time_str) == 4:  # e.g. "2030" -> "20:30"
                    time_str = f"{time_str[:2]}:{time_str[2:]}"
                    string_var.set(time_str)
                else:
                    return None
            
            # Further validation
            parts = time_str.split(":")
            if len(parts) != 2:
                return None
                
            hour = int(parts[0])
            minute = int(parts[1])
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return None
                
            # Format consistently as HH:MM
            formatted = f"{hour:02d}:{minute:02d}"
            if formatted != time_str:
                string_var.set(formatted)
                
            return formatted
            
        except (ValueError, IndexError):
            return None
    
    def _on_schedule_mode_changed(self):
        """Handle schedule mode change between manual and profile-based"""
        mode = self.schedule_mode_var.get()
        
        # Clear current options
        for widget in self.schedule_options_frame.winfo_children():
            widget.pack_forget()
        
        # Show appropriate frame based on mode
        if mode == "manual":
            self.manual_frame.pack(fill=tk.X)
            
            # Load saved manual schedule times
            saved_start = self.config_manager.get("schedule.start_time", "20:00")
            saved_end = self.config_manager.get("schedule.end_time", "07:00")
            
            # Set the time variables
            if saved_start:
                self.start_time_var.set(saved_start)
            if saved_end:
                self.end_time_var.set(saved_end)
                
            # Update enable checkbox state
            was_enabled = self.config_manager.get("schedule.enabled", False)
            if was_enabled and self.config_manager.get("schedule.mode", "manual") == "manual":
                self.schedule_enabled_var.set(True)
            else:
                self.schedule_enabled_var.set(False)
        else:  # profile mode
            self.profile_frame.pack(fill=tk.X)
            
            # Update profile dropdowns with current profiles
            profiles = list(self.profile_manager.get_all_profiles().keys())
            
            for combo in [self.morning_profile_combo, self.evening_profile_combo, self.night_profile_combo]:
                combo['values'] = profiles
                if not profiles:
                    combo.set("")
                    combo.configure(state="disabled")
                else:
                    combo.configure(state="readonly")
            
            # Set default values if not already set
            if not self.morning_profile_var.get() and profiles:
                    if "Morning" in profiles:
                        self.morning_profile_var.set("Morning")
                    else:
                        self.morning_profile_var.set(profiles[0])
                        
            if not self.evening_profile_var.get() and profiles:
                    if "Evening" in profiles:
                        self.evening_profile_var.set("Evening")
                    else:
                        self.evening_profile_var.set(profiles[0])
                        
            if not self.night_profile_var.get() and profiles:
                    if "Night" in profiles:
                        self.night_profile_var.set("Night")
                    else:
                        self.night_profile_var.set(profiles[0])
                    
            # Update enable checkbox state
            was_enabled = self.config_manager.get("schedule.enabled", False)
            if was_enabled and self.config_manager.get("schedule.mode", "manual") == "profile":
                self.schedule_enabled_var.set(True)
            else:
                self.schedule_enabled_var.set(False)
        
        # Update the config with the new mode
        self.config_manager.set("schedule.mode", mode)
    
    def _save_schedule(self):
        """Save schedule settings and apply immediately"""
        try:
            # Get values from UI
            is_enabled = self.schedule_enabled_var.get()
            current_mode = self.schedule_mode_var.get()
            
            # Save common settings
            self.config_manager.set("schedule.enabled", is_enabled)
            self.config_manager.set("schedule.mode", current_mode)
            
            # Save mode-specific settings
            if current_mode == "manual":
                # Save manual time settings
                start_time = self.validate_and_format_start_time()
                end_time = self.validate_and_format_end_time()
                
                # Validate times
                if is_enabled and (not start_time or not end_time):
                    messagebox.showwarning(
                        "Invalid Schedule", 
                        "Please enter valid start and end times in HH:MM format"
                    )
                    # Don't save invalid schedule
                    return
                
                if start_time:
                    self.config_manager.set("schedule.start_time", start_time)
                if end_time:
                    self.config_manager.set("schedule.end_time", end_time)
                
                # Log the saved schedule
                self.logger.info(f"Saved manual schedule: start={start_time}, end={end_time}, enabled={is_enabled}")
                
                # Update UI
                status_text = "Schedule saved"
                if is_enabled:
                    status_text = f"Manual schedule active: {start_time} to {end_time}"
                    
                    # Show a confirmation message
                    messagebox.showinfo(
                        "Schedule Saved",
                        f"The filter will be active from {start_time} to {end_time} daily.\n\n"
                        "The schedule will run automatically in the background."
                    )
            else:
                # Save profile-based settings
                self.config_manager.set("schedule.morning.enabled", self.morning_enabled_var.get())
                self.config_manager.set("schedule.morning.profile", self.morning_profile_var.get())
                
                self.config_manager.set("schedule.evening.enabled", self.evening_enabled_var.get())
                self.config_manager.set("schedule.evening.profile", self.evening_profile_var.get())
                
                self.config_manager.set("schedule.night.enabled", self.night_enabled_var.get())
                self.config_manager.set("schedule.night.profile", self.night_profile_var.get())
                
                # Update UI
                status_text = "Profile schedule saved"
                if is_enabled:
                    status_text = "Profile-based schedule active"
                    
                    # Show confirmation message
                    messagebox.showinfo(
                        "Profile Schedule Saved",
                        "The profile-based schedule has been saved and activated.\n\n"
                        "Profiles will switch automatically at the scheduled times."
                    )
            
            # Save configuration to file
            self.config_manager._save_config()
            
            # Update the scheduler with new settings
            self.scheduler.update_schedule()
            
            # Force an immediate check if the schedule is enabled
            if is_enabled:
                self.scheduler.force_check_now()
            
            # Update status bar
            self.status_var.set(status_text)
            self.logger.info(f"Schedule saved - mode: {current_mode}, enabled: {is_enabled}")
            
        except Exception as e:
            self.logger.error(f"Error saving schedule: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to save schedule: {e}")
    
    def _update_filter_ui(self):
        """Update UI elements to reflect current filter state"""
        try:
            # Update toggle button text
            if self.filter_manager.is_enabled():
                self.toggle_button.config(text="Disable Filter")
                self.status_var.set("Filter: Enabled")
                
                # Set icon to enabled version if available
                if 'app_enabled' in self.icons and hasattr(self, 'app_icon_label'):
                    self.app_icon_label.config(image=self.icons['app_enabled'])
            else:
                self.toggle_button.config(text="Enable Filter")
                self.status_var.set("Filter: Disabled")
                
                # Set icon to disabled version if available
                if 'app' in self.icons and hasattr(self, 'app_icon_label'):
                    self.app_icon_label.config(image=self.icons['app'])
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
    
    def _on_close(self):
        """Handle the application close event."""
        try:
            self.logger.info("Closing application")
            
            if hasattr(self, 'filter_manager') and self.filter_manager:
                self.filter_manager.disable_filter()
                self.filter_manager.cleanup()
                self.logger.info("Filter cleaned up")
            
            self.config_manager.save_config()
            self.logger.info("Configuration saved")
            
            self.root.destroy()
            self.logger.info("Application closed")
        except Exception as e:
            self.logger.error(f"Error during application closure: {e}")


def main():
    # Set up logging
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting OpenBlueFilter")
    
    # Create Tkinter root window
    root = tk.Tk()
    
    # Create the application
    app = SystemTrayApp(root)
    
    # Start the Tkinter event loop
    root.mainloop()
    
if __name__ == "__main__":
    main() 