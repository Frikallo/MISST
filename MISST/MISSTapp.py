import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import base64
import datetime
import io
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tkinter
import traceback
import webbrowser

import customtkinter
import GPUtil
import music_tag
import psutil
from __version__ import __version__ as version
from lyrics_extractor import SongLyrics
from MISSThelpers import MISSTconsole, MISSThelpers
from MISSTlogger import MISSTlogger
from MISSTplayer import MISSTplayer
from MISSTpreprocess import MISSTpreprocess
from MISSTsettings import MISSTconfig, MISSTsettings
from MISSTSetup import MISSTSetup
# from MISSTupdate import MISSTupdater (commented out for now)
from PIL import Image
from pypresence import Presence

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("./Assets/Themes/MISST.json")  # Themes: "blue" (standard), "green", "dark-blue"

class MISSTapp(customtkinter.CTk):
    """
    The main MISST application.
    """
    def __init__(self) -> None:
        """
        Initialize the MISST application.
        """
        super().__init__()

        self.player = MISSTplayer([
             "Assets/silent/silence.flac",
             "Assets/silent/silence.flac",
             "Assets/silent/silence.flac",
             "Assets/silent/silence.flac"
             ], 
             [0]*4
        )
        self.logger = MISSTlogger().logger 
        self.settings = MISSTsettings()
        self.preprocess = MISSTpreprocess()

        self.rpc = self.settings.getSetting("rpc")
        self.discord_client_id = self.settings.getSetting("discord_client_id")

        if self.rpc == "true":
            try:
                self.RPC = Presence(self.discord_client_id)
                self.RPC.connect()
                self.RPC_CONNECTED = True
            except:
                self.logger.error(traceback.format_exc())
                self.logger.error("RPC connection failed or aborted.")
                self.RPC_CONNECTED = False
        else:
            self.RPC_CONNECTED = False

        tokens = [self.settings.getSetting("cse_api_key"), self.settings.getSetting("cse_id")]
        self.lyric_engine = SongLyrics(tokens[0],tokens[1])

        self.importsDest = os.path.abspath(self.settings.getSetting("importsDest"))
        if not os.path.isdir(self.importsDest):
            os.mkdir(self.importsDest)

        self.FFMpegAvailable = True if shutil.which("ffmpeg") != None else False
        self.version = version

        for line in MISSThelpers.GenerateSystemInfo(self).split("\n"):
            if line != "":
                self.logger.info(line)

        self.playing = False
        self.current_song = ""

        # configure window
        self.title("MISST")
        self.iconbitmap(r"./Assets/icon.ico")
        self.WIDTH = 755
        self.HEIGHT = 430
        #self.WIDTH = int(self.winfo_screenwidth() * 0.3932291666666667)
        #self.HEIGHT = int(self.winfo_screenheight() * 0.3981481481481481)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(self.WIDTH, self.HEIGHT)
        self.maxsize(755, 430)

        #customtkinter.set_widget_scaling(((self.WIDTH / 755) + (self.HEIGHT / 430)) / 2)  # widget dimensions and text size
        #customtkinter.set_window_scaling(((self.WIDTH / 755) + (self.HEIGHT / 430)) / 2)  # window geometry dimensions

        self.check_var1 = tkinter.StringVar(value="on")
        self.check_var2 = tkinter.StringVar(value="on")
        self.check_var3 = tkinter.StringVar(value="on")
        self.check_var4 = tkinter.StringVar(value="on")
        self.nc_var = tkinter.StringVar(value="off")

        self.ImageCache = {
            "empty"        : customtkinter.CTkImage(Image.open(f"./Assets/UIAssets/empty.png"),                                                                                                size=(1,  1)),
            "playing"      : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/player-pause-light.png"),        light_image=Image.open("./Assets/Player/player-pause.png"),        size=(32,32)),
            "paused"       : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/player-play-light.png"),         light_image=Image.open("./Assets/Player/player-play.png"),         size=(32,32)),
            "shuffle"      : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/player-shuffle-light.png"),      light_image=Image.open("./Assets/Player/player-shuffle.png"),      size=(25,25)),
            "loop"         : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/loop-light.png"),                light_image=Image.open("./Assets/Player/loop.png"),                size=(25,25)),
            "loop-off"     : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/loop-off-light.png"),            light_image=Image.open("./Assets/Player/loop-off.png"),            size=(25,25)),
            "skip-forward" : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/player-skip-forward-light.png"), light_image=Image.open("./Assets/Player/player-skip-forward.png"), size=(30,30)),
            "skip-back"    : customtkinter.CTkImage(dark_image=Image.open("./Assets/Player/player-skip-back-light.png"),    light_image=Image.open("./Assets/Player/player-skip-back.png"),    size=(30,30)),
            "settings"     : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/settings-light.png"),          light_image=Image.open("./Assets/UIAssets/settings.png"),          size=(25,25)),
            "equalizer"    : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/equalizer-light.png"),         light_image=Image.open("./Assets/UIAssets/equalizer.png"),         size=(25,25)),
            "github"       : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/code-light.png"),              light_image=Image.open("./Assets/UIAssets/code.png"),              size=(25,25)),
            "import"       : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/import-dark.png"),             light_image=Image.open("./Assets/UIAssets/import-light.png"),      size=(30,30)),
            "spotify"      : customtkinter.CTkImage(Image.open("./Assets/Sources/Spotify.png"),                                                                                                size=(40,40)),
            "youtube"      : customtkinter.CTkImage(Image.open("./Assets/Sources/YoutubeMusic.png"),                                                                                           size=(40,40)),
            "applemusic"   : customtkinter.CTkImage(Image.open("./Assets/Sources/AppleMusic.png"),                                                                                             size=(40,40)),
            "soundcloud"   : customtkinter.CTkImage(Image.open("./Assets/Sources/Soundcloud.png"),                                                                                             size=(40,40)),
            "return"       : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/goback_dark.png"),             light_image=Image.open("./Assets/UIAssets/goback.png"),            size=(25,25)),
            "no-cover-art" : customtkinter.CTkImage(dark_image=Image.open("./Assets/UIAssets/default-light.png"),           light_image=Image.open("./Assets/UIAssets/default.png"),           size=(40,40))
        }

        self.loop = False
        self.autoplay = True

        self.FONT = "Roboto Medium"
        self.createWidgets()

        # Check if setup is needed (next version will have a better way of doing this)
        # updater = MISSTupdater(self)
        # try:
        #     updater.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        # except:
        #     pass

        required_files = MISSTSetup.get_model_urls(self, self.settings.getSetting("chosen_model"))
        required_files = [file.split("/")[-1] for file in required_files]
        if not all([os.path.isfile(f"Pretrained/{file}") for file in required_files]):
            self.logger.info("Setup required.")
            self.model_setup_widget = MISSTSetup(self, self.settings.getSetting("chosen_model"))
            self.model_setup_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        else:
            self.logger.info("Setup not required.")

        def on_closing():
            self.destroy()
            self.quit()
            self.player.stop()
            current_pid = psutil.Process().pid
            
            # Terminate child processes
            process = psutil.Process(current_pid)
            children = process.children(recursive=True)
            self.logger.info(f"Terminating {len(children)} child processes.")
            for child in children:
                child.terminate()
            
            # Terminate the current process
            self.logger.info("MISST closed.")
            os.kill(current_pid, signal.SIGTERM)
            sys.exit()

        self.protocol("WM_DELETE_WINDOW", on_closing)

    def createWidgets(self) -> None:
        """
        Creates the widgets for the main window.
        """
        self.west_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (175 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT), corner_radius=0)
        self.west_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), rowspan=4)

        self.north_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.north_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(5, 0))

        self.center_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (200 / self.HEIGHT), corner_radius=8)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.south_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (350 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.south_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=(0, 5))       

        self.interface_frame = customtkinter.CTkFrame(master=self, width=self.WIDTH * (195 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.interface_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=(5, 0))
        
        self.east_frame = customtkinter.CTkTabview(master=self, width=self.WIDTH * (195 / self.WIDTH), height=self.HEIGHT * (100 / self.HEIGHT), corner_radius=8)
        self.east_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 0), pady=(0, 5), rowspan=3)
        self.east_frame.add("Imported")
        self.east_frame.add("Export")
        self.east_frame.tab("Imported").grid_columnconfigure(0, weight=1)
        self.east_frame.tab("Export").grid_columnconfigure(0, weight=1)

        # Interface Frame
        self.shuffle_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=self.ImageCache["shuffle"],
            command=lambda: self.shuffle(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8
        )

        self.loop_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=self.ImageCache["loop-off"],
            command=lambda: self.loopEvent(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8
        )

        self.next_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=self.ImageCache["skip-forward"],
            command=lambda: print("test"),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.previous_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=self.ImageCache["skip-back"],
            command=lambda: print("test"),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.playpause_button = customtkinter.CTkButton(
            master=self.interface_frame,
            image=self.ImageCache["paused"],
            command=lambda: self.playpause(),
            text="",
            width=5,
            height=5,
            fg_color='transparent',
            hover_color=self.interface_frame.cget("bg_color"),
            corner_radius=8,
            state=tkinter.DISABLED
        )

        self.next_button.place(relx=0.67, rely=0.5, anchor=tkinter.CENTER)
        self.previous_button.place(relx=0.33, rely=0.5, anchor=tkinter.CENTER)
        self.shuffle_button.place(relx=0.16, rely=0.5, anchor=tkinter.CENTER)
        self.loop_button.place(relx=0.84, rely=0.5, anchor=tkinter.CENTER)
        self.playpause_button.place(relx=0.50, rely=0.5, anchor=tkinter.CENTER)

        ## EAST FRAME -------------  ---------------------------------------------------------------------------------------
        # Imported Tab
        self.search_entry = customtkinter.CTkEntry(
            master=self.east_frame.tab("Imported"),
            width=150,
            height=25,
            placeholder_text="Search for audio",
        )
        self.search_entry.place(relx=0.5, rely=0.05, anchor=tkinter.CENTER)

        self.listframe = customtkinter.CTkFrame(
            master=self.east_frame.tab("Imported"), width=150, height=175, corner_radius=8
        )
        self.listframe.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)

        self.songs_box = customtkinter.CTkTextbox(
            master=self.listframe,
            width=140,
            height=175,
            bg_color='transparent',
            fg_color='transparent',
            corner_radius=8,
        )
        self.songs_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.index_entry = customtkinter.CTkEntry(
            master=self.east_frame.tab("Imported"),
            width=150,
            height=25,
            placeholder_text="Enter index of audio",
        )
        self.index_entry.place(relx=0.5, rely=0.85, anchor=tkinter.CENTER)

        self.playbutton = customtkinter.CTkButton(
            master=self.east_frame.tab("Imported"),
            text="Play",
            width=150,
            height=25,
            command=lambda: self.play_search(self.index_entry.get(), MISSThelpers.MISSTlistdir(self, self.importsDest)),
        )
        self.playbutton.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)

        importsBoxUpdates = threading.Thread(target=self.imports_check, args=(self.search_entry, self.songs_box))
        importsBoxUpdates.daemon = True
        importsBoxUpdates.start()
        # Export Tab
        self.export_components = {
            "Bass": (None, None),
            "Other": (None, None),
            "Drums": (None, None),
            "Vocals": (None, None)
        }
        def activate(button, slider):
            button_text = button.cget("text")
            if button_text == "Bass":
                sound = 0
                self.slider1.set(0.5) if button.cget("border_color") == "#3E454A" else self.slider1.set(0)
                self.checkbox1.select() if button.cget("border_color") == "#3E454A" else self.checkbox1.deselect()
            
            elif button_text == "Drums":
                sound = 1
                self.slider2.set(0.5) if button.cget("border_color") == "#3E454A" else self.slider2.set(0)
                self.checkbox2.select() if button.cget("border_color") == "#3E454A" else self.checkbox2.deselect()

            elif button_text == "Other":
                sound = 2
                self.slider3.set(0.5) if button.cget("border_color") == "#3E454A" else self.slider3.set(0)
                self.checkbox3.select() if button.cget("border_color") == "#3E454A" else self.checkbox3.deselect()

            elif button_text == "Vocals":
                sound = 3
                self.slider4.set(0.5) if button.cget("border_color") == "#3E454A" else self.slider4.set(0)
                self.checkbox4.select() if button.cget("border_color") == "#3E454A" else self.checkbox4.deselect()

            if button.cget("border_color") == "#3E454A":
                button.configure(border_color=self.settings.getSetting("chosenLightColor") if customtkinter.get_appearance_mode() == "Light" else self.settings.getSetting("chosenDarkColor"))
                slider.set(0.5)
            else:
                button.configure(border_color="#3E454A")
                slider.set(0)

            self.player.set_volume(sound, slider.get())

        def slider_event(slider, button):
            button_text = button.cget("text")
            if button_text == "Bass":
                sound = 0
                self.slider1.set(self.export_components["Bass"][0].get())
                self.checkbox1.select() if self.export_components["Bass"][0].get() != 0 else self.checkbox1.deselect()
            
            elif button_text == "Drums":
                sound = 1
                self.slider2.set(self.export_components["Drums"][0].get())
                self.checkbox2.select() if self.export_components["Drums"][0].get() != 0 else self.checkbox2.deselect()

            elif button_text == "Other":
                sound = 2
                self.slider3.set(self.export_components["Other"][0].get())
                self.checkbox3.select() if self.export_components["Other"][0].get() != 0 else self.checkbox3.deselect()

            elif button_text == "Vocals":
                sound = 3
                self.slider4.set(self.export_components["Vocals"][0].get())
                self.checkbox4.select() if self.export_components["Vocals"][0].get() != 0 else self.checkbox4.deselect()

            self.player.set_volume(sound, slider)
            if slider == 0:
                button.configure(border_color="#3E454A")
            else:
                button.configure(border_color=self.settings.getSetting("chosenLightColor") if customtkinter.get_appearance_mode() == "Light" else self.settings.getSetting("chosenDarkColor"))

        widgets = ["Bass", "Other", "Drums", "Vocals"]
        sliders = []
        i = 0
        for widget in widgets:
            activate_button = customtkinter.CTkButton(
                master=self.east_frame.tab("Export"),
                text=widget,
                width=70,
                height=70,
                border_width=2,
                border_color=self.settings.getSetting("chosenLightColor") if customtkinter.get_appearance_mode() == "Light" else self.settings.getSetting("chosenDarkColor"),
                bg_color='transparent',
                fg_color='transparent',
                hover_color=self.east_frame.cget("bg_color"),
            )
            factor = 0.25 if i < 2 else 0.75
            activate_button.place(
                relx=factor, rely=0.25 if i % 2 == 0 else 0.6, anchor=tkinter.CENTER
            )
            volume_slider = customtkinter.CTkSlider(
                master=self.east_frame.tab("Export"),
                width=70,
                height=10,
                number_of_steps=10
            )
            sliders.append(volume_slider)
            volume_slider.place(
                relx=factor, rely=0.42 if i % 2 == 0 else 0.77, anchor=tkinter.CENTER
            )
            activate_button.configure(
                command=lambda button=activate_button, slider=volume_slider: activate(button, slider)
            )
            volume_slider.configure(
                command=lambda slider=volume_slider, button=activate_button: slider_event(slider, button)
            )
            i += 1
            self.export_components[activate_button.cget("text")] = volume_slider, activate_button
        self.export_button = customtkinter.CTkButton(
            master=self.east_frame.tab("Export"),
            text="Export",
            width=150,
            height=25,
            command=lambda: threading.Thread(target=self.export, args=(self.current_song, sliders), daemon=True).start()
        )
        self.export_button.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)
        ## WEST FRAME ----------------------------------------------------------------------------------------------------

        self.logolabel = customtkinter.CTkLabel(
            master=self.west_frame, text=f"MISST {version}", font=(self.FONT, -16)
        )
        self.logolabel.place(relx=0.5, rely=0.12, anchor=tkinter.CENTER)

        self.themelabel = customtkinter.CTkLabel(master=self.west_frame, text="Appearance Mode:")
        self.themelabel.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

        self.thememenu = customtkinter.CTkOptionMenu(
            master=self.west_frame,
            values=["System", "Dark", "Light"],
            command=lambda x: MISSThelpers.change_theme(x)
        )
        self.thememenu.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        self.settings_button = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=self.ImageCache["settings"],
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            command=lambda: self.draw_settings_frame(),
        )
        self.settings_button.place(relx=0.3, rely=0.9, anchor=tkinter.CENTER)

        self.equalizer = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=self.ImageCache["equalizer"],
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            corner_radius=16,
            command=lambda: self.draw_effects_frame(),
        )
        self.equalizer.place(relx=0.7, rely=0.9, anchor=tkinter.CENTER)

        self.github_button = customtkinter.CTkButton(
            master=self.west_frame,
            font=(self.FONT, -12),
            text="",
            image=self.ImageCache["github"],
            bg_color='transparent',
            fg_color='transparent',
            hover_color=self.west_frame.cget("bg_color"),
            width=5,
            height=5,
            command=lambda: webbrowser.open("https://github.com/Frikallo/MISST", new=2),
        )
        self.github_button.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

        ## NORTH FRAME ----------------------------------------------------------------------------------------------------

        self.songlabel = customtkinter.CTkButton(
            master=self.north_frame,
            text=f"Play Something!",
            width=240,
            height=50,
            font=(self.FONT, -14),
            command=lambda: self.draw_lyrics_box(),
            fg_color='transparent',
            hover_color=self.north_frame.cget("bg_color"),
            text_color=self.logolabel.cget("text_color"),
            image = self.ImageCache["empty"],
        )
        self.songlabel.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

        self.progressbar = customtkinter.CTkSlider(master=self.north_frame, width=225, height=15, from_=0, to=100, number_of_steps=100, command=lambda x: self.slider_event(x), state=tkinter.DISABLED)
        self.progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
        self.progressbar.set(0)

        self.progress_label_left = customtkinter.CTkLabel(
            master=self.north_frame, text="0:00", font=(self.FONT, -12), width=5
        )
        self.progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

        self.progress_label_right = customtkinter.CTkLabel(
            master=self.north_frame, text="0:00", font=(self.FONT, -12), width=5
        )
        self.progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

        ## CENTER FRAME ----------------------------------------------------------------------------------------------------

        self.checkbox1 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="Bass",
            command=lambda: MISSThelpers.checkbox_event(self.check_var1, self.export_components["Bass"], 0, self.player, self.slider1),
            variable=self.check_var1,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox1.place(relx=0.1, rely=0.2, anchor=tkinter.W)

        self.checkbox2 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="Drums",
            command=lambda: MISSThelpers.checkbox_event(self.check_var2, self.export_components["Drums"], 1, self.player, self.slider2),
            variable=self.check_var2,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox2.place(relx=0.1, rely=0.35, anchor=tkinter.W)

        self.checkbox3 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="Other",
            command=lambda: MISSThelpers.checkbox_event(self.check_var3, self.export_components["Other"], 2, self.player, self.slider3),
            variable=self.check_var3,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox3.place(relx=0.1, rely=0.5, anchor=tkinter.W)

        self.checkbox4 = customtkinter.CTkCheckBox(
            master=self.center_frame,
            text="Vocals",
            command=lambda: MISSThelpers.checkbox_event(self.check_var4, self.export_components["Vocals"], 3, self.player, self.slider4),
            variable=self.check_var4,
            onvalue="on",
            offvalue="off",
        )
        self.checkbox4.place(relx=0.1, rely=0.65, anchor=tkinter.W)

        self.slider1 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x, self.export_components["Bass"], 0, self.player, self.check_var1),
            number_of_steps=10,
        )
        self.slider1.place(relx=0.6, rely=0.2, anchor=tkinter.CENTER)

        self.slider2 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x, self.export_components["Drums"], 1, self.player, self.check_var2),
            number_of_steps=10,
        )
        self.slider2.place(relx=0.6, rely=0.35, anchor=tkinter.CENTER)

        self.slider3 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x, self.export_components["Other"], 2, self.player, self.check_var3),
            number_of_steps=10,
        )
        self.slider3.place(relx=0.6, rely=0.5, anchor=tkinter.CENTER)

        self.slider4 = customtkinter.CTkSlider(
            master=self.center_frame,
            from_=0,
            to=1,
            command=lambda x: MISSThelpers.slider_event(x, self.export_components["Vocals"], 3, self.player, self.check_var4),
            number_of_steps=10,
        )
        self.slider4.place(relx=0.6, rely=0.65, anchor=tkinter.CENTER)

        self.effects_checkbox = customtkinter.CTkSwitch(
            master=self.center_frame,
            text="Effects",
            command=self.effects,
            variable=self.nc_var,
            onvalue="on",
            offvalue="off",
            fg_color=None
        )
        self.effects_checkbox.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
        self.effects_checkbox.configure(state=tkinter.DISABLED)

        self.effects_button = customtkinter.CTkButton(
            master=self.center_frame,
            text="Effects",
            font=(self.FONT, -12, "underline"),
            command=self.draw_effects_frame,
            fg_color=self.center_frame.cget("fg_color"),
            hover_color=self.center_frame.cget("bg_color"),
            width=25,
            height=25,
        )
        self.effects_button.place(relx=0.53, rely=0.9, anchor=tkinter.CENTER)
        self.effects_button.configure(state=tkinter.DISABLED)

        ## SOUTH FRAME ----------------------------------------------------------------------------------------------------

        self.import_button = customtkinter.CTkButton(
            master=self.south_frame,
            command=lambda: self.imports_toggle(),
            image=self.ImageCache["import"],
            fg_color='transparent',
            hover_color=self.south_frame.cget("bg_color"),
            text="Import Song(s)",
            font=(self.FONT, -14),
            width=240,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)        

    def raise_above_all(self, window:customtkinter.CTkToplevel) -> None:
        """
        Raises a window above all other windows

        Args:
            window (tkinter.Tk): The window to raise
        """
        window.attributes("-topmost", 1)
        window.attributes("-topmost", 0)

    def draw_lyrics_box(self) -> None:
        """
        Draws the lyrics box
        """
        try:
            self.lyrics_window.destroy() # Destroy the window if it already exists
        except:
            pass

        self.lyrics_window = customtkinter.CTkToplevel(app)
        self.lyrics_window.geometry("580x435")
        self.lyrics_window.title("Lyrics")
        self.lyrics_window.after(201, lambda: self.lyrics_window.wm_iconbitmap(r"Assets/icon.ico")) # Weird bug where icon doesn't load unless it's done after 200ms
        self.lyrics_window.minsize(580, 435)
        self.lyrics_window.maxsize(580, 435)
        self.raise_above_all(self.lyrics_window)

        search_term = self.songlabel.cget("text")
        if search_term == "Play Something!":
            self.lyrics_window.destroy()
            return
        search_term = self.current_song

        self.lyrics_box = customtkinter.CTkTextbox(
            master=self.lyrics_window,
            font=(self.FONT, -14),
            width=500,
            height=375,
            bg_color=self.lyrics_window.cget("fg_color"),
            fg_color=self.lyrics_window.cget("fg_color"),
            state=tkinter.DISABLED,
        )
        self.lyrics_box.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)

        def search(term):
            self.lyrics_box.configure(state=tkinter.NORMAL)
            try:
                lyrics = self.lyric_engine.get_lyrics(term)
                self.lyrics_box.delete("0.0", "end")
                self.lyrics_box.insert(tkinter.END, lyrics['lyrics'])
                config.setConfig(path, "lyrics", lyrics['lyrics'])
            except:
                self.logger.error(traceback.format_exc())
                self.lyrics_box.delete("0.0", "end")
                self.lyrics_box.insert(tkinter.END, "Lyrics not found")
            self.lyrics_box.configure(state=tkinter.DISABLED)

        path = f"{self.importsDest}/{search_term}"
        config = MISSTconfig(path)

        if config.getConfig(path)["lyrics"] == "null":
            search(search_term)
        else:
            self.lyrics_box.configure(state=tkinter.NORMAL)
            self.lyrics_box.delete("0.0", "end")
            self.lyrics_box.insert(tkinter.END, config.getConfig(path)["lyrics"])
            self.lyrics_box.configure(state=tkinter.DISABLED)

        self.lyric_entry = customtkinter.CTkEntry(
            master=self.lyrics_window,
            font=(self.FONT, -14),
            width=375,
            height=15,
            placeholder_text="Not the right lyrics? Click here to search for them!",
        )
        self.lyric_entry.place(relx=0.4, rely=0.92, anchor=tkinter.CENTER)

        self.search_button = customtkinter.CTkButton(
            master=self.lyrics_window,
            command=lambda: search(self.lyric_entry.get()),
            text="Search",
            font=(self.FONT, -14),
            width=100,
            height=15,
        )
        self.search_button.place(relx=0.84, rely=0.92, anchor=tkinter.CENTER)

    def imports_checkbox_event(self, current_var:tkinter.StringVar) -> None:
        """
        Called when an import checkbox is clicked

        Args:
            current_var (tkinter.StringVar): The variable of the checkbox that was clicked
        """
        vars = [self.import_Spotify_var, self.import_Youtube_var, self.import_AppleMusic_var, self.import_Soundcloud_var]
        checkboxes = [self.import_Spotify_checkbox, self.import_Youtube_checkbox, self.import_AppleMusic_checkbox, self.import_Soundcloud_checkbox]
        for var in vars:
            if var.get() == "on":
                var.set("off")
                checkboxes[vars.index(var)].deselect()
        current_var.set("on")
        checkboxes[vars.index(current_var)].select()

    def imports_toggle(self) -> None:
        """
        Toggles the imports frame
        """
        try:
            self.imports_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        except:
            self.draw_imports_frame()

    def draw_imports_frame(self) -> None:
        """
        Draws the imports frame
        """
        self.imports_frame = customtkinter.CTkFrame(
            master=self, width=self.WIDTH * (755 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT)
        )
        self.imports_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.left_frame = customtkinter.CTkFrame(
            master=self.imports_frame, width=350, height=380
        )
        self.left_frame.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)

        self.right_frame = customtkinter.CTkFrame(
            master=self.imports_frame, width=350, height=380
        )
        self.right_frame.place(relx=0.75, rely=0.47, anchor=tkinter.CENTER)

        self.import_title = customtkinter.CTkLabel(
            master=self.left_frame,
            text="Choose a source",
            font=(self.FONT, -20),
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_title.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.import_Spotify_var = tkinter.StringVar()   
        self.import_Youtube_var = tkinter.StringVar()
        self.import_AppleMusic_var = tkinter.StringVar()
        self.import_Soundcloud_var = tkinter.StringVar()

        self.import_Spotify_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=self.ImageCache["spotify"],
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Spotify_button.place(relx=0.3, rely=0.2375, anchor=tkinter.CENTER)

        self.import_Spotify_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Spotify_var),
            variable=self.import_Spotify_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Spotify_checkbox.place(relx=0.61, rely=0.2375, anchor=tkinter.CENTER)


        self.import_Youtube_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=self.ImageCache["youtube"],
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Youtube_button.place(relx=0.3, rely=0.3750, anchor=tkinter.CENTER)

        self.import_Youtube_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Youtube_var),
            variable=self.import_Youtube_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Youtube_checkbox.place(relx=0.61, rely=0.3750, anchor=tkinter.CENTER)

        self.import_Deezer_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=self.ImageCache["applemusic"],
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Deezer_button.place(relx=0.3, rely=0.5125, anchor=tkinter.CENTER)

        self.import_AppleMusic_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_AppleMusic_var),
            variable=self.import_AppleMusic_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_AppleMusic_checkbox.place(relx=0.61, rely=0.5125, anchor=tkinter.CENTER)

        self.import_Soundcloud_button = customtkinter.CTkLabel(
            master=self.left_frame,
            image=self.ImageCache["soundcloud"],
            fg_color='transparent',
            text="",
            font=(self.FONT, -14),
            width=50,
            height=50,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_Soundcloud_button.place(relx=0.3, rely=0.6500, anchor=tkinter.CENTER)

        self.import_Soundcloud_checkbox = customtkinter.CTkCheckBox(
            master=self.left_frame,
            text="",
            command=lambda: self.imports_checkbox_event(self.import_Soundcloud_var),
            variable=self.import_Soundcloud_var,
            onvalue="on",
            offvalue="off",
        )
        self.import_Soundcloud_checkbox.place(relx=0.61, rely=0.6500, anchor=tkinter.CENTER)

        self.source_entry = customtkinter.CTkEntry(
            master=self.left_frame,
            width=200,
            text_color=self.logolabel.cget("text_color"),
            placeholder_text="Enter your share URL here",
        )
        self.source_entry.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        self.import_button = customtkinter.CTkButton(
            master=self.left_frame,
            command=lambda: threading.Thread(target=self.sourcePreprocess, args=(self.source_entry.get(),), daemon=True).start(),
            text="Import",
            font=(self.FONT, -14),
            width=75,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_button.place(relx=0.32, rely=0.9, anchor=tkinter.CENTER)

        self.or_label = customtkinter.CTkLabel(
            master=self.left_frame,
            text="OR",
            font=(self.FONT, -14),
            text_color=self.logolabel.cget("text_color"),
        )
        self.or_label.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

        self.import_file_button = customtkinter.CTkButton(
            master=self.left_frame,
            command=lambda: threading.Thread(target=self.filePreprocess, daemon=True).start(),
            text="From File",
            font=(self.FONT, -14),
            width=75,
            text_color=self.logolabel.cget("text_color"),
        )
        self.import_file_button.place(relx=0.68, rely=0.9, anchor=tkinter.CENTER)

        self.preprocess_status_label = customtkinter.CTkLabel(
            master=self.right_frame,
            text="Preprocess Status",
            font=(self.FONT, -20),
            text_color=self.logolabel.cget("text_color"),
        )
        self.preprocess_status_label.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.preprocess_terminal = customtkinter.CTkFrame(
            master=self.right_frame,
            width=275,
            height=290,
            fg_color="#0C0C0C",
            border_width=1,
        )
        self.preprocess_terminal.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

        self.preprocess_terminal_text = customtkinter.CTkTextbox(
            master=self.preprocess_terminal,
            font=(self.FONT, -14),
            width=250,
            height=250,
            bg_color="transparent",
            fg_color="transparent",
            text_color="#CCCCCC",
        )
        self.preprocess_terminal_text.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        def get_usage_info():
            while True:
                cpu_usage = psutil.cpu_percent()
                mem_usage = psutil.virtual_memory().percent
                try:
                    gpu_usage = GPUtil.getGPUs()[0].load * 100
                except:
                    gpu_usage = "N/A" #CPU version of MISST
                self.system_info.configure(
                    text=f"CPU: {cpu_usage:.1f}% | Mem: {mem_usage:.1f}% | GPU: {f'{gpu_usage:.1f}' if gpu_usage != 'N/A' else 'N/A'}%"
                )
                time.sleep(1)
        threading.Thread(target=get_usage_info, daemon=True).start()

        self.system_info = customtkinter.CTkLabel(
            master=self.imports_frame,
            text=f"CPU: 00.0% | Mem: 00.0% | GPU: 00.0%",
            font=(self.FONT, -12),
            text_color=self.logolabel.cget("text_color"),
            state=tkinter.DISABLED,
        )
        self.system_info.place(relx=0.76, rely=0.95, anchor=tkinter.CENTER)

        self.return_button = customtkinter.CTkButton(
            master=self.imports_frame,
            command=lambda: self.imports_frame.place_forget(),
            image=self.ImageCache["return"],
            fg_color='transparent',
            hover_color=self.imports_frame.cget("bg_color"),
            text="Return",
            font=(self.FONT, -12),
            width=5,
            text_color="#6D6D6D",
        )
        self.return_button.place(relx=0.24, rely=0.95, anchor=tkinter.CENTER)

        self.console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        self.console.update("\nMISST> waiting")

    def retrieve_metadata(self, save_dir:str = None, temp_dir:str = None, file:str = None) -> None:
        """
        Retrieves metadata from a file and saves it to a directory.

        Args:
            save_dir (str): The directory to save the metadata to.
            temp_dir (str): The directory to retrieve the metadata from.
            file (str): The file to retrieve the metadata from.
        """
        self.console.update("\nMISST> Getting Metadata")
        if temp_dir is not None:
            save_dir = f"{self.importsDest}/{os.path.splitext(os.path.basename(os.listdir(temp_dir)[0]))[0]}"
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            file = f"{temp_dir}/{os.listdir(temp_dir)[0]}"
        else:
            file = file
        config = MISSTconfig(save_dir) #Create config file
        try:
            f = music_tag.load_file(file)
            art = f['artwork']
            raw_art = art.first.data
            image = Image.open(io.BytesIO(raw_art))

            square_size = min(image.size)
            left = (image.width - square_size) // 2
            top = (image.height - square_size) // 2
            right = left + square_size
            bottom = top + square_size

            # Crop the square region from the center of the image
            cropped_image = image.crop((left, top, right, bottom))

            image = cropped_image.resize((40, 40), Image.Resampling.LANCZOS)
            raw_art = image.tobytes()
            png_bytes = io.BytesIO()
            image.save(png_bytes, format="PNG")
            raw_art = png_bytes.getvalue()
            config.setConfig(save_dir, "image_url", MISSThelpers().freeimage_upload(raw_art))
            config.setConfig(save_dir, "image_raw", base64.b64encode(raw_art).decode('utf-8'))
            self.console.endUpdate()
            self.console.addLine("\nMISST> Metadata Retrieved.")
        except:
            self.logger.error(traceback.format_exc())
            self.console.endUpdate()
            self.console.addLine("\nMISST> Error getting metadata.")

    def filePreprocess(self) -> None:
        """
        Preprocesses a file.
        """
        self.console.editLine(f"MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n", 0)
        self.import_file_button.configure(state=tkinter.DISABLED)
        self.import_button.configure(state=tkinter.DISABLED)
        file = tkinter.filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("mp3 files","*.mp3"),("wav files", "*.wav"),("flac files", "*.flac"),("all files","*.*")), multiple=False)
        if file != "":
            self.console.endUpdate()
            save_name = os.path.splitext(os.path.basename(file))[0]
            save_dir = f"{self.importsDest}/{save_name}"
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            self.retrieve_metadata(save_dir=save_dir, file=file)
            thread = threading.Thread(target=MISSTpreprocess.preprocess, args=(self, file, self.importsDest, self.settings.getSetting("chosen_model"), "cuda" if self.settings.getSetting("accelerate_on_gpu") == "true" else "cpu"), daemon=True)
            thread.start()
            thread.join()
            self.import_file_button.configure(state=tkinter.NORMAL)
            self.import_button.configure(state=tkinter.NORMAL)
        else:
            self.import_file_button.configure(state=tkinter.NORMAL)
            self.import_button.configure(state=tkinter.NORMAL)
            
    def sourcePreprocess(self, url:str) -> None:
        """
        Preprocesses a source.

        Args:
            url (str): The URL of the source to preprocess.
        """
        self.console.editLine(f"MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n", 0)
        if url != "":
            # Spotify Import
            if self.import_Spotify_var.get() == "on":
                self.import_file_button.configure(state=tkinter.DISABLED)
                self.import_button.configure(state=tkinter.DISABLED)
                if "https://open.spotify.com/track" not in url:
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Invalid URL.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.update("\nMISST> Downloading")
                temp_dir = tempfile.mkdtemp()
                cmd = [os.path.abspath("./Assets/Bin/spotdl.exe"),
                       f"{url}",
                       "--output",
                       temp_dir,
                       "--ffmpeg",
                       "./ffmpeg.exe"
                       ]
                process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=0x08000000)
                if process.returncode != 0:
                    self.logger.error(process.stderr)
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Error downloading file.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.addLine("\nMISST> Downloaded.")
                self.retrieve_metadata(temp_dir=temp_dir)
                thread = threading.Thread(target=MISSTpreprocess.preprocess, args=(self, f"{temp_dir}/{os.listdir(temp_dir)[0]}", self.importsDest, self.settings.getSetting("chosen_model"), "cuda" if self.settings.getSetting("accelerate_on_gpu") == "true" else "cpu"), daemon=True)
                thread.start()
                thread.join()
                os.remove(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                os.rmdir(temp_dir)
                self.import_file_button.configure(state=tkinter.NORMAL)
                self.import_button.configure(state=tkinter.NORMAL)
                self.source_entry.delete(0, tkinter.END) #Clear entry
            
            # Youtube Import
            elif self.import_Youtube_var.get() == "on":
                self.import_file_button.configure(state=tkinter.DISABLED)
                self.import_button.configure(state=tkinter.DISABLED)
                if "https://music.youtube.com/watch?v=" not in url and "https://www.youtube.com/watch?v=" not in url:
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Invalid URL.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.update("\nMISST> Downloading")
                temp_dir = tempfile.mkdtemp()
                cmd = [os.path.abspath("./Assets/Bin/music-dl.exe"), 
                       "-v", 
                       "-x",
                       "--embed-thumbnail",
                       "--audio-format",
                       "flac",
                       "-o",
                       f"{temp_dir}/%(title)s.%(ext)s",
                       f"{url}",
                       "--ffmpeg-location",
                       "./ffmpeg.exe"
                ] 
                process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=0x08000000)
                if process.returncode != 0:
                    self.logger.error(process.stderr)
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Error downloading file.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.addLine("\nMISST> Downloaded.")
                self.retrieve_metadata(temp_dir=temp_dir)
                thread = threading.Thread(target=MISSTpreprocess.preprocess, args=(self, f"{temp_dir}/{os.listdir(temp_dir)[0]}", self.importsDest, self.settings.getSetting("chosen_model"), "cuda" if self.settings.getSetting("accelerate_on_gpu") == "true" else "cpu"), daemon=True)
                thread.start()
                thread.join()
                os.remove(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                os.rmdir(temp_dir)
                self.import_file_button.configure(state=tkinter.NORMAL)
                self.import_button.configure(state=tkinter.NORMAL)
                self.source_entry.delete(0, tkinter.END) #Clear entry

            # AppleMusic Import
            elif self.import_AppleMusic_var.get() == "on":
                self.import_file_button.configure(state=tkinter.DISABLED)
                self.import_button.configure(state=tkinter.DISABLED)
                if "https://music.apple.com/" not in url:
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Invalid URL.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.update("\nMISST> Downloading")
                temp_dir = tempfile.mkdtemp()
                try:
                    MISSThelpers.apple_music(url, temp_dir) # Download
                except:
                    self.logger.error(traceback.format_exc())
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Error downloading file.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.addLine("\nMISST> Downloaded.")
                self.retrieve_metadata(temp_dir=temp_dir)
                thread = threading.Thread(target=MISSTpreprocess.preprocess, args=(self, f"{temp_dir}/{os.listdir(temp_dir)[0]}", self.importsDest, self.settings.getSetting("chosen_model"), "cuda" if self.settings.getSetting("accelerate_on_gpu") == "true" else "cpu"), daemon=True)
                thread.start()
                thread.join()
                os.remove(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                os.rmdir(temp_dir)
                self.import_file_button.configure(state=tkinter.NORMAL)
                self.import_button.configure(state=tkinter.NORMAL)
                self.source_entry.delete(0, tkinter.END) #Clear entry

            # Soundcloud Import
            elif self.import_Soundcloud_var.get() == "on":
                self.import_file_button.configure(state=tkinter.DISABLED)
                self.import_button.configure(state=tkinter.DISABLED)
                if "https://soundcloud.com" not in url:
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Invalid URL.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.update("\nMISST> Downloading")
                temp_dir = tempfile.mkdtemp()
                cmd = [
                    os.path.abspath("./Assets/Bin/music-dl.exe"),
                    "-v",
                    "-x",
                    "--embed-thumbnail",
                    "--audio-format",
                    "flac",
                    "-o",
                    f"{temp_dir}/%(title)s.%(ext)s",
                    f"{url}",
                    "--ffmpeg-location",
                    "./ffmpeg.exe"
                ]
                process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=0x08000000)
                if process.returncode != 0:
                    self.logger.error(process.stderr)
                    self.console.endUpdate()
                    self.console.addLine("\nMISST> Error downloading file.")
                    self.import_file_button.configure(state=tkinter.NORMAL)
                    self.import_button.configure(state=tkinter.NORMAL)
                    return
                self.console.endUpdate()
                self.console.addLine("\nMISST> Downloaded.")
                self.retrieve_metadata(temp_dir=temp_dir)
                thread = threading.Thread(target=MISSTpreprocess.preprocess, args=(self, f"{temp_dir}/{os.listdir(temp_dir)[0]}", self.importsDest, self.settings.getSetting("chosen_model"), "cuda" if self.settings.getSetting("accelerate_on_gpu") == "true" else "cpu"), daemon=True)
                thread.start()
                thread.join()
                os.remove(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                os.rmdir(temp_dir)
                self.import_file_button.configure(state=tkinter.NORMAL)
                self.import_button.configure(state=tkinter.NORMAL)
                self.source_entry.delete(0, tkinter.END) #Clear entry

            else:
                pass
        else:
            self.console.endUpdate()
            self.console.addLine("\nMISST> Empty URL.")
            self.console.update("\nMISST> waiting")
            return
        return

    def change_model(self, model):
        self.settings.setSetting("chosen_model", model)
        self.setup = MISSTSetup(self, self.settings.getSetting("chosen_model"))
        try:
            self.setup.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        except:
            pass

    def draw_settings_frame(self) -> None:
        """
        Draws the settings frame.
        """
        self.settings_window = customtkinter.CTkFrame(
            master=self, width=self.WIDTH * (755 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT), corner_radius=0
        )
        self.settings_window.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.settings_frame = customtkinter.CTkFrame(
            master=self.settings_window, width=350, height=380, corner_radius=10
        )
        self.settings_frame.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)

        self.setting_header = customtkinter.CTkLabel(
            master=self.settings_frame, text="Settings", font=(self.FONT, -18)
        )
        self.setting_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.general_frame = customtkinter.CTkTabview(master=self.settings_frame, width=300, height=160)
        self.general_frame.place(relx=0.5, rely=0.34, anchor=tkinter.CENTER)

        self.general_frame.add("General")
        self.general_frame.add("Advanced")

        self.general_header = customtkinter.CTkLabel(
            master=self.general_frame.tab("General"), text="General", font=(self.FONT, -16)
        )
        self.general_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

        self.autoplay_box = customtkinter.CTkSwitch(
            master=self.general_frame.tab("General"),
            text="Autoplay",
            font=(self.FONT, -12),
            command=lambda: MISSThelpers.autoplay_event(self),
            width=50,
        )
        self.autoplay_box.place(relx=0.28, rely=0.4, anchor=tkinter.CENTER)
        if self.settings.getSetting('autoplay') == 'true':
            self.autoplay_box.select()

        self.rpc_box = customtkinter.CTkSwitch(
            master=self.general_frame.tab("General"),
            text="Discord RPC",
            font=(self.FONT, -12),
            command=lambda: MISSThelpers.rpc_event(self),
            width=50,
        )
        self.rpc_box.place(relx=0.31, rely=0.625, anchor=tkinter.CENTER)
        if self.settings.getSetting('rpc') == 'true':
            self.rpc_box.select()

        self.preprocess_method_box = customtkinter.CTkSwitch(
            master=self.general_frame.tab("General"),
            text="Accelerate on GPU?",
            font=(self.FONT, -12),
            command=lambda: threading.Thread(target=MISSThelpers.accelerate_event, args=(self,), daemon=True).start(),
            width=50,
        )
        self.preprocess_method_box.place(relx=0.38, rely=0.85, anchor=tkinter.CENTER)
        if self.settings.getSetting('accelerate_on_gpu') == 'true':
            self.preprocess_method_box.select()

        ### General Settings ###

        self.storage_frame = customtkinter.CTkFrame(master=self.settings_frame, width=300, height=140)
        self.storage_frame.place(relx=0.5, rely=0.76, anchor=tkinter.CENTER)

        self.storage_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Storage", font=(self.FONT, -16)
        )
        self.storage_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

        self.downloads_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Downloads:", font=(self.FONT, -12, "bold")
        )
        self.downloads_header.place(relx=0.24, rely=0.4, anchor=tkinter.CENTER)

        bytes = MISSThelpers.getsize(MISSThelpers, self.importsDest)
        gb = bytes / 1000000000
        gb = round(gb, 2)

        text = str(gb) + " GB"

        self.downloads_info = customtkinter.CTkLabel(
            master=self.storage_frame,
            text=text,
            font=(self.FONT, -12),
            width=25,
            state=tkinter.DISABLED,
        )
        self.downloads_info.place(relx=0.46, rely=0.4, anchor=tkinter.CENTER)

        self.downloads_subheader = customtkinter.CTkLabel(
            master=self.storage_frame,
            text="Downloaded Content",
            font=(self.FONT, -11),
            state=tkinter.DISABLED,
        )
        self.downloads_subheader.place(relx=0.29, rely=0.55, anchor=tkinter.CENTER)

        self.clear_downloads_button = customtkinter.CTkButton(
            master=self.storage_frame,
            text="Clear Downloads",
            font=(self.FONT, -12),
            width=15,
            height=2,
            command=lambda: MISSThelpers.clearDownloads(self)
        )
        self.clear_downloads_button.place(relx=0.75, rely=0.475, anchor=tkinter.CENTER)

        self.storage_location_header = customtkinter.CTkLabel(
            master=self.storage_frame, text="Storage Location:", font=(self.FONT, -12, "bold")
        )
        self.storage_location_header.place(relx=0.305, rely=0.7, anchor=tkinter.CENTER)

        dir = os.path.abspath(self.importsDest)
        dirlen = len(dir)
        n = 20
        location_text = dir if dirlen <= n else "..." + dir[-(n - dirlen) :]

        self.storage_location_info = customtkinter.CTkLabel(
            master=self.storage_frame,
            text=location_text,
            font=(self.FONT, -11),
            width=25,
            state=tkinter.DISABLED,
        )
        self.storage_location_info.place(relx=0.345, rely=0.85, anchor=tkinter.CENTER)

        self.change_location_button = customtkinter.CTkButton(
            master=self.storage_frame,
            text="Change Location",
            font=(self.FONT, -12),
            width=15,
            height=2,
            command=lambda: MISSThelpers.change_location(self),
            corner_radius=10,
        )
        self.change_location_button.place(relx=0.75, rely=0.775, anchor=tkinter.CENTER)

        ### Advanced Settings ###
        self.advanced_header = customtkinter.CTkLabel(
            master=self.general_frame.tab("Advanced"), text="Advanced", font=(self.FONT, -16)
        )
        self.advanced_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

        self.chosen_model_header = customtkinter.CTkLabel(
            master=self.general_frame.tab("Advanced"), text="Model:", font=(self.FONT, -12, "bold")
        )
        self.chosen_model_header.place(relx=0.2, rely=0.45, anchor=tkinter.CENTER)

        self.model_select = customtkinter.CTkOptionMenu(
            master=self.general_frame.tab("Advanced"), 
            font=(self.FONT, -12), 
            width=175, 
            values=["hdemucs_mmi",
                    "htdemucs",
                    "htdemucs_ft",
                    "mdx",
                    "mdx_extra",
                    "mdx_extra_q",
                    "mdx_q",
                    "repro_mdx_a",
                    "repro_mdx_a_hybrid_only",
                    "repro_mdx_a_time_only"]
        )
        self.model_select.place(relx=0.65, rely=0.45, anchor=tkinter.CENTER)
        self.model_select.set(self.settings.getSetting("chosen_model"))

        self.save_model_button = customtkinter.CTkButton(
            master=self.general_frame.tab("Advanced"),
            text="Download and Save Model",
            font=(self.FONT, -12),
            command=lambda: self.change_model(self.model_select.get()),
            corner_radius=10,
            height=15,
            width=30,
        )
        self.save_model_button.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        ### Theme Settings ###

        self.theme_frame = customtkinter.CTkFrame(master=self.settings_window, width=350, height=380)
        self.theme_frame.place(relx=0.75, rely=0.47, anchor=tkinter.CENTER)

        self.theme_header = customtkinter.CTkLabel(
            master=self.theme_frame, text="Theme", font=(self.FONT, -18)
        )
        self.theme_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        self.theme_frame_mini = customtkinter.CTkFrame(master=self.theme_frame, width=300, height=292)
        self.theme_frame_mini.place(relx=0.5, rely=0.56, anchor=tkinter.CENTER)

        self.button_light = customtkinter.CTkButton(
            master=self.theme_frame_mini,
            height=100,
            width=200,
            corner_radius=10,
            border_color="white",
            fg_color=self.settings.getSetting("chosenLightColor"),
            hover_color=self.settings.getSetting("chosenLightColor"),
            border_width=2,
            text="Light",
            command=lambda: MISSThelpers.updateTheme(self, "light"),
        )
        self.button_light.place(relx=0.5, rely=0.25, anchor=tkinter.CENTER)

        self.button_dark = customtkinter.CTkButton(
            master=self.theme_frame_mini,
            height=100,
            width=200,
            corner_radius=10,
            border_color="white",
            fg_color=self.settings.getSetting("chosenDarkColor"),
            hover_color=self.settings.getSetting("chosenDarkColor"),
            border_width=2,
            text="Dark",
            command=lambda: MISSThelpers.updateTheme(self, "dark"),
        )
        self.button_dark.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)

        self.info_label = customtkinter.CTkLabel(
            master=self.settings_window,
            text="Note: You may need to restart the app for changes to take effect.",
            font=(self.FONT, -11),
            state=tkinter.DISABLED,
            height=10,
        )
        self.info_label.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)

        self.reset_button = customtkinter.CTkButton(
            master=self.settings_window,
            text="Reset",
            font=(self.FONT, -12, "underline"),
            command=lambda: MISSThelpers.resetSettings(self),
            fg_color=self.settings_window.cget("fg_color"),
            hover_color=self.theme_frame.cget("fg_color"),
            width=25,
            height=25,
            text_color=self.info_label.cget("text_color")
        )
        self.reset_button.place(relx=0.75, rely=0.95, anchor=tkinter.CENTER)

        self.return_button = customtkinter.CTkButton(
            master=self.settings_window,
            command=lambda: self.settings_window.destroy(),
            image=self.ImageCache["return"],
            fg_color='transparent',
            hover_color=self.theme_frame.cget("fg_color"),
            text="",
            font=(self.FONT, -14),
            width=25,
            height=25,
            text_color=self.logolabel.cget("text_color"),
        )
        self.return_button.place(relx=0.25, rely=0.95, anchor=tkinter.CENTER)

    def eq_sliders_event(self, curVal:int, curSlider:int, sliders:list) -> None:
        """
        Event that is called when a slider is moved. If the move sliders together option is enabled, it will move all the sliders together.

        Args:
            curVal (int): The current value of the slider.
            curSlider (int): The index of the slider that was moved.
            sliders (list): A list of all the sliders.
        """
        self.settings.setSetting(f"eq_{curSlider+1}", str(curVal))
        if self.move_sliders_together.get() == 0:
            return
        slider = sliders[curSlider]
        for slider in sliders:
            index = sliders.index(slider)
            distance = abs(index - curSlider)
            if curVal < 0:
                multiplier = 1 * distance
                set = curVal + multiplier
                slider.set(set if set < 0 else 0)
                self.settings.setSetting(f"eq_{index+1}", str(slider.get()))
            else:
                multiplier = -1 * distance
                set = curVal + multiplier
                slider.set(set if set > 0 else 0)
                self.settings.setSetting(f"eq_{index+1}", str(slider.get()))
        return
        
    def moveSlidersTogether(self) -> None:
        """
        Event that is called when the move sliders together option is changed. It will save the setting.
        """
        self.settings.setSetting("eq_move_sliders_together", "true" if str(self.move_sliders_together.get()) == "1" else "false")
        return
    
    def eqOnOff(self) -> None:
        """
        Event that is called when the eq on/off button is changed. It will save the setting and enable/disable the eq sliders.
        """
        self.settings.setSetting("eq", "true" if str(self.eqOnOffButton.get()) == "1" else "false")
        if self.eqOnOffButton.get() == 0:
            self.eqOnOffButton.configure(text="Off")
            for child in self.eq_frame.winfo_children():
                child.configure(state=tkinter.DISABLED)
            self.eqOnOffButton.configure(state='normal')
            self.return_button.configure(state='normal')
            self.eq_header.configure(state='normal')
        else:
            self.eqOnOffButton.configure(text="On")
            for child in self.eq_frame.winfo_children():
                child.configure(state='normal')
        return

    def draw_effects_frame(self) -> None:
        """
        Draws the effects frame.
        """
        self.effects_window = customtkinter.CTkFrame(
            master=self, width=self.WIDTH * (755 / self.WIDTH), height=self.HEIGHT * (430 / self.HEIGHT)
        )
        self.effects_window.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.eq_frame = customtkinter.CTkFrame(master=self.effects_window, width=450, height=350)
        self.eq_frame.place(relx=0.35, rely=0.5, anchor=tkinter.CENTER)

        self.eq_header = customtkinter.CTkLabel(
            master=self.eq_frame, text="Equalizer", font=(self.FONT, -16)
        )
        self.eq_header.place(relx=0.15, rely=0.12, anchor=tkinter.CENTER)

        self.return_button = customtkinter.CTkButton(
            master=self.eq_frame,
            command=lambda: self.effects_window.destroy(),
            image=self.ImageCache["return"],
            fg_color='transparent',
            hover_color=self.effects_window.cget("bg_color"),
            text="",
            font=(self.FONT, -14),
            width=5,
            text_color=self.logolabel.cget("text_color"),
        )
        self.return_button.place(relx=0.87, rely=0.9, anchor=tkinter.CENTER)

        val = 0.02
        frqs = ["62 Hz", "125 Hz", "250 Hz", "500 Hz", "1 KHz", "2.5 KHz", "4 KHz", "8 KHz", "16 KHz"]
        sliders = [eq_slider1, eq_slider2, eq_slider3, eq_slider4, eq_slider5, eq_slider6, eq_slider7, eq_slider8, eq_slider9] = [None] * 9
        for i in range(0, len(sliders)):
            sliders[i] = customtkinter.CTkSlider(
                master=self.eq_frame,
                from_=-12,
                to=12,
                number_of_steps=24,
                orientation="vertical",
                height=175,
                command= lambda x, curSlider=i, sliders=sliders: self.eq_sliders_event(x, curSlider, sliders)
            )
            sliders[i].set(float(self.settings.getSetting(f"eq_{i+1}")))
            val += 0.1
            sliders[i].place(relx=val, rely=0.5, anchor=tkinter.CENTER)

        val = 0.02
        for frq in frqs:
            eq_label = customtkinter.CTkLabel(
                master=self.eq_frame, text=frq, font=(self.FONT, -10), state=tkinter.DISABLED
            )
            val += 0.1
            eq_label.place(relx=val, rely=0.8, anchor=tkinter.CENTER)

        self.eq_12dB_label = customtkinter.CTkLabel(
            master=self.eq_frame, text="+12dB", font=(self.FONT, -10), state=tkinter.DISABLED
        )
        self.eq_12dB_label.place(relx=0.05, rely=0.27, anchor=tkinter.CENTER)

        self.eq_6dB_label = customtkinter.CTkLabel(
            master=self.eq_frame, text="+6dB", font=(self.FONT, -10), state=tkinter.DISABLED
        )
        self.eq_6dB_label.place(relx=0.05, rely=0.395, anchor=tkinter.CENTER)

        self.eq_0dB_label = customtkinter.CTkLabel(
            master=self.eq_frame, text="0dB", font=(self.FONT, -10), state=tkinter.DISABLED
        )
        self.eq_0dB_label.place(relx=0.05, rely=0.5, anchor=tkinter.CENTER)

        self.eq_m6dB_label = customtkinter.CTkLabel(
            master=self.eq_frame, text="-6dB", font=(self.FONT, -10), state=tkinter.DISABLED
        )
        self.eq_m6dB_label.place(relx=0.05, rely=0.615, anchor=tkinter.CENTER)

        self.eq_m12dB_label = customtkinter.CTkLabel(
            master=self.eq_frame, text="-12dB", font=(self.FONT, -10), state=tkinter.DISABLED
        )
        self.eq_m12dB_label.place(relx=0.05, rely=0.73, anchor=tkinter.CENTER)

        self.move_sliders_together = customtkinter.CTkCheckBox(
            master=self.eq_frame, text="Move nearby sliders together", font=(self.FONT, -12), command=lambda: self.moveSlidersTogether()
        )
        self.move_sliders_together.place(relx=0.28, rely=0.9, anchor=tkinter.CENTER)
        if self.settings.getSetting("eq_move_sliders_together") == "true":
            self.move_sliders_together.select()
            self.moveSlidersTogether()
        else:
            self.move_sliders_together.deselect()
            self.moveSlidersTogether()

        self.eqOnOffButton = customtkinter.CTkSwitch(
            master=self.eq_frame,
            text="On",
            width=50,
            height=50,
            font=(self.FONT, -14),
            command=lambda: self.eqOnOff(),
        )
        self.eqOnOffButton.place(relx=0.85, rely=0.12, anchor=tkinter.CENTER)
        if self.settings.getSetting("eq") == "true":
            self.eqOnOffButton.select()
            self.eqOnOff()
        else:
            self.eqOnOffButton.deselect()
            self.eqOnOff()

        # Effects
        self.effects_frame = customtkinter.CTkFrame(master=self.effects_window, width=200, height=350)
        self.effects_frame.place(relx=0.82, rely=0.5, anchor=tkinter.CENTER)

        self.effects_header = customtkinter.CTkLabel(
            master=self.effects_frame, text="Effects", font=(self.FONT, -16)
        )
        self.effects_header.place(relx=0.5, rely=0.12, anchor=tkinter.CENTER)

        def setEffect(effect, value):
            self.settings.setSetting(effect, f"{value}")
            if effect == "speed":
                self.speed_slider.set(float(value))
            elif effect == "pitch":
                self.pitch_slider.set(float(value))
            elif effect == "bass":
                self.bass_slider.set(float(value))
            elif effect == "reverb":
                self.reverb_slider.set(float(value))

        # Effect - Speed
        self.speed_header = customtkinter.CTkLabel(
            master=self.effects_frame, text="Speed", font=(self.FONT, -14)
        )
        self.speed_header.place(relx=0.17, rely=0.23, anchor=tkinter.CENTER)

        self.speed_slider = customtkinter.CTkSlider(
            master=self.effects_frame,
            from_=0.25,
            to=1.75,
            number_of_steps=6,
            width=165,
            height=10,
            command=lambda x: setEffect("speed", x)
        )
        self.speed_slider.set(float(self.settings.getSetting("speed")))
        self.speed_slider.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

        speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]
        # create little indicators
        val = 0
        for value in speeds:
            speed_label = customtkinter.CTkLabel(
                master=self.effects_frame, text=value, font=(self.FONT, -10), state=tkinter.DISABLED
            )
            val += 0.125
            speed_label.place(relx=val, rely=0.37, anchor=tkinter.CENTER)

        # Effect - Pitch
        self.pitch_header = customtkinter.CTkLabel(
            master=self.effects_frame, text="Pitch", font=(self.FONT, -14)
        )
        self.pitch_header.place(relx=0.17, rely=0.48, anchor=tkinter.CENTER)

        self.pitch_slider = customtkinter.CTkSlider(
            master=self.effects_frame,
            from_=-1,
            to=1,
            number_of_steps=8,
            width=165,
            height=10,
            command=lambda x: setEffect("pitch", x)
        )
        self.pitch_slider.set(float(self.settings.getSetting("pitch")))
        self.pitch_slider.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

        pitch_factors = [-1.0, -0.5, 0.0, 0.5, 1.0]
        # create little indicators
        val = -0.06
        for value in pitch_factors:
            speed_label = customtkinter.CTkLabel(
                master=self.effects_frame, text=value, font=(self.FONT, -10), state=tkinter.DISABLED
            )
            val += 0.19
            speed_label.place(relx=val, rely=0.62, anchor=tkinter.CENTER)

        # Effect - Reverb
        self.reverb_header = customtkinter.CTkLabel(
            master=self.effects_frame, text="Reverb", font=(self.FONT, -14)
        )
        self.reverb_header.place(relx=0.17, rely=0.73, anchor=tkinter.CENTER)

        self.reverb_slider = customtkinter.CTkSlider(
            master=self.effects_frame,
            from_=0,
            to=1.5,
            number_of_steps=6,
            width=165,
            height=10,
            command=lambda x: setEffect("reverb", x)
        )
        self.reverb_slider.set(float(self.settings.getSetting("reverb")))
        self.reverb_slider.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

        reverb_factors = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
        # create little indicators
        val = 0
        for value in reverb_factors:
            value = value if value != 0 else "Off"
            reverb_label = customtkinter.CTkLabel(
                master=self.effects_frame, text=value, font=(self.FONT, -10), state=tkinter.DISABLED
            )
            val += 0.125
            reverb_label.place(relx=val, rely=0.87, anchor=tkinter.CENTER)
    
    def imports_check(self, search_entry:customtkinter.CTkEntry, songs_box:customtkinter.CTkTextbox) -> None:
        """
        Checks for new songs in the imports folder and adds them to the songs box

        Args:
            search_entry (tkinter.Entry): The search entry
            songs_box (tkinter.Text): The songs box
        """
        def add_highlight(text, start, end):
            text.tag_add("start", start, end)
            text.tag_config("start", background = self.settings.getSetting("chosenLightColor") if customtkinter.get_appearance_mode() == "Light" else self.settings.getSetting("chosenDarkColor"), foreground= "black")
        entry_val = None
        num = 0
        songs = []
        for _ in MISSThelpers.MISSTlistdir(self, self.importsDest):
            num += 1
            songs.append(f"{num}. {_}")
        while True:
            time.sleep(0.25)
            if self.songlabel.cget("text") == "Play Something!":
                self.export_button.configure(text="Nothing Playing")
                self.export_button.configure(state=tkinter.DISABLED)
            else:
                if (self.export_button.cget("text").startswith("Export")):
                    pass
                else:
                    self.export_button.configure(state=tkinter.NORMAL)
                    self.export_button.configure(text="Export")
            if len(MISSThelpers.MISSTlistdir(self, self.importsDest)) != num:
                num = 0
                songs = []
                for _ in MISSThelpers.MISSTlistdir(self, self.importsDest):
                    num += 1
                    songs.append(f"{num}. {_}")
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "\n\n".join(songs))
                songs_box.configure(state=tkinter.DISABLED)
            if len(songs) == 0:
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "No songs Imported!")
                songs_box.configure(state=tkinter.DISABLED)
            search = search_entry.get()
            found_songs = []
            for _ in songs:
                if search.lower() in _.lower():
                    found_songs.append(_)
            if entry_val == search_entry.get():
                pass
            else:
                songs_box.configure(state="normal")
                songs_box.delete("0.0", "end")
                songs_box.insert("0.0", "\n\n".join(found_songs))
                for line in songs_box.get("0.0", "end").splitlines():
                    if search.lower() in line.lower():
                        start = line.lower().find(search.lower())
                        end = line.lower().find(search.lower()) + len(search)
                        line_num = songs_box.get("0.0", "end").splitlines().index(line)
                        add_highlight(songs_box, f"{line_num + 1}.{start}", f"{line_num + 1}.{end}")
                songs_box.configure(state=tkinter.DISABLED)
                entry_val = search_entry.get()

    def play(self, dir:str) -> None:
        """
        Plays a song

        Args:
            dir (str): The directory of the song
        """
        self.player.change_files([
            f"{self.importsDest}/{dir}/bass.flac", 
            f"{self.importsDest}/{dir}/drums.flac", 
            f"{self.importsDest}/{dir}/other.flac", 
            f"{self.importsDest}/{dir}/vocals.flac"
            ], 
            [self.slider1.get(), 
             self.slider2.get(), 
             self.slider3.get(), 
             self.slider4.get()
            ]
        )
        self.update_UI(
            f"{self.importsDest}/{dir}/other.flac", 
            0
        )

    def play_search(self, index_label:str, songs:list) -> None:
        """
        Plays a song from the search box

        Args:
            index_label (str): The index of the song
            songs (list): The list of songs
        """
        self.playbutton.configure(state=tkinter.DISABLED)
        try:
            index = int(index_label)
            song = songs[index - 1]
            self.playing = True
            self.effects_checkbox.deselect()
            self.effects()
            self.play(song)
        except:
            self.logger.error(traceback.format_exc())
            pass
        self.playbutton.configure(state=tkinter.NORMAL)

    def export(self, songname:str, sliders:list) -> None:
        """
        Exports a song

        Args:
            songname (str): The name of the song
        """
        file = tkinter.filedialog.asksaveasfilename(initialfile=f"{songname}.mp3", filetypes=(('mp3 files', '*.mp3'),('All files', '*.*')))
        if file == "":
            self.export_button.configure(text="Export Cancelled.")
            threading.Timer(1.5, lambda: self.export_button.configure(text="Export")).start()
            return
        self.export_button.configure(text="Exporting...")
        self.player.save([
            f"{self.importsDest}/{songname}/bass.flac",
            f"{self.importsDest}/{songname}/drums.flac",
            f"{self.importsDest}/{songname}/other.flac",
            f"{self.importsDest}/{songname}/vocals.flac"
        ], [
            sliders[0].get(),
            sliders[2].get(),
            sliders[1].get(),
            sliders[3].get()
        ], file, MISSTconfig.getConfig(self, f"{self.importsDest}/{songname}")["image_raw"]
        )
        self.export_button.configure(text="Exported!")
        threading.Timer(1.5, lambda: self.export_button.configure(text="Export")).start()

    def shuffle(self) -> None:
        """
        Plays a random song
        """
        self.shuffle_button.configure(state=tkinter.DISABLED)
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            random.shuffle(songs)
            self.playing = True
            self.effects_checkbox.deselect()
            self.effects()
            self.play(songs[0])
        except:
            # can ignore this error
            pass
        self.shuffle_button.configure(state=tkinter.NORMAL)

    def play_next(self, songName:str) -> None:
        """
        Plays the next song

        Args:
            songName (str): The name of the current song
        """
        self.next_button.configure(state=tkinter.DISABLED)
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            index = songs.index(songName)
            self.playing = True
            self.effects_checkbox.deselect()
            self.effects()
            self.play(songs[index + 1])
        except:
            # can ignore this error
            pass
        self.next_button.configure(state=tkinter.NORMAL)

    def play_previous(self, songName:str) -> None:
        """
        Plays the previous song

        Args:
            songName (str): The name of the current song
        """
        self.previous_button.configure(state=tkinter.DISABLED)
        try:
            songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
            index = songs.index(songName)
            self.playing = True
            self.effects_checkbox.deselect()
            self.effects()
            self.play(songs[index - 1])
        except:
            # can ignore this error
            pass
        self.previous_button.configure(state=tkinter.NORMAL)

    def slider_event(self, value:int) -> None:
        """
        Sets the position of the song

        Args:
            value (int): The position of the song
        """
        frames_per_millisecond = self.player.frame_rate / 1000
        ms = value * 1000
        frame = int(ms * frames_per_millisecond)
        self.player.set_position(0, frame)
        self.player.set_position(1, frame)
        self.player.set_position(2, frame)
        self.player.set_position(3, frame)
        return
    
    def effects(self) -> None:
        """
        Sets the effects state
        """
        if self.effects_checkbox.get() == 'on':
            self.player.set_effects(True)
        else:
            self.player.set_effects(False)
    
    def playpause(self) -> None:
        """
        Pauses or resumes the song
        """
        if self.playing == True:
            self.playpause_button.configure(state="normal", image=self.ImageCache["paused"])
            self.player.pause()
            self.playing = False
            self.progressbar.configure(state=tkinter.DISABLED)
            self.effects_checkbox.configure(state=tkinter.DISABLED)
            self.effects_button.configure(state=tkinter.DISABLED)
            self.effects()
        else:
            self.playpause_button.configure(state="normal", image=self.ImageCache["playing"])
            self.player.resume()
            self.playing = True
            self.progressbar.configure(state="normal")
            self.effects_checkbox.configure(state="normal")
            self.effects_button.configure(state="normal")

    def loopEvent(self) -> None:
        """
        Sets the loop state
        """
        if self.loop == True:
            self.loop = False
            self.loop_button.configure(state="normal", image=self.ImageCache["loop-off"])
        else:
            self.loop = True
            self.loop_button.configure(state="normal", image=self.ImageCache["loop"])

    def update_progress_bar(self, current_time:int, total_duration:int) -> None:
        """
        Updates the progress bar

        Args:
            current_time (int): The current time of the song
            total_duration (int): The total duration of the song
        """
        progress = current_time / total_duration
        progress_in_seconds = int(progress * total_duration)

        self.progressbar.set(progress_in_seconds)
        self.progress_label_left.configure(text=f"{str(datetime.timedelta(seconds=progress_in_seconds))[2:7]}")
        self.progress_label_right.configure(text=f"{str(datetime.timedelta(seconds=total_duration))[2:7]}")
        
    def update_UI(self, audioPath:str, start_ms:int) -> None:
        """
        Updates the UI

        Args:
            audioPath (str): The path to the song
            start_ms (int): The start time of the song
        """
        try:
            self.lyrics_window.destroy() # Destroy the lyrics window if it exists
        except:
            pass
        try:
            self.next_button.configure(state="normal")
            self.previous_button.configure(state="normal")
            self.playpause_button.configure(state="normal")
            self.effects_checkbox.configure(state="normal")
            self.effects_button.configure(state="normal")
            self.effects_checkbox.deselect()
            self.effects()

            if self.playing == True:
                self.playpause_button.configure(image=self.ImageCache["playing"])
            else:
                self.playpause_button.configure(image=self.ImageCache["paused"])
        except:
            pass # This is just to prevent errors when the player is closed or the song is changed before the UI is updated.

        self.songlabel.configure(text="")
        song_name = os.path.basename(os.path.dirname(audioPath))
        song_dir = os.path.dirname(audioPath)
        config = MISSTconfig(song_dir)

        self.next_button.configure(command=lambda: self.play_next(song_name))
        self.previous_button.configure(command=lambda: self.play_previous(song_name))
        try:
            byte_string = config.getConfig(song_dir)["image_raw"]
            byte_data = base64.b64decode(byte_string)
            byte_stream = io.BytesIO(byte_data)
            byte_stream.seek(0)
            cover_art = customtkinter.CTkImage(Image.open(byte_stream), size=(40, 40))
        except:
            self.logger.error(traceback.format_exc())
            self.logger.error("No cover art found.")
            cover_art = self.ImageCache["no-cover-art"]

        namelen = len(song_name)
        n = 30
        shortname = song_name if namelen <= n else song_name[:(n - namelen)] + "..."
        self.current_song = song_name

        self.songlabel.configure(text=shortname)
        self.songlabel.configure(image=cover_art)

        duration = int(self.player.duration)
        self.progressbar.configure(from_=0, to=duration, state="normal")
        self.progressbar.set(start_ms // 1000)

        # Define a variable to track the current time
        current_time = start_ms // 1000

        MISSThelpers.update_rpc(
            self,
            Ltext="Listening to separated audio",
            Dtext=song_name,
            image=config.getConfig(song_dir)["image_url"],
            large_text=song_name,
            end_time=time.time() + duration,
            small_image="icon-0",
        )

        self.progressbar_active = False

        def reset_to_default():
            self.logger.info("No more songs to play. Returning to default state.")
            self.playpause_button.configure(image=self.ImageCache["paused"], state=tkinter.DISABLED)
            self.playing = False
            self.progressbar.configure(state=tkinter.DISABLED)
            self.effects_checkbox.configure(state=tkinter.DISABLED)
            self.effects_button.configure(state=tkinter.DISABLED)
            self.progressbar.set(0)
            self.progress_label_left.configure(text="00:00")
            self.progress_label_right.configure(text="00:00")
            self.songlabel.configure(text="Play Something!", image=self.ImageCache["empty"])
            self.next_button.configure(state=tkinter.DISABLED)
            self.previous_button.configure(state=tkinter.DISABLED)
            MISSThelpers.update_rpc(
                self,
                Ltext="Idle",
                Dtext="Nothing is playing",
                image="icon-0",
                large_text="MISST",
            )    
        
        def on_end():
            if self.loop == True:
                try:
                    self.play(song_name)
                except:
                    self.logger.error(traceback.format_exc())
                    reset_to_default()
            elif self.autoplay == True:
                try:
                    songs = MISSThelpers.MISSTlistdir(self, self.importsDest) 
                    index = songs.index(song_name)
                    self.playing = True
                    self.effects_checkbox.deselect()
                    self.effects()
                    self.play(songs[index + 1])
                except:
                    self.logger.error(traceback.format_exc())
                    reset_to_default()      
            else:
                reset_to_default()

        def update_progress():
            nonlocal current_time
            while True:
                time.sleep(0.1) # Update the progress bar every 100ms
                # Update the progress bar
                current_time = self.player.get_position(3)
                self.update_progress_bar(current_time, duration)
                # Increment the current time only if the user hasn't interacted with the progress bar
                if self.playing == False:
                    MISSThelpers.update_rpc(
                        self,
                        Ltext="(Paused)",
                        Dtext=song_name,
                        image=config.getConfig(song_dir)["image_url"],
                        large_text=song_name,
                        end_time=None,
                        small_image="icon-0",
                    )
                if not self.progressbar_active and self.playing == True:
                    MISSThelpers.update_rpc(
                        self,
                        Ltext="Listening to separated audio",
                        Dtext=song_name,
                        image=config.getConfig(song_dir)["image_url"],
                        large_text=song_name,
                        end_time=time.time() + duration - current_time,
                        small_image="icon-0",
                    )
                if current_time >= duration:
                    stop_update_thread()
                    on_end()
                    return

        def stop_update_thread():
            try:
                if self.update_timer:
                    MISSThelpers.terminate_thread(self, self.update_timer)
            except:
                pass # Can ignore this error because the threads pointer is killed when this function is called (which is when a new song is played)

        def on_progressbar_drag_start(event):
            self.progressbar_active = True

        def on_progressbar_drag_stop(event):
            nonlocal current_time
            self.progressbar_active = False
            # Update the current time based on the user's selection
            current_time = self.progressbar.get()

        # Bind the drag start and drag stop events to the progress bar
        self.progressbar.bind("<ButtonPress-1>", on_progressbar_drag_start)
        self.progressbar.bind("<ButtonRelease-1>", on_progressbar_drag_stop)

        # Stop the previous update thread if it exists
        stop_update_thread()

        # Start the progress update timer
        self.update_timer = threading.Thread(target=update_progress, daemon=True)
        self.update_timer.start()

if __name__ == "__main__":
    app = MISSTapp()
    MISSThelpers.update_rpc(app, Ltext="Idle", Dtext="Nothing is playing")
    app.mainloop()