import json

class MISSTsettings():
    def __init__(self):
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
            json.dump(data, f)

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


if __name__ == "__main__":
    settings = MISSTsettings()
    #print(settings.getSetting("serverBase"))
    #settings.setSetting("serverBase", "http://localhost:5001")
    #print(settings.getSetting("serverBase"))
    settings.applyThemeSettings("./MISST/Assets/Themes/MISST.json", "./MISST/Assets/Themes/maluableJSON")