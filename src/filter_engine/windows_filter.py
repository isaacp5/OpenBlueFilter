import logging
import ctypes
import math
from ctypes import windll, byref, Structure, POINTER, c_int, c_uint, c_ulong, c_float
from .filter_manager import AbstractFilterManager

class COLORREF(Structure):
    _fields_ = [
        ('byRed', c_uint),
        ('byGreen', c_uint),
        ('byBlue', c_uint),
        ('byReserved', c_uint)
    ]

class ColorMatrix(Structure):
    _fields_ = [
        ('matrix', (c_float * 5) * 5)
    ]

class WindowsFilterManager(AbstractFilterManager):
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.logger = logging.getLogger(__name__)
        self._magnification_dll = None
        self._matrix = None
        self._initialize_magnification()
        
    def _initialize_magnification(self):
        try:
            # Load the Windows Magnification API
            self._magnification_dll = ctypes.WinDLL("Magnification.dll")
            
            # Initialize the magnification runtime
            if not self._magnification_dll.MagInitialize():
                self.logger.error("Failed to initialize magnification runtime")
                return False
                
            self.logger.info("Windows Magnification API initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Windows Magnification API: {e}")
            return False
    
    def _cleanup_magnification(self):
        if self._magnification_dll:
            self._magnification_dll.MagUninitialize()
            self.logger.info("Windows Magnification API uninitialized")
    
    def _create_color_matrix(self):
        # Create a color matrix adjusted for intensity and color temperature
        # This is a simplified version - actual implementation would be more sophisticated
        intensity = self._intensity
        temp_factor = (6500 - self._color_temperature) / 3800  # Normalize temp to 0-1 range
        
        # Clamp values to safe range
        temp_factor = max(0, min(1, temp_factor))
        
        # Reduce blue based on intensity and temperature
        blue_reduction = intensity * temp_factor
        
        # Adjust red slightly higher for warmer appearance
        red_boost = intensity * temp_factor * 0.3
        
        matrix = ColorMatrix()
        
        # Identity matrix
        for i in range(5):
            for j in range(5):
                matrix.matrix[i][j] = 1.0 if i == j else 0.0
        
        # Adjust color channels
        matrix.matrix[0][0] = 1.0 + red_boost  # Red channel (increased slightly)
        matrix.matrix[1][1] = 1.0 - (intensity * 0.1)  # Green channel (reduced slightly)
        matrix.matrix[2][2] = 1.0 - blue_reduction  # Blue channel (reduced based on settings)
        
        self._matrix = matrix
        return matrix
    
    def _apply_color_filter(self, enable=True):
        try:
            if enable:
                matrix = self._create_color_matrix()
                result = self._magnification_dll.MagSetFullscreenColorEffect(byref(matrix))
            else:
                # Use identity matrix to disable the filter
                matrix = ColorMatrix()
                for i in range(5):
                    for j in range(5):
                        matrix.matrix[i][j] = 1.0 if i == j else 0.0
                result = self._magnification_dll.MagSetFullscreenColorEffect(byref(matrix))
                
            if not result:
                error_code = ctypes.GetLastError()
                self.logger.error(f"Failed to {'apply' if enable else 'remove'} color filter. Error code: {error_code}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error {'applying' if enable else 'removing'} color filter: {e}")
            return False
    
    def enable(self):
        self.logger.info("Enabling Windows blue light filter")
        result = self._apply_color_filter(True)
        if result:
            self._enabled = True
            self.config_manager.set("filter_enabled", True)
        return result
    
    def disable(self):
        self.logger.info("Disabling Windows blue light filter")
        result = self._apply_color_filter(False)
        if result:
            self._enabled = False
            self.config_manager.set("filter_enabled", False)
        return result
    
    def set_intensity(self, value):
        self.logger.info(f"Setting filter intensity to {value}")
        self._intensity = max(0.0, min(1.0, float(value)))
        self.config_manager.set("intensity", self._intensity)
        
        # Apply the change if filter is enabled
        if self._enabled:
            return self._apply_color_filter(True)
        return True
    
    def set_color_temperature(self, value):
        self.logger.info(f"Setting color temperature to {value}K")
        # Clamp to a reasonable range (1000K to 6500K)
        self._color_temperature = max(1000, min(6500, int(value)))
        self.config_manager.set("color_temperature", self._color_temperature)
        
        # Apply the change if filter is enabled
        if self._enabled:
            return self._apply_color_filter(True)
        return True
    
    def __del__(self):
        # Cleanup when object is destroyed
        self._cleanup_magnification() 