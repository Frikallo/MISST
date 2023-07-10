import ctypes
import os
import platform
import re
import shutil
import sys
import threading
import time
import tkinter
import uuid
from colorsys import hls_to_rgb, rgb_to_hls

import customtkinter
import demucs
import music_tag
import psutil
import requests
import torch
from MISSTplayer import MISSTplayer
from MISSTsettings import MISSTsettings
from vcolorpicker import getColor, hex2rgb, rgb2hex, useLightTheme


class MISSTconsole():
    """
    A class to handle the console output of MISST
    """
    def __init__(self, terminal:customtkinter.CTkTextbox, ogText:str) -> None:
        """
        Parameters

        terminal : tkinter.Text
            The tkinter.Text widget to be used as the console
        ogText : str
            The original text to be displayed in the console
        """
        self.consoleText = ogText
        self.terminal = terminal
        self.curThread = None
        self.terminal.delete("0.0", "end")  # delete all text
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")

    def updateThread(self, text:str) -> None:
        """
        A thread to update the console text

        Args:
            text (str): The text to be added to the console
        """
        t = 0
        while True:
            time.sleep(0.5)
            if t > 3:
                t -= t
            periods = ["", ".", "..", "..."]
            self.terminal.configure(state="normal")
            self.terminal.delete("0.0", "end")
            self.terminal.insert("0.0", f"{self.consoleText}{text}{periods[t]}")
            self.terminal.configure(state="disabled")
            t += 1

    def update(self, text:str) -> None:
        """
        Update the console text

        Args:
            text (str): The text to be added to the console
        """
        self.curThread = threading.Thread(target=self.updateThread, args=(text,), daemon=True)
        self.curThread.start()

    def endUpdate(self) -> None:
        """
        End the update thread

        Args:
            text (str): The text to be added to the console
        """
        MISSThelpers.terminate_thread(self, self.curThread)
        self.terminal.configure(state="normal")
        self.terminal.delete("0.0", "end")
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")

    def addLine(self, text:str) -> None:
        """
        Add a line to the console

        Args:
            text (str): The text to be added to the console
        """
        self.consoleText += f"{text}"
        self.terminal.configure(state="normal")
        self.terminal.delete("0.0", "end")
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")

    def editLine(self, text:str, line_number:int) -> None:
        """
        Edit a line in the console

        Args:
            text (str): The text to be added to the console
            line_number (int): The line number to be edited
        """
        self.consoleText = text
        self.terminal.configure(state="normal")
        self.terminal.delete(f"{line_number + 1}.0", f"end")
        self.terminal.insert(f"{line_number + 1}.0", text)
        self.terminal.configure(state="disabled")

class MISSThelpers():
    """
    A class filled with helper methods for MISST
    """
    def update_rpc(
        self,
        Ltext:str = None,
        Dtext:str = None,
        image:str = "icon-0",
        large_text:str = "MISST",
        end_time:int = None,
        small_image:str = None,
    ) -> None:
        """
        Update the Discord Rich Presence

        Args:
            Ltext (str, optional): The large text to be displayed. Defaults to None.
            Dtext (str, optional): The details text to be displayed. Defaults to None.
            image (str, optional): The image to be displayed. Defaults to "icon-0".
            large_text (str, optional): The large text to be displayed. Defaults to "MISST".
            end_time (int, optional): The end time of the activity. Defaults to None.
            small_image (str, optional): The small image to be displayed. Defaults to None.
        """
        start_time = time.time()
        if self.RPC_CONNECTED:
            try:
                self.RPC.update(
                    large_image=image,
                    small_image=small_image,
                    start=start_time,
                    end=end_time,
                    large_text=large_text,
                    state=Ltext,
                    details=Dtext,
                )
            except:
                return
        return
    
    def apple_music(url:str, outdir:str) -> None:
        """
        Download an Apple Music song

        Args:
            url (str): The Apple Music song URL
            outdir (str): The output directory
        """
        host = 'https://api.fabdl.com'
        info = requests.get(host + '/apple-music/get?url=', params={'url': url}).json()['result']
        convert_task = requests.get(host + f'/apple-music/mp3-convert-task/{info["gid"]}/{info["id"]}')
        tid = convert_task.json()['result']['tid']
        convert_task = requests.get(host + f'/apple-music/mp3-convert-progress/{tid}')
        r = requests.get(host + convert_task.json()['result']['download_url'])  
        with open(f"{outdir}/{info['artists'] + ' - ' + info['name']}.mp3", 'wb') as f:
            f.write(r.content)
        try:
            audiofile = music_tag.load_file(f"{outdir}/{info['artists'] + ' - ' + info['name']}.mp3")
            audiofile['artwork'] = requests.get(info['image']).content
            audiofile.save()
        except:
            pass

    def change_theme(theme:str) -> None:
        """
        Change the theme of the application

        Args:
            theme (str): The theme to be changed to
        """
        customtkinter.set_appearance_mode(theme)

    def checkbox_event(checkbox:customtkinter.CTkCheckBox, export_slider:customtkinter.CTkSlider, sound:str, player:MISSTplayer, slider:customtkinter.CTkSlider) -> None:
        """
        Change the volume of a sound

        Args:
            checkbox (tkinter.Checkbutton): The checkbox
            sound (str): The sound to be changed
            player (MISSTplayer): The sound player
            slider (tkinter.Scale): The volume slider
        """
        if checkbox.get() == "on":
            player.set_volume(sound, slider.get())
        else:
            slider.set(0)
            player.set_volume(sound, slider.get())

        MISSThelpers.slider_event(slider.get(), export_slider, sound, player, checkbox)

    def slider_event(value:int, export_slider:customtkinter.CTkSlider, sound:str, player:MISSTplayer, checkbox:customtkinter.CTkCheckBox) -> None:
        """
        Change the volume of a sound

        Args:
            value (int): The volume value
            sound (str): The sound to be changed
            player (MISSTplayer): The sound player
            checkbox (tkinter.Checkbutton): The checkbox
        """
        settings = MISSTsettings()
        export_slider[0].set(value)
        if value >= 0.01:
            checkbox.set("on")
            export_slider[1].configure(border_color=settings.getSetting("chosenLightColor") if customtkinter.get_appearance_mode() == "Light" else settings.getSetting("chosenDarkColor"))
            player.set_volume(sound, value)
        else:
            checkbox.set("off")
            export_slider[1].configure(border_color="#3E454A")
            player.set_volume(sound, value)
    
    def MISSTlistdir(self, directory:str) -> list:
        """
        List all MISST folders in a directory

        Args:
            directory (str): The directory to be searched
        """
        try:
            os_list = os.listdir(directory)
            misst_list = []
            for _ in os_list:
                required_files = ["bass.flac", "drums.flac", "other.flac", "vocals.flac", ".misst"]
                found = 0
                for file in required_files:
                    if os.path.isfile(f"{directory}/{_}/{file}"):
                        found += 1
                if len(required_files) == found:
                    misst_list.append(_)
            return misst_list
        except:
            return []
        
    def getsize(self, dir:str) -> int:
        """
        Get the size of a directory

        Args:
            dir (str): The directory to be searched
        """
        total = 0
        for entry in os.scandir(dir):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.getsize(self, entry.path)
        return total

    def adjust_color_lightness(r:int, g:int, b:int, factor:int) -> str:
        """
        Adjust the lightness of a color

        Args:
            r (int): The red value
            g (int): The green value
            b (int): The blue value
            factor (int): The factor to be adjusted by
        """
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        l = max(min(l * factor, 1.0), 0.0)
        r, g, b = hls_to_rgb(h, l, s)
        return f"#{rgb2hex(int(r * 255), int(g * 255), int(b * 255))}"
    
    def darken_color(r:int, g:int, b:int, factor:int = 0.1) -> str:
        """
        Darken a color

        Args:
            r (int): The red value
            g (int): The green value
            b (int): The blue value
            factor (int, optional): The factor to be darkened by. Defaults to 0.1.
        """
        return MISSThelpers.adjust_color_lightness(r, g, b, 1 - factor)

    def updateTheme(self, color:str) -> str: 
        """
        Update the theme of the application

        Args:
            color (str): The color to be changed
        """
        if color == "light":
            cur_color = self.settings.getSetting("chosenLightColor")
            old_color = (hex2rgb(cur_color.replace("#", "")))
            useLightTheme(True if customtkinter.get_appearance_mode() == "Light" else False)
            self.withdraw() # Hide the window
            chosen_color = f"#{rgb2hex(getColor(old_color))}"
            self.deiconify() # Show the window
            rgb_chosen = hex2rgb(chosen_color.replace("#", ""))
            self.settings.setSetting("chosenLightColor", chosen_color)
            self.settings.setSetting("chosenLightHoverColor", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.2))
            self.settings.setSetting("chosenLightDarker", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.35))
            self.settings.applyThemeSettings("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
            self.button_light.configure(fg_color=chosen_color, hover_color=chosen_color)
        else:
            cur_color = self.settings.getSetting("chosenDarkColor")
            old_color = (hex2rgb(cur_color.replace("#", "")))
            useLightTheme(True if customtkinter.get_appearance_mode() == "Light" else False)
            self.withdraw() # Hide the window
            chosen_color = f"#{rgb2hex(getColor(old_color))}"
            self.deiconify() # Show the window
            rgb_chosen = hex2rgb(chosen_color.replace("#", ""))
            self.settings.setSetting("chosenDarkColor", chosen_color)
            self.settings.setSetting("chosenDarkHoverColor", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.2))
            self.settings.setSetting("chosenDarkDarker", MISSThelpers.darken_color(rgb_chosen[0], rgb_chosen[1], rgb_chosen[2], 0.35))
            self.settings.applyThemeSettings("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
            self.button_dark.configure(fg_color=chosen_color, hover_color=chosen_color)
        return chosen_color
    
    def resetSettings(self) -> None:
        """
        Reset the settings of the application
        """
        cuda = torch.cuda.is_available()
        self.settings.resetDefaultTheme("./Assets/Themes/MISST.json", "./Assets/Themes/maluableJSON")
        self.settings.setSetting("rpc", "true")
        self.settings.setSetting("autoplay", "true")
        self.settings.setSetting("accelerate_on_gpu", "true" if cuda else "false")
        self.rpc_box.select()
        self.autoplay_box.select()
        self.preprocess_method_box.select() if cuda else self.preprocess_method_box.deselect()
        self.button_light.configure(fg_color=self.settings.getSetting("defaultLightColor"), hover_color=self.settings.getSetting("defaultLightColor"))
        self.button_dark.configure(fg_color=self.settings.getSetting("defaultDarkColor"), hover_color=self.settings.getSetting("defaultDarkColor"))
        self.model_select.set("htdemucs")
        self.settings.setSetting("chosen_model", "htdemucs")
        self.change_model(self.model_select.get())

    def autoplay_event(self) -> None:
        """
        Event for when the autoplay box is checked
        """
        if self.autoplay_box.get() == 1:
            self.settings.setSetting("autoplay", "true")
        else:
            self.settings.setSetting("autoplay", "false")

    def rpc_event(self) -> None:
        """
        Event for when the rpc box is checked
        """
        if self.rpc_box.get() == 1:
            self.settings.setSetting("rpc", "true")
        else:
            self.settings.setSetting("rpc", "false")

    def accelerate_event(self) -> None:
        """
        Event for when the accelerate box is checked
        """
        if self.preprocess_method_box.get() == 1 and torch.cuda.is_available() == True:
            self.settings.setSetting("accelerate_on_gpu", "true")
        elif self.preprocess_method_box.get() == 1 and torch.cuda.is_available() == False:
            self.preprocess_method_box.deselect()
            self.preprocess_method_box.place(relx=0.39, rely=0.85, anchor=tkinter.CENTER)
            self.preprocess_method_box.configure(text="CUDA Not Available")
            self.settings.setSetting("accelerate_on_gpu", "false")
            time.sleep(1.5)
            self.preprocess_method_box.place(relx=0.38, rely=0.85, anchor=tkinter.CENTER)
            self.preprocess_method_box.configure(text="Accelerate on GPU?")
        else:
            self.settings.setSetting("accelerate_on_gpu", "false")

    def clearDownloads(self) -> None:
        """
        Clear the downloads folder
        """
        self.confirmation_frame = customtkinter.CTkFrame(
            master=self.settings_window, width=350, height=350, corner_radius=0
        )
        self.confirmation_frame.place(relx=0.25, rely=0.5, anchor=tkinter.CENTER)

        self.confirmation_header = customtkinter.CTkLabel(
            master=self.confirmation_frame, text="Are you sure?", font=(self.FONT, -16)
        )
        self.confirmation_header.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)
        self.confirmation_yes = customtkinter.CTkButton(
            master=self.confirmation_frame,
            text="Yes",
            font=(self.FONT, -12),
            command=lambda: clear(),
            width=80,
        )
        self.confirmation_yes.place(relx=0.35, rely=0.55, anchor=tkinter.CENTER)
        self.confirmation_no = customtkinter.CTkButton(
            master=self.confirmation_frame,
            text="No",
            font=(self.FONT, -12),
            command=lambda: self.confirmation_frame.destroy(),
            width=80,
        )
        self.confirmation_no.place(relx=0.65, rely=0.55, anchor=tkinter.CENTER)
        def clear():
            try:
                shutil.rmtree(self.importsDest)
                os.mkdir(self.importsDest)
                self.confirmation_frame.destroy()
                bytes = MISSThelpers.getsize(MISSThelpers, self.importsDest)
                gb = bytes / 1000000000
                gb = round(gb, 2)
                text = str(gb) + " GB"
                self.downloads_info.configure(text=text)
            except:
                pass

    def change_location(self) -> None:
        """
        Change the location of the downloads folder
        """
        try:
            importsdest_nocheck = tkinter.filedialog.askdirectory(
                initialdir=os.path.abspath(self.importsDest)
            )
            importsdest_nocheck = importsdest_nocheck.replace("\\", "/")
            if importsdest_nocheck != "" and os.path.isdir(
                os.path.abspath(importsdest_nocheck)
            ):
                dummypath = os.path.join(importsdest_nocheck, str(uuid.uuid4()))
                try:
                    with open(dummypath, "w"):
                        pass
                    os.remove(dummypath)
                    importsdest = importsdest_nocheck
                except IOError:
                    importsdest = os.path.abspath(importsdest)
                self.settings.setSetting("importsDest", importsdest)
                self.importsDest = importsdest
                dir = os.path.abspath(self.importsDest)
                dirlen = len(dir)
                n = 20
                location_text = dir if dirlen <= n else "..." + dir[-(n - dirlen) :]
                self.storage_location_info.configure(text=location_text)
                return None
            else:
                self.importsDest = os.path.abspath(self.importsDest)
                return None
        except Exception as e:
            print(e)
            self.importsDest = os.path.abspath(self.importsDest)
            return None

    def loading_label(label:customtkinter.CTkLabel, text:str, og_text:str = "") -> None:
        """
        Loading animation for the settings window

        Args:
            label (tkinter.Label): The label to animate
            text (str): The text to append to the label
            og_text (str, optional): The original text of the label. Defaults to "".
        """
        t = 0
        try:
            while True:
                time.sleep(0.5)
                if label.cget("text") == "":
                    break
                if t > 3:
                    t -= t
                periods = ["", ".", "..", "..."]
                label.configure(text=f"{og_text}{text}{periods[t]}")
                t += 1
        except:
            pass
        return
    
    def GenerateSystemInfo(self) -> str:
        """
        Generate system info for the settings window
        """
        info = ""
        info += "Python version:\t%s\n" % sys.version
        info += "System:\t%s\n" % platform.platform()
        info += "CPU:\t%s\n" % platform.processor()
        info += "Memory:\t%.3fMB\n" % (psutil.virtual_memory().total / 1048576)
        info += "PyTorch version:\t%s\n" % torch.__version__
        info += "CUDA available:\t%s\n" % torch.cuda.is_available()
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                info += "CUDA %d:\t%s\n" % (i, re.findall("\\((.*)\\)", str(torch.cuda.get_device_properties(i)))[0])
        info += "Demucs version:\t%s\n" % demucs.__version__
        info += "FFMpeg available:\t%s\n" % self.FFMpegAvailable
        info += "MISST version:\t%s\n" % self.version
        return info
    
    def freeimage_upload(self, img:str) -> str:
        """
        Upload an image to freeimage.host

        Args:
            img (str): The path to the image
        """
        key = "6d207e02198a847aa98d0a2a901485a5"

        response = requests.post(
            url="https://freeimage.host/api/1/upload",
            data={"key": key},
            files={"source": img},
        )
        if not response.ok:
            raise Exception("Error uploading image", response.json())

        return response.json()["image"]["url"]
    
    def terminate_thread(self, thread:threading.Thread) -> None:
        """
        Terminate a thread

        Args:
            thread (threading.Thread): The thread to terminate
        """
        if not thread.is_alive():
            return

        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")