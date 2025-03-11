import json
import os
import logging
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        "filter_enabled": False,
        "intensity": 0.5,  # 0.0 to 1.0
        "color_temperature": 3500,  # Kelvin (lower = warmer)
        "start_with_system": False,
        "schedule_enabled": False,
        "schedule_start": "20:00",  # 24-hour format
        "schedule_end": "07:00",
        "auto_adjust_with_sunset": False,
        "location": {
            "latitude": None,
            "longitude": None
        },
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
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".openbluefilter"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Ensure all default keys exist in loaded config
                updated_config = self.DEFAULT_CONFIG.copy()
                self._update_nested_dict(updated_config, config)
                
                self.logger.info("Configuration loaded successfully")
                return updated_config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            self.logger.info("Config file not found, creating default configuration")
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _update_nested_dict(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
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
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        
        # Navigate to the innermost dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self._save_config()
    
    def save_profile(self, profile_name, settings):
        if "profiles" not in self.config:
            self.config["profiles"] = {}
            
        self.config["profiles"][profile_name] = settings
        self._save_config()
        
    def delete_profile(self, profile_name):
        if "profiles" in self.config and profile_name in self.config["profiles"]:
            del self.config["profiles"][profile_name]
            
            # Reset active profile if it was deleted
            if self.config.get("active_profile") == profile_name:
                if self.config["profiles"]:
                    self.config["active_profile"] = next(iter(self.config["profiles"]))
                else:
                    self.config["active_profile"] = None
                    
            self._save_config()
            return True
        return False
    
    def get_all_profiles(self):
        return self.config.get("profiles", {})
    
    def save(self):
        return self._save_config() 