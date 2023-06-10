import json
import os
import shutil

import torch


class MISSTsettings():
    def __init__(self):
        # Check if the config file exists, if not create it
        # Path: MISST\MISSTsettings.py
        if not os.path.isfile("config.json"):
            self.createSettings()
        return
    
    def getSetting(self, setting):
        # Get the setting from the saved config file
        # Path: MISST\MISSTsettings.py
        # setting: The setting to be retrieved
        with open("config.json", "r") as f:
            data = json.load(f)
        return data[setting]
    
    def setSetting(self, setting, value):
        # Set the setting in the saved config file
        # Path: MISST\MISSTsettings.py
        # setting: The setting to be set
        # value: The value to be set
        with open("config.json", "r") as f:
            data = json.load(f)
        data[setting] = value
        with open("config.json", "w") as f:
            json.dump(data, f, indent=4)

    def applyThemeSettings(self, themeFile, baseTheme):
        # Apply the chosen colorways to the theme file
        # Path: MISST\MISSTsettings.py
        # themeFile: The theme file to be modified
        # colorways: The colorways to be applied
        with open(baseTheme, "r") as f:
            data = f.read()
        colorways = ["defaultLightColor", "defaultDarkColor", "defaultLightHoverColor", "defaultDarkHoverColor", "defaultLightDarker", "defaultDarkDarker"]
        for colorway in colorways:
            data = data.replace(colorway, self.getSetting(colorway.replace('default', 'chosen')))
            with open(themeFile, "w") as f:
                f.write(data)

    def resetDefaultTheme(self, themeFile, baseTheme):
        # Reset the theme file to the default theme
        # Path: MISST\MISSTsettings.py
        # themeFile: The theme file to be modified
        # colorways: The colorways to be applied
        with open(baseTheme, "r") as f:
            data = f.read()
        colorways = ["defaultLightColor", "defaultDarkColor", "defaultLightHoverColor", "defaultDarkHoverColor", "defaultLightDarker", "defaultDarkDarker"]
        for colorway in colorways:
            self.setSetting(colorway.replace('default', 'chosen'), self.getSetting(colorway))
            data = data.replace(colorway, self.getSetting(colorway))
            with open(themeFile, "w") as f:
                f.write(data)

    def createSettings(self):
        # Creates a new config file in the apps directory with all the default settings.
        shutil.copy("Assets/config_base.json", "config.json")
        self.setSetting("accelerate_on_gpu", "true" if torch.cuda.is_available() else "false") #Automatically set GPU acceleration to true if available.


class MISSTconfig:
    def __init__(self, configPath):
        # Check if the config file exists, if not create it
        # Path: MISST\MISSTsettings.py
        if not os.path.isfile(f"{configPath}/.misst"):
            self.createConfig(configPath)
        return
    
    def getConfig(self, configPath):
        # Get the setting from the saved config file
        # Path: MISST\MISSTsettings.py
        # setting: The setting to be retrieved
        with open(f"{configPath}/.misst", "r") as f:
            data = json.load(f)
        return data
    
    def setConfig(self, configPath, setting, value):
        # Set the setting in the saved config file
        # Path: MISST\MISSTsettings.py
        # setting: The setting to be set
        # value: The value to be set
        with open(f"{configPath}/.misst", "r") as f:
            data = json.load(f)
        data[setting] = value
        with open(f"{configPath}/.misst", "w") as f:
            json.dump(data, f, indent=4)

    def createConfig(self, configPath):
        # Creates a new config file in the apps directory with all the default settings.
        with open(f"{configPath}/.misst", "w") as f:
            json.dump({"image_url": "null", "image_raw": "null", "lyrics": "null"}, f, indent=4)
        f.close()