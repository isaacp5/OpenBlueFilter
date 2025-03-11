import logging
from .filter_manager import AbstractFilterManager

class DummyFilterManager(AbstractFilterManager):
    """A dummy implementation of the filter manager for testing or unsupported platforms"""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self.logger.warning("Using DummyFilterManager - no actual filtering will occur")
    
    def enable(self):
        self.logger.info("Dummy filter enabled (no actual effect)")
        self._enabled = True
        self.config_manager.set("filter_enabled", True)
        return True
    
    def disable(self):
        self.logger.info("Dummy filter disabled (no actual effect)")
        self._enabled = False
        self.config_manager.set("filter_enabled", False)
        return True
    
    def set_intensity(self, value):
        self.logger.info(f"Dummy filter intensity set to {value} (no actual effect)")
        self._intensity = max(0.0, min(1.0, float(value)))
        self.config_manager.set("intensity", self._intensity)
        return True
    
    def set_color_temperature(self, value):
        self.logger.info(f"Dummy filter color temperature set to {value}K (no actual effect)")
        self._color_temperature = max(1000, min(6500, int(value)))
        self.config_manager.set("color_temperature", self._color_temperature)
        return True 