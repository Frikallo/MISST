## LICENSE ----------------------------------------------------------------------------------------------------

# MISST 2.0.6
# Copyright (C) 2022 Frikallo.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

## IMPORTS ----------------------------------------------------------------------------------------------------
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chmod(os.getcwd(), 0o777)

import sys

sys.path.append(os.path.abspath("./binaries"))
sys.path.append(os.path.abspath("./binaries/ffmpeg.exe"))
sys.path.append(os.path.abspath("./binaries/ffmprobe.exe"))
import pygame
import datetime
from scipy.io import wavfile
import threading
import customtkinter
import tkinter
from tkinter.colorchooser import askcolor
from tkinter import PhotoImage, filedialog
import nightcore as nc
import logging
import os
import time
config = open("./Assets/config.txt", "r").readlines()

def getVal(val):
    for line in config:
        if val in line:
            return line.split("=")[1].strip().replace("'", "")

client_id = getVal("client_id")
genius_access_token = getVal("genius_access_token")
server_base = getVal("server_base")
importsdest = getVal("importsdest")
rpc = bool(getVal("rpc"))
autoplay = bool(getVal("autoplay"))
preprocess_method = getVal("preprocess_method")
dark_theme = getVal("dark_theme")
light_theme = getVal("light_theme")
DefaultDark_Theme = getVal("DefaultDark_Theme")
DefaultLight_Theme = getVal("DefaultLight_Theme")
json_data = getVal("json_data")
hover_color_light = getVal("hover_color_light")
hover_color_dark = getVal("hover_color_dark")
DefaultHover_ThemeLight = getVal("DefaultHover_ThemeLight")
DefaultHover_ThemeDark = getVal("DefaultHover_ThemeDark")
DarkerHover_ThemeDark = getVal("DarkerHover_ThemeDark")
DarkerHover_ThemeLight = getVal("DarkerHover_ThemeLight")
color_darker_light = getVal("color_darker_light")
color_darker_dark = getVal("color_darker_dark")
uid = getVal("uid")

from werkzeug.utils import secure_filename
import lyricsgenius as lg
from pypresence import Presence
import nest_asyncio
import subprocess
import requests
import shutil
import urllib.request
import gc
from PIL import Image, ImageTk
import io
import music_tag
import random
from ping3 import ping
import uuid
import socket
import matplotlib.colors as mc
import colorsys

## LOGGER ----------------------------------------------------------------------------------------------------

loggerName = "MISST"
logFormatter = logging.Formatter(fmt=" %(name)s :: %(levelname)-8s :: %(message)s")
logger = logging.getLogger(loggerName)
logger.setLevel(logging.INFO)

logging.basicConfig(
    filename="MISST.log",
    filemode="a",
    format=" %(name)s :: %(levelname)-8s :: %(message)s",
    level=logging.INFO,
)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.info(f'Logger initialized ({str(datetime.datetime.now()).split(".")[0]})')

# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warn message')
# logger.error('error message')
# logger.critical('critical message')

## GLOBAL VARIABLES ----------------------------------------------------------------------------------------------------

version = "V2.0.6"
discord_rpc = client_id
genius_access_token = genius_access_token
CREATE_NO_WINDOW = 0x08000000
GENIUS = True

demucs_post = f"{server_base}/demucs-upload"
demucs_get = f"{server_base}/download"
demucs_queue = f"{server_base}/queue"
demucs_coverart = f"{server_base}/coverart"

## INIT ----------------------------------------------------------------------------------------------------

nest_asyncio.apply()
gc.enable()
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(10)

try:
    genius_object = lg.Genius(genius_access_token)
except:
    GENIUS = False
    logger.error("connection failed")

if rpc == True:
    RPC = Presence(discord_rpc)
    try:
        RPC.connect()
        logger.info("Connected to Discord")
        RPC_CONNECTED = True
    except:
        RPC_CONNECTED = False
        logger.error("RPC connection failed")
else:
    RPC_CONNECTED = False
    logger.info("RPC disabled")

bass = pygame.mixer.Channel(0)
drums = pygame.mixer.Channel(1)
other = pygame.mixer.Channel(2)
vocals = pygame.mixer.Channel(3)


def checkInternetUrllib(url="http://google.com"):
    try:
        urllib.request.urlopen(url)
        return True
    except Exception as e:
        logger.error(e)
        return False


server_connection = None


def server_status(url=server_base):
    global server_connection
    try:
        req = requests.get(url)
        if req.text != "SSH Tunnel Down":
            server_connection = True
            return True
        else:
            server_connection = False
            return False
    except:
        server_connection = False
        return False


server_connection = server_status()
internet_connection = checkInternetUrllib()

if not os.path.exists(importsdest):
    os.mkdir(importsdest)

if os.path.exists("./dl-songs"):
    shutil.rmtree("./dl-songs")
    logger.info("dl-songs folder deleted")

## APP CONFIG ----------------------------------------------------------------------------------------------------

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme(
    "./Assets/Themes/MISST.json"
)  # Themes: "blue" (standard), "green", "dark-blue"

app = customtkinter.CTk()
app.title("MISST")
app.iconbitmap(r"./Assets/icon.ico")

WIDTH = 755
HEIGHT = 435

geometry = f"{WIDTH}x{HEIGHT}"
app.geometry(geometry)
app.resizable(False, False)
app.minsize(WIDTH, HEIGHT)
app.maxsize(WIDTH, HEIGHT)

check_var1 = tkinter.StringVar(value="on")
check_var2 = tkinter.StringVar(value="on")
check_var3 = tkinter.StringVar(value="on")
check_var4 = tkinter.StringVar(value="on")
nc_var = tkinter.StringVar(value="off")

## FUNCTIONS ----------------------------------------------------------------------------------------------------


def play_thread(sound, channel):
    thread = pygame.mixer.Sound(sound)
    while True:
        try:
            pygame.mixer.Channel(channel).play(thread)
            del thread
            gc.collect()
        except:
            songlabel.configure(text="")
            return
        while pygame.mixer.get_busy():
            pygame.time.delay(100)


def change_theme(theme):
    customtkinter.set_appearance_mode(theme)


def checkbox_event(checkbox, sound, slider):
    if checkbox.get() == "on":
        sound.set_volume(slider.get())
    else:
        slider.set(0)
        sound.set_volume(slider.get())


def slider_event(value, sound, checkbox):
    if value >= 0.01:
        checkbox.select()
        sound.set_volume(value)
    else:
        checkbox.deselect()
        sound.set_volume(value)


window = None
lyric_box = None


def lyrics_window():
    global window
    global lyric_box
    try:
        window.destroy()
    except:
        pass

    theme = customtkinter.get_appearance_mode()
    if theme == "Dark":
        frame_color = "#212325"
        frame_fg = "white"
    if theme == "Light":
        frame_color = "#EBEBEC"
        frame_fg = "black"

    try:
        file = os.path.join(importsdest + "/" + songlabel.text + "/.misst")
        if os.path.isfile(file):
            with open(file, "rb") as f:
                lyrics = f.read()
        else:
            raise Exception("No lyrics found")
        window = customtkinter.CTkToplevel(app)
        window.geometry("580x435")
        window.title("MISST")
        window.iconbitmap(r"./Assets/icon.ico")
        raise_above_all(window)

        lyric_box = tkinter.Text(
            bd=0,
            bg=frame_color,
            fg=frame_fg,
            highlightthickness=0,
            borderwidth=0,
            master=window,
            width=60,
            height=23,
            font=(FONT, -14),
        )
        lyric_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        lyric_box.insert(tkinter.END, lyrics)
        lyric_box.configure(state=tkinter.DISABLED)

    except Exception as e:
        logger.error(e)
        return


def get_lyrics(song, artist):
    try:
        if GENIUS == True:
            audio = genius_object.search_song(title=song, artist=artist)
            lyrics = audio.lyrics
        else:
            lyrics = "Internet connection is not available"
        return lyrics
    except Exception as e:
        logger.error(f"MISST Encountered an error, ({e})")
        return "Could not find lyrics."


import_window = None


def import_():
    global import_window
    try:
        import_window.destroy()
    except:
        pass
    WIDTH = 400
    HEIGHT = 275
    import_window = customtkinter.CTkToplevel(app)
    import_window.geometry(f"{WIDTH}x{HEIGHT}")
    import_window.title("MISST")
    import_window.iconbitmap(r"./Assets/icon.ico")

    import_window.resizable(False, False)
    import_window.minsize(WIDTH, HEIGHT)
    import_window.maxsize(WIDTH, HEIGHT)
    raise_above_all(import_window)

    song_frame = customtkinter.CTkFrame(import_window, width=375, height=175)
    song_frame.place(relx=0.5, rely=0.35, anchor=tkinter.CENTER)

    status_frame = customtkinter.CTkFrame(import_window, width=375, height=70)
    status_frame.place(relx=0.5, rely=0.83, anchor=tkinter.CENTER)

    status_label = customtkinter.CTkLabel(
        status_frame, text=" - ", text_font=(FONT, -14)
    )
    status_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    ## SONG IMPORT --------------------------------------------------

    importsong_label = customtkinter.CTkLabel(
        song_frame, text="Import song:", text_font=(FONT, -14)
    )
    importsong_label.place(relx=0.23, rely=0.1, anchor=tkinter.CENTER)

    mp3Import = customtkinter.CTkButton(
        master=song_frame,
        text="Import from .mp3",
        width=150,
        height=25,
        command=lambda: import_fun1(status_label),
    )
    mp3Import.place(relx=0.23, rely=0.3, anchor=tkinter.CENTER)

    breaklabel = customtkinter.CTkLabel(song_frame, text="OR", text_font=(FONT, -14))
    breaklabel.place(relx=0.23, rely=0.48, anchor=tkinter.CENTER)

    spot_importEntry = customtkinter.CTkEntry(
        master=song_frame,
        width=150,
        height=25,
        placeholder_text="Enter song url",
    )
    spot_importEntry.place(relx=0.23, rely=0.65, anchor=tkinter.CENTER)

    spot_import = customtkinter.CTkButton(
        master=song_frame,
        text="Import from Spotify",
        width=150,
        height=25,
        command=lambda: threading.Thread(
            target=import_fun2, args=(spot_importEntry.get(), status_label), daemon=True
        ).start(),
    )
    spot_import.place(relx=0.23, rely=0.85, anchor=tkinter.CENTER)

    ## PLAYLIST IMPORT --------------------------------------------------

    importplaylist_label = customtkinter.CTkLabel(
        song_frame, text="Import playlist:", text_font=(FONT, -14)
    )
    importplaylist_label.place(relx=0.77, rely=0.1, anchor=tkinter.CENTER)

    playlistthread = threading.Thread(target=import_fun3, args=(status_label,))
    playlistthread.daemon = True

    mp3PlaylistImport = customtkinter.CTkButton(
        master=song_frame,
        text="Import from .mp3's",
        width=150,
        height=25,
        command=lambda: playlistthread.start(),
    )
    mp3PlaylistImport.place(relx=0.77, rely=0.3, anchor=tkinter.CENTER)

    breakPlaylistlabel = customtkinter.CTkLabel(
        song_frame, text="OR", text_font=(FONT, -14)
    )
    breakPlaylistlabel.place(relx=0.77, rely=0.48, anchor=tkinter.CENTER)

    spot_PlaylistimportEntry = customtkinter.CTkEntry(
        master=song_frame,
        width=150,
        height=25,
        placeholder_text="Enter playlist url",
    )
    spot_PlaylistimportEntry.place(relx=0.77, rely=0.65, anchor=tkinter.CENTER)

    spot_Playlistimport = customtkinter.CTkButton(
        master=song_frame,
        text="Import from Spotify",
        width=150,
        height=25,
        command=lambda: threading.Thread(
            target=import_fun4,
            args=(spot_PlaylistimportEntry.get(), status_label),
            daemon=True,
        ).start(),
    )
    spot_Playlistimport.place(relx=0.77, rely=0.85, anchor=tkinter.CENTER)

    if server_connection == True or preprocess_method.replace("'", "") != "server":
        status_update(status_label, "Awaiting Instructions")
    else:
        mask_frame = customtkinter.CTkFrame(import_window, width=375, height=175)
        mask_frame.place(relx=0.5, rely=0.35, anchor=tkinter.CENTER)
        server_off = customtkinter.CTkButton(
            master=mask_frame,
            text="",
            width=100,
            height=100,
            image=PhotoImage(file="./Assets/server_off.png"),
            bg_color=mask_frame.fg_color,
            fg_color=mask_frame.fg_color,
            hover_color=mask_frame.fg_color,
        )
        server_off.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        status_update(status_label, "Server is not available")
        offline_label = customtkinter.CTkLabel(
            status_frame,
            text="(preprocessing services not available while server is down)",
            text_font=(FONT, -10),
            height=20,
        )
        offline_label.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)
        spot_Playlistimport.configure(state=tkinter.DISABLED)
        mp3PlaylistImport.configure(state=tkinter.DISABLED)
        spot_import.configure(state=tkinter.DISABLED)
        mp3Import.configure(state=tkinter.DISABLED)


def import_fun1(status_label):
    file = filedialog.askopenfilename(
        initialdir="/",
        title="Select file",
        filetypes=(("mp3 files", "*.mp3"), ("all files", "*.*")),
    )
    if file != "":
        try:
            status_update(status_label, "Preprocessing")
            preprocessthread = threading.Thread(
                target=preprocess, args=(file, status_label)
            )
            preprocessthread.daemon = True
            preprocessthread.start()
        except Exception as e:
            logger.error(e)
            errorlabel = customtkinter.CTkLabel(
                master=status_label.master,
                text="Error importing song",
                text_font=(FONT, -14),
                width=200,
            )
            errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    else:
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="No file selected",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)


def import_fun2(url, status_label):
    if url == "":
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="No url provided",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        time.sleep(1)
        errorlabel.destroy()
        return
    if not url.startswith("https://open.spotify.com/track/"):
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="Invalid url",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        time.sleep(1)
        errorlabel.destroy()
        return
    else:
        status_label.configure(text=f"")
        status_label.configure(text=f"Downloading")
        status_update(status_label, "Downloading")
        dlthread = threading.Thread(target=spot_dl, args=(url, status_label))
        dlthread.daemon = True
        dlthread.start()


def import_fun3(status_label):
    files = filedialog.askopenfilenames(
        initialdir="/",
        title="Select files",
        filetypes=(("mp3 files", "*.mp3"), ("all files", "*.*")),
    )
    if files != "":
        try:
            for file in files:
                status_update(
                    status_label,
                    "Preprocessing {}/{}".format(files.index(file) + 1, len(files)),
                )
                preprocessmultiple(file, status_label)
            donelabel = customtkinter.CTkLabel(
                master=status_label.master,
                text="Done! {} songs imported! \nresults can be found in:\n{}/separated".format(
                    len(files), os.getcwd()
                ),
                text_font=(FONT, -14),
                width=200,
            )
            donelabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        except Exception as e:
            logger.error(e)
            errorlabel = customtkinter.CTkLabel(
                master=status_label.master,
                text="Error importing song",
                text_font=(FONT, -14),
                width=200,
            )
            errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    else:
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="No file selected",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    try:
        for i in os.listdir("./dl-songs"):
            os.remove(os.path.join("./dl-songs", i))
        os.rmdir("./dl-songs")
    except:
        pass


def import_fun4(url, status_label):
    if url == "":
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="No url provided",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        time.sleep(1)
        errorlabel.destroy()
        return
    if not url.startswith("https://open.spotify.com/playlist/") and not url.startswith(
        "https://open.spotify.com/album/"
    ):
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="Invalid url",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        time.sleep(1)
        errorlabel.destroy()
        return
    else:
        status_label.configure(text=f"")
        status_label.configure(text=f"Downloading")
        status_update(status_label, "Downloading")
        spot_dl_playlist(url, status_label)
        for i in os.listdir("./dl-songs"):
            status_update(
                status_label,
                "Preprocessing {}/{}".format(
                    os.listdir("./dl-songs").index(i) + 1, len(os.listdir("./dl-songs"))
                ),
            )
            preprocessmultiple("./dl-songs/" + i, status_label)
        donelabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="Done! {} songs imported! \nresults can be found in:\n{}/separated".format(
                len(os.listdir("./dl-songs")), os.getcwd()
            ),
            text_font=(FONT, -14),
            width=200,
        )
        donelabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        try:
            for i in os.listdir("./dl-songs"):
                os.remove(os.path.join("./dl-songs", i))
            os.rmdir("./dl-songs")
        except:
            pass
        return


## UTIL FUNCTIONS ----------------------------------------------------------------------------------------------------


def getsize(dir):
    total = 0
    for entry in os.scandir(dir):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += getsize(entry.path)
    return total


def format_size(size):
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return size


def clear_downloads(dir, frame):
    try:
        for file in os.listdir(dir):
            file = os.path.join(dir, file).replace("\\", "/")
            if os.path.isdir(file) and os.path.isfile(file + "/.misst"):
                shutil.rmtree(file)
        frame.destroy()
        settings()
    except:
        pass


def clear_downloads_window(dir, settings_window):
    confirmation_frame = customtkinter.CTkFrame(
        master=settings_window, width=350, height=350, corner_radius=10
    )
    confirmation_frame.place(relx=0.25, rely=0.5, anchor=tkinter.CENTER)

    confirmation_header = customtkinter.CTkLabel(
        master=confirmation_frame, text="Are you sure?", text_font=(FONT, -16)
    )
    confirmation_header.place(relx=0.5, rely=0.45, anchor=tkinter.CENTER)
    confirmation_yes = customtkinter.CTkButton(
        master=confirmation_frame,
        text="Yes",
        text_font=(FONT, -12),
        command=lambda: clear_downloads(dir, confirmation_frame),
        width=80,
    )
    confirmation_yes.place(relx=0.35, rely=0.55, anchor=tkinter.CENTER)
    confirmation_no = customtkinter.CTkButton(
        master=confirmation_frame,
        text="No",
        text_font=(FONT, -12),
        command=lambda: confirmation_frame.destroy(),
        width=80,
    )
    confirmation_no.place(relx=0.65, rely=0.55, anchor=tkinter.CENTER)


def change_location():
    global importsdest
    try:
        importsdest_nocheck = filedialog.askdirectory(
            initialdir=os.path.abspath(importsdest)
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
            update_setting("importsdest", f"'{importsdest}'")
            settings()
            return None
        else:
            importsdest = os.path.abspath(importsdest)
            return None
    except:
        importsdest = os.path.abspath(importsdest)
        return None


def update_setting(setting, value):
    global autoplay
    global rpc
    global preprocess_method
    global dark_theme
    global light_theme
    global hover_color_light
    global hover_color_dark
    global color_darker_light
    global color_darker_dark
    if setting == "autoplay":
        autoplay = value
    elif setting == "rpc":
        rpc = value
    elif setting == "preprocess_method":
        preprocess_method = value
    elif setting == "dark_theme":
        dark_theme = value.replace("'", "")
    elif setting == "light_theme":
        light_theme = value.replace("'", "")
    elif setting == "hover_color_light":
        hover_color_light = value.replace("'", "")
    elif setting == "hover_color_dark":
        hover_color_dark = value.replace("'", "")
    elif setting == "color_darker_light":
        color_darker_light = value.replace("'", "")
    elif setting == "color_darker_dark":
        color_darker_dark = value.replace("'", "")
    settings = open("./Assets/config.txt").readlines()
    lines = []
    for line in settings:
        if setting in line:
            line = f"{setting} = {value}\n"
            lines.append(line)
        else:
            lines.append(line)
    with open("./Assets/config.txt", "w") as f:
        f.writelines(lines)


if server_connection == True:
    try:
        uid = str(uuid.uuid4()) if uid == '"None"' else uid
        requests.post(f"{server_base}/user/{uid}", data=str(socket.gethostbyname(socket.gethostname())))
        update_setting("uid", uid)
    except Exception as e:
        logger.error("Failed to generate new UID ({})".format(e))
        pass


def count(label, text):
    t = 0
    try:
        while True:
            time.sleep(0.5)
            if label.text == "":
                break
            if t > 3:
                t -= t
            periods = ["", ".", "..", "..."]
            label.configure(text=f"{text}{periods[t]}")
            t += 1
    except:
        pass
    return


def update_rpc(
    Ltext=None,
    Dtext=None,
    image="icon-0",
    large_text="MISST",
    end_time=None,
    small_image=None,
):
    start_time = time.time()
    if RPC_CONNECTED:
        try:
            RPC.update(
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


def update_songUI(song):
    songlabel.configure(text="")
    song_name = os.path.basename(os.path.dirname(song))
    song_dir = os.path.dirname(song)
    try:
        cover_art = ImageTk.PhotoImage(get_album_art(song_dir, song_name))
    except:
        cover_art = ImageTk.PhotoImage(Image.open("./assets/default.png"))
    songlabel.configure(text=song_name, image=cover_art)
    web_name = song_name.replace(" ", "")
    nc_checkbox.configure(state="normal")
    label = tkinter.Label(image=cover_art)
    label.image = cover_art
    label.place(relx=2, rely=2, anchor=tkinter.CENTER)
    sample_rate, audio_data = wavfile.read(song)
    duration = audio_data.shape[0] / sample_rate
    update_rpc(
        Ltext="Listening to seperated audio",
        Dtext=song_name,
        image=f"{server_base}getcoverart/{web_name}.png",
        large_text=song_name,
        end_time=time.time() + duration,
        small_image="icon-0",
    )
    t = 0

    progress_label_left = customtkinter.CTkLabel(
        master=north_frame, text="0:00", text_font=(FONT, -12), width=75
    )
    progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

    progress_label_right = customtkinter.CTkLabel(
        master=north_frame, text="0:00", text_font=(FONT, -12), width=75
    )
    progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

    progressbar = customtkinter.CTkProgressBar(master=north_frame, width=225, height=10)
    progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
    progressbar.set(0)

    for _ in os.listdir(importsdest + "/" + song_name):
        if _.endswith("_nc.wav"):
            os.remove(importsdest + "/" + song_name + "/" + _)

    percent = 0

    while True:
        if songlabel.text == "":

            if loop == True and not song.endswith("_nc.wav"):
                print("looping")
                nc_checkbox.deselect()
                play_song(song_dir)
                break
            else:
                progressbar.set(0)
                songlabel.configure(text="(song name)", image=None)
                progress_label_left.configure(text="0:00")
                progress_label_right.configure(text="0:00")
                update_rpc(
                    Ltext="Idle",
                    Dtext="Nothing is playing",
                    image="icon-0",
                    large_text="MISST",
                )
                nc_checkbox.configure(state=tkinter.DISABLED)
                break

        if songlabel.text != song_name:
            break

        if playing == False:
            update_rpc(
                Ltext="(Paused)",
                Dtext=song_name,
                image=f"{server_base}getcoverart/{web_name}.png",
                large_text=song_name,
                end_time=None,
                small_image="icon-0",
            )
            while playing == False:
                time.sleep(0.1)
                if playing != False:
                    update_rpc(
                        Ltext="Listening to seperated audio",
                        Dtext=song_name,
                        image=f"{server_base}getcoverart/{web_name}.png",
                        large_text=song_name,
                        end_time=time.time() + duration - t,
                        small_image="icon-0",
                    )
                    break
        t += 1
        percent = t / duration
        progressbar.set(percent)
        progress_label_left.configure(
            text=f"{str(datetime.timedelta(seconds=t)).split('.')[0][2:]}"
        )
        progress_label_right.configure(
            text=f"{str(datetime.timedelta(seconds=duration-t)).split('.')[0][2:]}"
        )
        time.sleep(1)
    if autoplay == True and percent >= 0.99 and loop != True:
        try:
            next_song(song_name)
            return
        except:
            pass
    return


def spot_dl(url, status_label):
    if os.path.exists("./dl-songs"):
        pass
    else:
        os.mkdir("./dl-songs")
    try:
        spotdl = os.path.abspath("./binaries/spotdl.exe")
        ffmpeg = os.path.abspath("./binaries/ffmpeg.exe")
        try:
            cmd = subprocess.call(
                f"{spotdl} download {url} --output ./dl-songs --ffmpeg {ffmpeg}",
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
            )
        except Exception as e:
            logger.error(e)
        if cmd != 0:
            raise Exception
        logger.info("Download complete")
        status_update(status_label, "Preprocessing")
        pp_thread = threading.Thread(
            target=preprocess,
            args=(f'./dl-songs/{os.listdir("./dl-songs")[0]}', status_label),
        )
        pp_thread.daemon = True
        pp_thread.start()
    except Exception as e:
        logger.error(e)
        logger.error(cmd.stdout.decode())
        logger.error("Download failed")
        error_label = customtkinter.CTkLabel(
            status_label.master,
            text="Download failed",
            text_font=(FONT, -14),
            width=200,
        )
        error_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return


def spot_dl_playlist(url, status_label):
    if os.path.exists("./dl-songs"):
        pass
    else:
        os.mkdir("./dl-songs")
    try:
        spotdl = os.path.abspath("./binaries/spotdl.exe")
        ffmpeg = os.path.abspath("./binaries/ffmpeg.exe")
        cmd = subprocess.call(
            f"{spotdl} download {url} --output ./dl-songs --ffmpeg {ffmpeg}",
            creationflags=CREATE_NO_WINDOW,
        )
        if cmd != 0:
            raise Exception
        logger.info("Download complete")
    except:
        logger.error("Download failed")
        error_label = customtkinter.CTkLabel(
            status_label.master,
            text="Download failed",
            text_font=(FONT, -14),
            width=200,
        )
        error_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return


def preprocess(abspath_song, status_label):
    start = time.time()
    songname = urllib.parse.quote(secure_filename(os.path.splitext(os.path.basename(abspath_song))[0]))
    try:
        status_update(status_label, "In Queue")
        queue = requests.post(demucs_queue)
        logger.info("Added to queue")
        logger.info(queue.content)
        status_update(status_label, "Preprocessing")
        requests.post(demucs_post, files={"file": open(abspath_song, "rb")})
        logger.info("preprocessed")
        subprocess.run(
            f'curl "{demucs_get}/{songname}.zip" -o "{songname.replace("_", " ")}.zip"',
            creationflags=CREATE_NO_WINDOW,
            check=True,
        )
        logger.info("downloaded")
        songname = songname.replace("_", " ")
        savename = urllib.parse.unquote(songname.replace(".mp3", ""))
        ns = []
        for _ in os.listdir(importsdest):
            if savename in _:
                ns.append(_)  # get all songs with the same name
        n = len(ns)
        if os.path.exists(f"{importsdest}/{savename}"):
            savename = f"{savename} ({n})"
        shutil.unpack_archive(f"{songname}.zip", f"{importsdest}/{savename}")
        logger.info("unpacked")
        os.remove(f"{songname}.zip")
    except Exception as e:
        logger.error(e)
        logger.error("Preprocessing failed")
        error_label = customtkinter.CTkLabel(
            status_label.master,
            text="Preprocessing failed",
            text_font=(FONT, -14),
            width=200,
        )
        error_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return

    try:
        metadata = music_tag.load_file(abspath_song)
        metaart = metadata["artwork"]
        metaimg = Image.open(io.BytesIO(metaart.first.data))
        metaimg.save(f"{importsdest}/{savename}/cover.png")
    except:
        logger.error("No metadata found")
        shutil.copyfile("./Assets/default.png", f"{importsdest}/{savename}/cover.png")
        pass

    try:
        lyrics = get_lyrics(metadata["title"].first, metadata["albumartist"].first)
        with open(f"{importsdest}/{savename}/.misst", "w", encoding="utf-8") as f:
            f.write(lyrics)
        logger.info("Lyrics saved")
    except:
        logger.error("No lyrics found")
        with open(f"{importsdest}/{savename}/.misst", "w", encoding="utf-8") as f:
            f.write("No lyrics found")
        pass

    try:
        for i in os.listdir("./dl-songs"):
            os.remove(os.path.join("./dl-songs", i))
        os.rmdir("./dl-songs")
    except:
        pass

    end = int(time.time() - start)
    logger.info(f"Preprocessing took {end} seconds")
    done_label = customtkinter.CTkLabel(
        status_label.master,
        text=f"Done! took {end} seconds",
        text_font=(FONT, -14),
        width=200,
    )
    done_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    time.sleep(3)
    status_update(status_label, "Awaiting Instructions")
    play_song(f"{importsdest}/{savename}")
    return


def preprocessmultiple(abspath_song, status_label):
    songname = urllib.parse.quote(secure_filename(os.path.splitext(os.path.basename(abspath_song))[0]))
    try:
        requests.post(demucs_queue)
        requests.post(demucs_post, files={"file": open(abspath_song, "rb")})
        logger.info("preprocessed")
        subprocess.run(
            f'curl "{demucs_get}/{songname}.zip" -o "{songname.replace("_", " ")}.zip"',
            creationflags=CREATE_NO_WINDOW,
            check=True,
        )
        logger.info("downloaded")
        songname = songname.replace("_", " ")
        savename = urllib.parse.unquote(songname.replace(".mp3", ""))
        ns = []
        for _ in os.listdir(importsdest):
            if savename in _:
                ns.append(_)  # get all songs with the same name
        n = len(ns)
        if os.path.exists(f"{importsdest}/{savename}"):
            savename = f"{savename} ({n})"
        shutil.unpack_archive(f"{songname}.zip", f"{importsdest}/{savename}")
        logger.info("unpacked")
        os.remove(f"{songname}.zip")
    except Exception as e:
        logger.error(e)
        logger.error("Preprocessing failed")
        error_label = customtkinter.CTkLabel(
            status_label.master,
            text="Preprocessing failed",
            text_font=(FONT, -14),
            width=200,
        )
        error_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        pass
    try:
        metadata = music_tag.load_file(abspath_song)
        metaart = metadata["artwork"]
        metaimg = Image.open(io.BytesIO(metaart.first.data))
        metaimg.save(f"{importsdest}/{savename}/cover.png")
    except:
        logger.error("No metadata found")
        try:
            shutil.copyfile(
                "./Assets/default.png", f"{importsdest}/{savename}/cover.png"
            )
        except:
            pass
        pass
    try:
        lyrics = get_lyrics(metadata["title"].first, metadata["albumartist"].first)
        with open(f"{importsdest}/{savename}/.misst", "w", encoding="utf-8") as f:
            f.write(lyrics)
        logger.info("Lyrics saved")
    except:
        logger.error("No lyrics found")
        with open(f"{importsdest}/{savename}/.misst", "w", encoding="utf-8") as f:
            f.write("No lyrics found")
        pass
    return


def play_song(parent_dir, nightcore=False):

    end = ".wav"
    if nightcore == True:
        end = "_nc.wav"

    reset_interface()

    thread1 = threading.Thread(
        target=play_thread, args=(os.path.join(parent_dir, f"bass{end}"), 0)
    )
    thread2 = threading.Thread(
        target=play_thread, args=(os.path.join(parent_dir, f"drums{end}"), 1)
    )
    thread3 = threading.Thread(
        target=play_thread, args=(os.path.join(parent_dir, f"other{end}"), 2)
    )
    thread4 = threading.Thread(
        target=play_thread, args=(os.path.join(parent_dir, f"vocals{end}"), 3)
    )
    songthread = threading.Thread(
        target=update_songUI, args=(os.path.join(parent_dir, f"other{end}"),)
    )

    thread1.daemon = True
    thread2.daemon = True
    thread3.daemon = True
    thread4.daemon = True
    songthread.daemon = True

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    songthread.start()


def status_update(status_label, status):
    master = status_label.master
    status_label = customtkinter.CTkLabel(
        master, text=status, text_font=(FONT, -14), width=200
    )
    status_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    status_thread = threading.Thread(target=count, args=(status_label, status))
    status_thread.daemon = True
    status_thread.start()


def get_album_art(abspathsong, songname):
    web_name = songname.replace(" ", "")

    try:
        im = Image.open(f"{abspathsong}/cover.png")
        im.save(f"{abspathsong}/{web_name}.png")
        im = im.resize((40, 40))
        os.remove(f"{abspathsong}/cover.png")
    except:
        pass

    try:
        im = Image.open(f"{abspathsong}/{web_name}.png")
        im = im.resize((40, 40))
    except Exception as e:
        logger.error(f"No album art found: {e}")
        return None

    if RPC_CONNECTED:
        try:
            req = requests.post(
                demucs_coverart,
                files={"file": open(f"{abspathsong}/{web_name}.png", "rb")},
                json={"name": web_name},
                timeout=0.5,
            )
            logger.info(f"Cover art uploaded to server: {req.status_code} ({songname})")
        except Exception as e:
            logger.error(f"Error uploading cover art: {e}")
            pass

    return im


def misst_listdir(path):
    try:
        os_list = os.listdir(path)
        misst_list = []
        for _ in os_list:
            if os.path.isfile(f"{path}/{_}/.misst"):
                misst_list.append(_)
        return misst_list
    except:
        return []


def global_checks(search_entry, songs_box):
    entry_val = None
    num = 0
    songs = []
    for _ in misst_listdir(importsdest):
        num += 1
        songs.append(f"{num}. {_}")
    while True:
        time.sleep(0.5)
        if len(misst_listdir(importsdest)) != num:
            num = 0
            songs = []
            for _ in misst_listdir(importsdest):
                num += 1
                songs.append(f"{num}. {_}")
            songs_box.configure(state="normal")
            songs_box.delete("1.0", tkinter.END)
            songs_box.insert(tkinter.END, "\n\n".join(songs))
            songs_box.configure(state=tkinter.DISABLED)

        songs_box.configure(
            bg=songs_box.master.fg_color[
                1 if customtkinter.get_appearance_mode() == "Dark" else 0
            ],
            fg="white" if customtkinter.get_appearance_mode() == "Dark" else "black",
        )
        try:
            lyric_box.configure(
                bg=lyric_box.master.fg_color[
                    1 if customtkinter.get_appearance_mode() == "Dark" else 0
                ],
                fg="white"
                if customtkinter.get_appearance_mode() == "Dark"
                else "black",
            )
        except:
            # Lyrics box not created yet
            pass
        if len(songs) == 0:
            songs_box.configure(state="normal")
            songs_box.delete("1.0", tkinter.END)
            songs_box.insert(tkinter.END, "No songs Imported!")
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
            songs_box.delete("1.0", tkinter.END)
            songs_box.insert(tkinter.END, "\n\n".join(found_songs))
            songs_box.configure(state=tkinter.DISABLED)
            entry_val = search_entry.get()


def play_search(index_label, songs):
    try:
        index = int(index_label)
        song = songs[index - 1]
        nc_checkbox.deselect()
        play_song(f"{importsdest}/{song}")
    except:
        pass


def raise_above_all(window):
    window.attributes("-topmost", 1)
    window.attributes("-topmost", 0)


inprogress = None


def nightcore(song, tones=3):
    nc_checkbox.configure(state=tkinter.DISABLED)
    value = nc_var.get()
    if value == "on":
        parentdir = os.path.abspath(os.path.join(importsdest, song.text))
        for _ in os.listdir(parentdir):
            if _.endswith(".wav"):
                song = os.path.join(parentdir, _)
                nc_audio = song @ nc.Tones(tones)
                _name = _.replace(".wav", "_nc.wav")
                nc_audio.export(f"{parentdir}/{_name}", format="wav")
        play_song(parentdir, nightcore=True)
        nc_checkbox.configure(state=tkinter.NORMAL)
        return None
    if value == "off":
        if song.text == "":
            return None
        play_song(os.path.abspath(os.path.join(importsdest, song.text)))
        nc_checkbox.configure(state=tkinter.NORMAL)
        return None


playing = None


def playpause():
    global playing
    if playing == False:

        other.unpause()
        vocals.unpause()
        bass.unpause()
        drums.unpause()

        playpause_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[0], 32)),
            command=lambda: playpause(),
            text="",
            width=32,
            height=32,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
        )
        playpause_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        playing = True
        return None

    if other.get_busy() or vocals.get_busy() or bass.get_busy() or drums.get_busy():
        other.pause()
        vocals.pause()
        bass.pause()
        drums.pause()

        playpause_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[1], 32)),
            command=lambda: playpause(),
            text="",
            width=32,
            height=32,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
        )
        playpause_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        playing = False
        return None


def next_song(song):
    global loop
    loop = False
    songs = misst_listdir(importsdest)
    index = songs.index(song)
    try:
        nc_checkbox.deselect()
        play_song(f"{importsdest}/{songs[index + 1]}")
        return None
    except Exception as e:
        logger.error(e)
        return None


def last_song(song):
    global loop
    loop = False
    songs = misst_listdir(importsdest)
    index = songs.index(song)
    if index == 0:
        return None
    try:
        nc_checkbox.deselect()
        play_song(f"{importsdest}/{songs[index - 1]}")
        return None
    except Exception as e:
        logger.error(e)
        return None


def shuffle():
    global loop
    loop = False
    try:
        songs = misst_listdir(importsdest)
        random.shuffle(songs)
        nc_checkbox.deselect()
        play_song(f"{importsdest}/{songs[0]}")
    except Exception as e:
        logger.error(e)
        logger.warning("No songs to shuffle!")
        pass


loop = None


def loop_song():
    global loop

    if loop != True:
        loop = True
        repeat_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[7], 25)),
            command=lambda: loop_song(),
            text="",
            width=25,
            height=25,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
        )
        repeat_button.place(relx=0.88, rely=0.5, anchor=tkinter.CENTER)
        return None
    else:
        loop = False
        repeat_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[6], 25)),
            command=lambda: loop_song(),
            text="",
            width=25,
            height=25,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
        )
        repeat_button.place(relx=0.88, rely=0.5, anchor=tkinter.CENTER)
        return None


def reset_interface():
    global playing
    playing = True

    playpause_button = customtkinter.CTkButton(
        master=interface_frame,
        image=PhotoImage(file=resize_image(interface_assets[0], 32)),
        command=lambda: playpause(),
        text="",
        width=32,
        height=32,
        fg_color=interface_frame.fg_color,
        hover_color=app.fg_color,
        state="normal",
    )
    playpause_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    if loop == False or loop == None:
        repeat_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[6], 25)),
            command=lambda: loop_song(),
            text="",
            width=25,
            height=25,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
            state="normal",
        )
        repeat_button.place(relx=0.88, rely=0.5, anchor=tkinter.CENTER)
    elif loop == True:
        repeat_button = customtkinter.CTkButton(
            master=interface_frame,
            image=PhotoImage(file=resize_image(interface_assets[7], 25)),
            command=lambda: loop_song(),
            text="",
            width=25,
            height=25,
            fg_color=interface_frame.fg_color,
            hover_color=app.fg_color,
            state="normal",
        )
        repeat_button.place(relx=0.88, rely=0.5, anchor=tkinter.CENTER)

    next_button.configure(state="normal")
    previous_button.configure(state="normal")
    shuffle_button.configure(state="normal")
    repeat_button.configure(state="normal")


def refresh():
    global inprogress
    if inprogress == True:
        return None
    inprogress = True
    try:
        import_window.destroy()
    except:
        pass
    try:
        server_connection = server_status()
        delay = int(ping(server_base[7:-6]) * 1000)
        if server_connection == True:
            refresh_button.configure(image=None, text=f"{delay}ms", width=25, height=25)
            time.sleep(1.5)
            refresh_button.configure(
                text="",
                image=PhotoImage(file=f"./Assets/reload.png"),
                width=25,
                height=25,
            )
        else:
            refresh_button.configure(
                text="",
                image=PhotoImage(file=f"./Assets/no-connection.png"),
                width=25,
                height=25,
            )
            time.sleep(1.5)
            refresh_button.configure(
                text="",
                image=PhotoImage(file=f"./Assets/reload.png"),
                width=25,
                height=25,
            )
        inprogress = False
    except:
        return None
    return None


def lighten_color(color, amount=0.5):
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    string = colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
    hex_string = "#%02x%02x%02x" % (
        int(string[0] * 255),
        int(string[1] * 255),
        int(string[2] * 255),
    )
    return hex_string.replace("-", "")


def change_color_light(button_light):
    color1 = askcolor(
        title="Choose color for (Light)", initialcolor=button_light.fg_color
    )[1]
    if color1 is not None:
        button_light.configure(fg_color=color1)
        accent_theme = lighten_color(color1, 1.5)
        hover_color_darker = lighten_color(accent_theme, 1.5)
        theme = (
            str(json_data)
            .replace("defaultLight", color1)
            .replace("defaultDark", dark_theme)
            .replace("LightHover", accent_theme)
            .replace("DarkHover", hover_color_dark)
            .replace("DarkerHoverLight", hover_color_darker)
            .replace("DarkerHoverDark", color_darker_dark)
        )
        update_setting("color_darker_light", f"'{hover_color_darker}'")
        update_setting("hover_color_light", f"'{accent_theme}'")
        update_setting("light_theme", f"'{color1}'")
        with open("./Assets/Themes/MISST.json", "w") as f:
            f.write(theme)


def change_color_dark(button_dark):
    color2 = askcolor(
        title="Choose color for (Dark)", initialcolor=button_dark.fg_color
    )[1]
    if color2 is not None:
        button_dark.configure(fg_color=color2)
        accent_theme = lighten_color(color2, 1.5)
        hover_color_darker = lighten_color(accent_theme, 1.5)
        theme = (
            str(json_data)
            .replace("defaultDark", color2)
            .replace("defaultLight", light_theme)
            .replace("LightHover", hover_color_light)
            .replace("DarkHover", accent_theme)
            .replace("DarkerHoverDark", hover_color_darker)
            .replace("DarkerHoverLight", color_darker_light)
        )
        update_setting("color_darker_dark", f"'{hover_color_darker}'")
        update_setting("hover_color_dark", f"'{accent_theme}'")
        update_setting("dark_theme", f"'{color2}'")
        with open("./Assets/Themes/MISST.json", "w") as f:
            f.write(theme.replace('"""', ""))


def reset_settings(
    button_light, button_dark, rpc_button, autoplay_button, preprocess_button
):
    theme = (
        str(json_data)
        .replace("defaultLight", DefaultLight_Theme)
        .replace("defaultDark", DefaultDark_Theme)
        .replace("LightHover", DefaultHover_ThemeLight)
        .replace("DarkHover", DefaultHover_ThemeDark)
        .replace("DarkerHoverLight", DarkerHover_ThemeLight)
        .replace("DarkerHoverDark", DarkerHover_ThemeDark)
    )
    update_setting("light_theme", f"'{DefaultLight_Theme}'")
    update_setting("dark_theme", f"'{DefaultDark_Theme}'")
    update_setting("hover_color_light", f"'{DefaultHover_ThemeLight}'")
    update_setting("hover_color_dark", f"'{DefaultHover_ThemeDark}'")
    update_setting("color_darker_light", f"'{DarkerHover_ThemeLight}'")
    update_setting("color_darker_dark", f"'{DarkerHover_ThemeDark}'")
    rpc_button.select()
    autoplay_button.select()
    preprocess_button.select()
    button_light.configure(fg_color=DefaultLight_Theme)
    button_dark.configure(fg_color=DefaultDark_Theme)
    with open("./Assets/Themes/MISST.json", "w") as f:
        f.write(theme.replace('"""', ""))


def settings():
    if os.path.isdir(importsdest) == False:
        os.mkdir(importsdest)

    settings_window = customtkinter.CTkFrame(
        master=app, width=755, height=435, fg_color=app.fg_color
    )
    settings_window.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    settings_frame = customtkinter.CTkFrame(
        master=settings_window, width=350, height=380
    )
    settings_frame.place(relx=0.25, rely=0.47, anchor=tkinter.CENTER)

    setting_header = customtkinter.CTkLabel(
        master=settings_frame, text="Settings", text_font=(FONT, -18)
    )
    setting_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

    general_frame = customtkinter.CTkFrame(master=settings_frame, width=300, height=125)
    general_frame.place(relx=0.5, rely=0.35, anchor=tkinter.CENTER)

    general_header = customtkinter.CTkLabel(
        master=general_frame, text="General", text_font=(FONT, -16)
    )
    general_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

    autoplay_box = customtkinter.CTkSwitch(
        master=general_frame,
        text="Autoplay",
        text_font=(FONT, -12),
        command=lambda: update_setting(
            "autoplay", True if autoplay_box.get() == 1 else False
        ),
    )
    autoplay_box.place(relx=0.28, rely=0.4, anchor=tkinter.CENTER)
    if autoplay == True:
        autoplay_box.select()
    else:
        pass

    rpc_box = customtkinter.CTkSwitch(
        master=general_frame,
        text="Discord RPC",
        text_font=(FONT, -12),
        command=lambda: update_setting("rpc", True if rpc_box.get() == 1 else False),
    )
    rpc_box.place(relx=0.31, rely=0.625, anchor=tkinter.CENTER)
    if rpc == True:
        rpc_box.select()
    else:
        pass

    preprocess_method_box = customtkinter.CTkSwitch(
        master=general_frame,
        text="Preprocess on Server?",
        text_font=(FONT, -12),
        command=lambda: update_setting(
            "preprocess_method",
            "'server'" if preprocess_method_box.get() == 1 else "'client'",
        ),
    )
    preprocess_method_box.place(relx=0.4, rely=0.85, anchor=tkinter.CENTER)
    if preprocess_method == "'server'" or preprocess_method == "server":
        preprocess_method_box.select()
    else:
        pass

    ### General Settings ###

    storage_frame = customtkinter.CTkFrame(master=settings_frame, width=300, height=125)
    storage_frame.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)

    storage_header = customtkinter.CTkLabel(
        master=storage_frame, text="Storage", text_font=(FONT, -16)
    )
    storage_header.place(relx=0.2, rely=0.15, anchor=tkinter.CENTER)

    downloads_header = customtkinter.CTkLabel(
        master=storage_frame, text="Downloads:", text_font=(FONT, -12, "bold")
    )
    downloads_header.place(relx=0.24, rely=0.4, anchor=tkinter.CENTER)

    downloads_info = customtkinter.CTkLabel(
        master=storage_frame,
        text=format_size(getsize(importsdest)),
        text_font=(FONT, -12),
        width=25,
        state=tkinter.DISABLED,
    )
    downloads_info.place(relx=0.45, rely=0.4, anchor=tkinter.CENTER)

    downloads_subheader = customtkinter.CTkLabel(
        master=storage_frame,
        text="Downloaded Content",
        text_font=(FONT, -11),
        state=tkinter.DISABLED,
    )
    downloads_subheader.place(relx=0.29, rely=0.55, anchor=tkinter.CENTER)

    clear_downloads_button = customtkinter.CTkButton(
        master=storage_frame,
        text="Clear Downloads",
        text_font=(FONT, -12),
        width=15,
        height=2,
        command=lambda: clear_downloads_window(importsdest, settings_window),
    )
    clear_downloads_button.place(relx=0.75, rely=0.475, anchor=tkinter.CENTER)

    storage_location_header = customtkinter.CTkLabel(
        master=storage_frame, text="Storage Location:", text_font=(FONT, -12, "bold")
    )
    storage_location_header.place(relx=0.305, rely=0.7, anchor=tkinter.CENTER)

    dir = os.path.abspath(importsdest)
    dirlen = len(dir)
    n = 20
    location_text = dir if dirlen <= n else "..." + dir[-(n - dirlen) :]

    storage_location_info = customtkinter.CTkLabel(
        master=storage_frame,
        text=location_text,
        text_font=(FONT, -11),
        width=25,
        state=tkinter.DISABLED,
    )
    storage_location_info.place(relx=0.345, rely=0.85, anchor=tkinter.CENTER)

    change_location_button = customtkinter.CTkButton(
        master=storage_frame,
        text="Change Location",
        text_font=(FONT, -12),
        width=15,
        height=2,
        command=lambda: change_location(),
    )
    change_location_button.place(relx=0.75, rely=0.775, anchor=tkinter.CENTER)

    theme_frame = customtkinter.CTkFrame(master=settings_window, width=350, height=380)
    theme_frame.place(relx=0.75, rely=0.47, anchor=tkinter.CENTER)

    theme_header = customtkinter.CTkLabel(
        master=theme_frame, text="Theme", text_font=(FONT, -18)
    )
    theme_header.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

    theme_frame_mini = customtkinter.CTkFrame(master=theme_frame, width=300, height=275)
    theme_frame_mini.place(relx=0.5, rely=0.55, anchor=tkinter.CENTER)

    button_light = customtkinter.CTkButton(
        master=theme_frame_mini,
        height=100,
        width=200,
        corner_radius=10,
        border_color="white",
        fg_color=light_theme,
        border_width=2,
        text="Light",
        hover_color=None,
        command=lambda: change_color_light(button_light),
    )
    button_light.place(relx=0.5, rely=0.25, anchor=tkinter.CENTER)

    button_dark = customtkinter.CTkButton(
        master=theme_frame_mini,
        height=100,
        width=200,
        corner_radius=10,
        border_color="white",
        fg_color=dark_theme,
        border_width=2,
        text="Dark",
        hover_color=None,
        command=lambda: change_color_dark(button_dark),
    )
    button_dark.place(relx=0.5, rely=0.75, anchor=tkinter.CENTER)

    info_label = customtkinter.CTkLabel(
        master=settings_window,
        text="Note: You must restart the app for changes to take effect.",
        text_font=(FONT, -12),
        state=tkinter.DISABLED,
        height=10,
    )
    info_label.place(relx=0.5, rely=0.95, anchor=tkinter.CENTER)

    reset_button = customtkinter.CTkButton(
        master=settings_window,
        text="Reset",
        text_font=(FONT, -12, "underline"),
        command=lambda: reset_settings(
            button_light, button_dark, rpc_box, autoplay_box, preprocess_method_box
        ),
        fg_color=settings_window.fg_color,
        hover_color=theme_frame.fg_color,
        width=15,
    )
    reset_button.place(relx=0.75, rely=0.95, anchor=tkinter.CENTER)

    goback_button = customtkinter.CTkButton(
        master=settings_window,
        text="",
        image=PhotoImage(
            file="./Assets/goback.png"
            if customtkinter.get_appearance_mode() == "Light"
            else "./Assets/goback_dark.png"
        ),
        text_font=(FONT, -12),
        command=lambda: settings_window.destroy(),
        fg_color=settings_window.fg_color,
        hover_color=theme_frame.fg_color,
        width=15,
    )
    goback_button.place(relx=0.25, rely=0.95, anchor=tkinter.CENTER)


## USER INTERFACE ----------------------------------------------------------------------------------------------------

FONT = "Roboto Medium"
north_frame = customtkinter.CTkFrame(master=app, width=350, height=100, corner_radius=8)
north_frame.place(relx=0.5, rely=0.13, anchor=tkinter.CENTER)

interface_frame = customtkinter.CTkFrame(
    master=app, width=175, height=100, corner_radius=8
)
interface_frame.place(relx=1, rely=0.13, anchor=tkinter.E)

center_frame = customtkinter.CTkFrame(
    master=app, width=350, height=200, corner_radius=8
)
center_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

south_frame = customtkinter.CTkFrame(master=app, width=350, height=100, corner_radius=8)
south_frame.place(relx=0.5, rely=0.87, anchor=tkinter.CENTER)

west_frame = customtkinter.CTkFrame(master=app, width=175, height=445, corner_radius=8)
west_frame.place(relx=0, rely=0.5, anchor=tkinter.W)

east_frame = customtkinter.CTkFrame(master=app, width=175, height=310, corner_radius=8)
east_frame.place(relx=1, rely=0.63, anchor=tkinter.E)

raise_above_all(app)

## INTERFACE ELEMENTS ------------------------------------------------------------------------------------------------


def resize_image(image, size):
    im = Image.open(f"./Assets/player/{image}")
    im = im.resize((size, size))
    im = im.save(f"./Assets/player/{image}")
    return f"./Assets/player/{image}"


interface_assets = os.listdir("./Assets/player")

playpause_button = customtkinter.CTkButton(
    master=interface_frame,
    image=PhotoImage(file=resize_image(interface_assets[0], 32)),
    command=lambda: playpause(),
    text="",
    width=32,
    height=32,
    fg_color=interface_frame.fg_color,
    hover_color=app.fg_color,
    state=tkinter.DISABLED,
)

next_button = customtkinter.CTkButton(
    master=interface_frame,
    image=PhotoImage(file=resize_image(interface_assets[4], 30)),
    command=lambda: next_song(songlabel.text),
    text="",
    width=30,
    height=30,
    fg_color=interface_frame.fg_color,
    hover_color=app.fg_color,
    state=tkinter.DISABLED,
)

previous_button = customtkinter.CTkButton(
    master=interface_frame,
    image=PhotoImage(file=resize_image(interface_assets[3], 30)),
    command=lambda: last_song(songlabel.text),
    text="",
    width=30,
    height=30,
    fg_color=interface_frame.fg_color,
    hover_color=app.fg_color,
    state=tkinter.DISABLED,
)

shuffle_button = customtkinter.CTkButton(
    master=interface_frame,
    image=PhotoImage(file=resize_image(interface_assets[2], 25)),
    command=lambda: shuffle(),
    text="",
    width=25,
    height=25,
    fg_color=interface_frame.fg_color,
    hover_color=app.fg_color,
)

repeat_button = customtkinter.CTkButton(
    master=interface_frame,
    image=PhotoImage(file=resize_image(interface_assets[6], 25)),
    command=lambda: loop_song(),
    text="",
    width=25,
    height=25,
    fg_color=interface_frame.fg_color,
    hover_color=app.fg_color,
)

playpause_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
next_button.place(relx=0.7, rely=0.5, anchor=tkinter.CENTER)
previous_button.place(relx=0.3, rely=0.5, anchor=tkinter.CENTER)
shuffle_button.place(relx=0.12, rely=0.5, anchor=tkinter.CENTER)
repeat_button.place(relx=0.88, rely=0.5, anchor=tkinter.CENTER)

## EAST FRAME ----------------------------------------------------------------------------------------------------

east_frame_title = customtkinter.CTkLabel(
    master=east_frame, text="Imported", text_font=(FONT, -16)
)
east_frame_title.place(relx=0.5, rely=0.08, anchor=tkinter.CENTER)

search_entry = customtkinter.CTkEntry(
    master=east_frame,
    width=150,
    height=25,
    placeholder_text="Search for audio",
)
search_entry.place(relx=0.5, rely=0.16, anchor=tkinter.CENTER)

listframe = customtkinter.CTkFrame(
    master=east_frame, width=150, height=175, corner_radius=8
)
listframe.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

songs_box = tkinter.Text(
    bd=0,
    bg=listframe.fg_color[1],
    fg="white",
    highlightthickness=0,
    borderwidth=0,
    master=listframe,
    width=16,
    height=11,
    font=(FONT, -12),
)
songs_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
songs_box.configure(state=tkinter.DISABLED)

index_entry = customtkinter.CTkEntry(
    master=east_frame,
    width=150,
    height=25,
    placeholder_text="Enter index of audio",
)
index_entry.place(relx=0.5, rely=0.84, anchor=tkinter.CENTER)

playbutton = customtkinter.CTkButton(
    master=east_frame,
    text="Play",
    width=150,
    height=25,
    command=lambda: play_search(index_entry.get(), os.listdir(importsdest)),
)
playbutton.place(relx=0.5, rely=0.93, anchor=tkinter.CENTER)

east_checks = threading.Thread(target=global_checks, args=(search_entry, songs_box))
east_checks.daemon = True
east_checks.start()

## WEST FRAME ----------------------------------------------------------------------------------------------------

logolabel = customtkinter.CTkLabel(
    master=west_frame, text=f"MISST {version}", text_font=(FONT, -16)
)
logolabel.place(relx=0.5, rely=0.12, anchor=tkinter.CENTER)

themelabel = customtkinter.CTkLabel(master=west_frame, text="Appearance Mode:")
themelabel.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

thememenu = customtkinter.CTkOptionMenu(
    master=west_frame,
    values=["System", "Dark", "Light"],
    command=change_theme,
)
thememenu.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

settings_button = customtkinter.CTkButton(
    master=west_frame,
    text_font=(FONT, -12),
    text="",
    image=PhotoImage(file=f"./Assets/settings.png"),
    bg_color=west_frame.fg_color,
    fg_color=west_frame.fg_color,
    hover_color=app.fg_color,
    width=25,
    height=25,
    command=lambda: settings(),
)
settings_button.place(relx=0.3, rely=0.9, anchor=tkinter.CENTER)

refresh_button = customtkinter.CTkButton(
    master=west_frame,
    text_font=(FONT, -12),
    text="",
    image=PhotoImage(file=f"./Assets/reload.png"),
    bg_color=west_frame.fg_color,
    fg_color=west_frame.fg_color,
    hover_color=app.fg_color,
    width=25,
    height=25,
    command=lambda: threading.Thread(target=refresh, daemon=True).start(),
)
refresh_button.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

lyrics = customtkinter.CTkButton(
    master=west_frame,
    text_font=(FONT, -12),
    text="",
    image=PhotoImage(file=f"./Assets/lyrics.png"),
    bg_color=west_frame.fg_color,
    fg_color=west_frame.fg_color,
    hover_color=app.fg_color,
    width=25,
    height=25,
    corner_radius=16,
    command=lambda: threading.Thread(target=lyrics_window, daemon=True).start(),
)
lyrics.place(relx=0.7, rely=0.9, anchor=tkinter.CENTER)

## NORTH FRAME ----------------------------------------------------------------------------------------------------

songlabel = customtkinter.CTkButton(
    master=north_frame,
    text=f"(song name)",
    width=240,
    height=50,
    text_font=(FONT, -14),
    command=lambda: threading.Thread(target=lyrics_window, daemon=True).start(),
    fg_color=north_frame.fg_color,
    hover_color=app.fg_color,
)
songlabel.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

progressbar = customtkinter.CTkProgressBar(master=north_frame, width=225, height=10)
progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
progressbar.set(0)

progress_label_left = customtkinter.CTkLabel(
    master=north_frame, text="0:00", text_font=(FONT, -12), width=50
)
progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

progress_label_right = customtkinter.CTkLabel(
    master=north_frame, text="0:00", text_font=(FONT, -12), width=50
)
progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

## CENTER FRAME ----------------------------------------------------------------------------------------------------

checkbox1 = customtkinter.CTkCheckBox(
    master=center_frame,
    text="bass",
    command=lambda: checkbox_event(check_var1, bass, slider1),
    variable=check_var1,
    onvalue="on",
    offvalue="off",
)
checkbox1.place(relx=0.1, rely=0.2, anchor=tkinter.W)

checkbox2 = customtkinter.CTkCheckBox(
    master=center_frame,
    text="drums",
    command=lambda: checkbox_event(check_var2, drums, slider2),
    variable=check_var2,
    onvalue="on",
    offvalue="off",
)
checkbox2.place(relx=0.1, rely=0.35, anchor=tkinter.W)

checkbox3 = customtkinter.CTkCheckBox(
    master=center_frame,
    text="other",
    command=lambda: checkbox_event(check_var3, other, slider3),
    variable=check_var3,
    onvalue="on",
    offvalue="off",
)
checkbox3.place(relx=0.1, rely=0.5, anchor=tkinter.W)

checkbox4 = customtkinter.CTkCheckBox(
    master=center_frame,
    text="vocals",
    command=lambda: checkbox_event(check_var4, vocals, slider4),
    variable=check_var4,
    onvalue="on",
    offvalue="off",
)
checkbox4.place(relx=0.1, rely=0.65, anchor=tkinter.W)

slider1 = customtkinter.CTkSlider(
    master=center_frame,
    from_=0,
    to=1,
    command=lambda x: slider_event(x, bass, checkbox1),
    number_of_steps=10,
)
slider1.place(relx=0.6, rely=0.2, anchor=tkinter.CENTER)

slider2 = customtkinter.CTkSlider(
    master=center_frame,
    from_=0,
    to=1,
    command=lambda x: slider_event(x, drums, checkbox2),
    number_of_steps=10,
)
slider2.place(relx=0.6, rely=0.35, anchor=tkinter.CENTER)

slider3 = customtkinter.CTkSlider(
    master=center_frame,
    from_=0,
    to=1,
    command=lambda x: slider_event(x, other, checkbox3),
    number_of_steps=10,
)
slider3.place(relx=0.6, rely=0.5, anchor=tkinter.CENTER)

slider4 = customtkinter.CTkSlider(
    master=center_frame,
    from_=0,
    to=1,
    command=lambda x: slider_event(x, vocals, checkbox4),
    number_of_steps=10,
)
slider4.place(relx=0.6, rely=0.65, anchor=tkinter.CENTER)

nc_checkbox = customtkinter.CTkSwitch(
    master=center_frame,
    text="nightcore",
    command=lambda: threading.Thread(
        target=nightcore, daemon=True, args=(songlabel,)
    ).start(),
    variable=nc_var,
    onvalue="on",
    offvalue="off",
)
nc_checkbox.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
nc_checkbox.configure(state=tkinter.DISABLED)

## SOUTH FRAME ----------------------------------------------------------------------------------------------------

import_button = customtkinter.CTkButton(
    master=south_frame,
    command=import_,
    image=PhotoImage(file=f"./Assets/import.png"),
    fg_color=south_frame.fg_color,
    hover_color=app.fg_color,
    text="Import Song(s)",
    text_font=(FONT, -14),
)
import_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

## STARTUP ----------------------------------------------------------------------------------------------------

update_rpc(Ltext="Idle", Dtext="Nothing is playing")
app.mainloop()
