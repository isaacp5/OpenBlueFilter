import logging
from abc import ABC, abstractmethod

class AbstractFilterManager(ABC):
    def __init__(self, config_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self._enabled = False
        self._intensity = self.config_manager.get("intensity", 0.5)
        self._color_temperature = self.config_manager.get("color_temperature", 3500)
    
    @abstractmethod
    def enable(self):
        """Enable the blue light filter"""
        pass
    
    @abstractmethod
    def disable(self):
        """Disable the blue light filter"""
        pass
    
    @abstractmethod
    def set_intensity(self, value):
        """Set the filter intensity (0.0 to 1.0)"""
        pass
    
    @abstractmethod
    def set_color_temperature(self, value):
        """Set the color temperature in Kelvin"""
        pass
    
    def is_enabled(self):
        """Check if the filter is currently enabled"""
        return self._enabled
    
    def toggle(self):
        """Toggle the filter state"""
        if self._enabled:
            return self.disable()
        else:
            return self.enable()
    
    def apply_config(self):
        """Apply the current configuration settings"""
        self._intensity = self.config_manager.get("intensity", 0.5)
        self._color_temperature = self.config_manager.get("color_temperature", 3500)
        
        # Apply the settings
        self.set_intensity(self._intensity)
        self.set_color_temperature(self._color_temperature)
        
        # Enable/disable according to config
        if self.config_manager.get("filter_enabled", False):
            self.enable()
        else:
            self.disable()


def get_filter_manager(config_manager):
    """Factory function to get the appropriate filter manager for the current platform"""
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        from .windows_filter import WindowsFilterManager
        return WindowsFilterManager(config_manager)
    elif system == "darwin":
        # macOS implementation
        from .macos_filter import MacOSFilterManager
        return MacOSFilterManager(config_manager)
    elif system == "linux":
        # Linux implementation
        from .linux_filter import LinuxFilterManager
        return LinuxFilterManager(config_manager)
    else:
        # Fallback to dummy implementation
        from .dummy_filter import DummyFilterManager
        return DummyFilterManager(config_manager) 