import logging
from .filter_manager import AbstractFilterManager

class LinuxFilterManager(AbstractFilterManager):
    """A placeholder implementation for Linux. Currently just uses the dummy filter functionality."""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self.logger.warning("Linux implementation not fully developed - limited functionality available")
    
    def enable(self):
        self.logger.info("Linux filter enabled (limited functionality)")
        self._enabled = True
        self.config_manager.set("filter_enabled", True)
        return True
    
    def disable(self):
        self.logger.info("Linux filter disabled")
        self._enabled = False
        self.config_manager.set("filter_enabled", False)
        return True
    
    def set_intensity(self, value):
        self.logger.info(f"Linux filter intensity set to {value}")
        self._intensity = max(0.0, min(1.0, float(value)))
        self.config_manager.set("intensity", self._intensity)
        return True
    
    def set_color_temperature(self, value):
        self.logger.info(f"Linux filter color temperature set to {value}K")
        self._color_temperature = max(1000, min(6500, int(value)))
        self.config_manager.set("color_temperature", self._color_temperature)
        return True 