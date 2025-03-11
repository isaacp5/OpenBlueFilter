import logging

class ProfileManager:
    def __init__(self, config_manager, filter_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.filter_manager = filter_manager
        
    def get_all_profiles(self):
        return self.config_manager.get_all_profiles()
    
    def get_active_profile_name(self):
        return self.config_manager.get("active_profile")
    
    def get_active_profile(self):
        profile_name = self.get_active_profile_name()
        if not profile_name:
            return None
            
        profiles = self.get_all_profiles()
        return profiles.get(profile_name)
    
    def activate_profile(self, profile_name):
        profiles = self.get_all_profiles()
        
        if profile_name not in profiles:
            self.logger.error(f"Profile '{profile_name}' does not exist")
            return False
            
        profile_settings = profiles[profile_name]
        
        # Update the active profile in config
        self.config_manager.set("active_profile", profile_name)
        
        # Apply the profile settings to the filter
        intensity = profile_settings.get("intensity", 0.5)
        color_temperature = profile_settings.get("color_temperature", 3500)
        
        self.filter_manager.set_intensity(intensity)
        self.filter_manager.set_color_temperature(color_temperature)
        
        # Update global settings in config
        self.config_manager.set("intensity", intensity)
        self.config_manager.set("color_temperature", color_temperature)
        
        self.logger.info(f"Activated profile: {profile_name}")
        return True
    
    def save_profile(self, profile_name, intensity=None, color_temperature=None):
        # Get current settings if not provided
        if intensity is None:
            intensity = self.config_manager.get("intensity", 0.5)
            
        if color_temperature is None:
            color_temperature = self.config_manager.get("color_temperature", 3500)
            
        profile = {
            "intensity": intensity,
            "color_temperature": color_temperature
        }
        
        self.config_manager.save_profile(profile_name, profile)
        self.logger.info(f"Saved profile: {profile_name}")
        return True
    
    def delete_profile(self, profile_name):
        result = self.config_manager.delete_profile(profile_name)
        if result:
            self.logger.info(f"Deleted profile: {profile_name}")
        else:
            self.logger.warning(f"Failed to delete profile: {profile_name}")
        return result
    
    def create_default_profiles(self):
        profiles = self.get_all_profiles()
        
        if not profiles:
            self.logger.info("Creating default profiles")
            
            # Create default profiles
            default_profiles = {
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
            }
            
            for name, settings in default_profiles.items():
                self.save_profile(name, settings["intensity"], settings["color_temperature"])
                
            # Set Day as the default active profile
            self.config_manager.set("active_profile", "Day")
            return True
            
        return False 