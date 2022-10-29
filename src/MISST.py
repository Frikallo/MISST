## LICENSE ----------------------------------------------------------------------------------------------------

# MISST 2.0.2
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

import pygame
import datetime
from scipy.io import wavfile
import threading
import customtkinter
import tkinter
from tkinter import PhotoImage, filedialog
import nightcore as nc
import webbrowser
import logging
import os
import time
from Assets.clientsecrets import (
    client_id,
    genius_access_token,
    server_base,
    importsdest,
)
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

## LOGGER ----------------------------------------------------------------------------------------------------

loggerName = "MISST"
logFormatter = logging.Formatter(fmt=" %(name)s :: %(levelname)-8s :: %(message)s")
logger = logging.getLogger(loggerName)
logger.setLevel(logging.DEBUG)

logging.basicConfig(
    filename="MISST.log",
    filemode="a",
    format=" %(name)s :: %(levelname)-8s :: %(message)s",
    level=logging.DEBUG,
)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)
logger.info(f'Logger initialized ({str(datetime.datetime.now()).split(".")[0]})')

# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warn message')
# logger.error('error message')
# logger.critical('critical message')

## GLOBAL VARIABLES ----------------------------------------------------------------------------------------------------

version = "V2.0.2"
discord_rpc = client_id
genius_access_token = genius_access_token
CREATE_NO_WINDOW = 0x08000000
GENIUS = True

demucs_post = f"{server_base}/demucs-upload"
demucs_get = f"{server_base}/download"
demucs_queue = f"{server_base}/queue"

## INIT ----------------------------------------------------------------------------------------------------

nest_asyncio.apply()
gc.enable()
pygame.mixer.init()
pygame.mixer.set_num_channels(10)

try:
    genius_object = lg.Genius(genius_access_token)
except:
    GENIUS = False
    logger.error("connection failed")

RPC = Presence(discord_rpc)
try:
    RPC.connect()
    logger.info("Connected to Discord")
    RPC_CONNECTED = True
except:
    RPC_CONNECTED = False
    logger.error("RPC connection failed")

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


internet_connection = checkInternetUrllib()

if not os.path.exists(importsdest):
    os.mkdir(importsdest)

if os.path.exists("./dl-songs"):
    shutil.rmtree("./dl-songs")
    logger.info("dl-songs folder deleted")

## APP CONFIG ----------------------------------------------------------------------------------------------------

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: "blue" (standard), "green", "dark-blue"

app = customtkinter.CTk()
app.title("MISST")
app.iconbitmap(r"./icon.ico")

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


def get_lyrics():
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
        if GENIUS == True:
            songartist = songlabel.text.split(" - ")
            song = songartist[1]
            artist = songartist[0]
            song = genius_object.search_song(title=song, artist=artist)
            lyrics = song.lyrics
        else:
            lyrics = "Internet connection is not available"
        window = customtkinter.CTkToplevel(app)
        window.geometry("580x435")
        window.title("MISST")
        window.iconbitmap(r"./icon.ico")
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
    import_window.iconbitmap(r"./icon.ico")

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
        command=lambda: import_fun2(spot_importEntry.get(), status_label),
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

    playlistdlthread = threading.Thread(
        target=import_fun4,
        args=(spot_PlaylistimportEntry.get(), status_label),
    )
    playlistdlthread.daemon = True

    spot_Playlistimport = customtkinter.CTkButton(
        master=song_frame,
        text="Import from Spotify",
        width=150,
        height=25,
        command=lambda: playlistdlthread.start(),
    )
    spot_Playlistimport.place(relx=0.77, rely=0.85, anchor=tkinter.CENTER)

    if server_connection == True:
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
        return
    if not url.startswith("https://open.spotify.com/track/"):
        status_label.configure(text=f"")
        status_label.configure(text=f"Invalid url")
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
                text="Done! {} songs imported \n(results can be found {}/separated)".format(
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


def import_fun4(url, status_label):
    if url == "":
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="No url provided",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return
    if not url.startswith("https://open.spotify.com/playlist/"):
        errorlabel = customtkinter.CTkLabel(
            master=status_label.master,
            text="Invalid url",
            text_font=(FONT, -14),
            width=200,
        )
        errorlabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
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
            text="Done! {} songs imported \n(results can be found {}/separated)".format(
                len(os.listdir("./dl-songs")), os.getcwd()
            ),
            text_font=(FONT, -14),
            width=200,
        )
        donelabel.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return


## UTIL FUNCTIONS ----------------------------------------------------------------------------------------------------


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


def update_rpc(Ltext=None, Dtext=None):
    start_time = time.time()
    if RPC_CONNECTED:
        try:
            RPC.update(
                large_image="misst",
                start=start_time,
                large_text="MISST",
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
        cover_art = ImageTk.PhotoImage(get_album_art(song_dir))
    except:
        cover_art = ImageTk.PhotoImage(Image.open("./assets/default.png"))
    songlabel.configure(text=song_name, image=cover_art)
    update_rpc(Ltext="Listening to seperated audio", Dtext=song_name)
    nc_checkbox.configure(state="normal")
    label = tkinter.Label(image=cover_art)
    label.image = cover_art
    label.place(relx=2, rely=2, anchor=tkinter.CENTER)
    sample_rate, audio_data = wavfile.read(song)
    duration = audio_data.shape[0] / sample_rate
    t = 0

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

    for _ in os.listdir(importsdest + "/" + song_name):
        if _.endswith("_nc.wav"):
            os.remove(importsdest + "/" + song_name + "/" + _)
    while True:
        if songlabel.text == "":
            progressbar.set(0)
            songlabel.configure(text="(song name)", image=None)
            progress_label_left.configure(text="0:00")
            progress_label_right.configure(text="0:00")
            update_rpc(Ltext="Idle", Dtext="Nothing is playing")
            nc_checkbox.configure(state=tkinter.DISABLED)
            break
        if songlabel.text != song_name:
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
    return


def spot_dl(url, status_label):
    if os.path.exists("./dl-songs"):
        pass
    else:
        os.mkdir("./dl-songs")
    try:
        spotdl = os.path.abspath("./spotdl.exe")
        cmd = subprocess.call(
            f"{spotdl} download {url} --output ./dl-songs",
            creationflags=CREATE_NO_WINDOW,
        )
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


def spot_dl_playlist(url, status_label):
    if os.path.exists("./dl-songs"):
        pass
    else:
        os.mkdir("./dl-songs")
    try:
        spotdl = os.path.abspath("./spotdl.exe")
        cmd = subprocess.call(
            f"{spotdl} download {url} --output ./dl-songs",
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
    songname = os.path.basename(abspath_song).replace(" ", "%20")

    try:
        status_update(status_label, "In Queue")
        requests.post(demucs_queue)
        status_update(status_label, "Preprocessing")
        requests.post(demucs_post, files={"file": open(abspath_song, "rb")})
        logger.info("preprocessed")
        subprocess.run(
            f'curl "{demucs_get}/{songname}.zip" -o "{songname.replace("%20", " ")}.zip"',
            creationflags=CREATE_NO_WINDOW,
            check=True,
        )
        logger.info("downloaded")
        songname = songname.replace("%20", " ")
        savename = songname.replace(".mp3", "")
        shutil.unpack_archive(f"{songname}.zip", f"{importsdest}/{savename}")
        logger.info("unpacked")
        os.remove(f"{songname}.zip")
    except:
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
        play_song(f"{importsdest}/{savename}")
    except:
        logger.error("No metadata found")
        shutil.copyfile("./Assets/default.png", f"{importsdest}/{savename}/cover.png")
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
    return


def preprocessmultiple(abspath_song, status_label):
    songname = os.path.basename(abspath_song).replace(" ", "%20")
    try:
        requests.post(demucs_queue)
        requests.post(demucs_post, files={"file": open(abspath_song, "rb")})
        logger.info("preprocessed")
        subprocess.run(
            f'curl "{demucs_get}/{songname}.zip" -o "{songname.replace("%20", " ")}.zip"',
            creationflags=CREATE_NO_WINDOW,
            check=True,
        )
        logger.info("downloaded")
        songname = songname.replace("%20", " ")
        savename = songname.replace(".mp3", "")
        shutil.unpack_archive(f"{songname}.zip", f"{importsdest}/{savename}")
        logger.info("unpacked")
        os.remove(f"{songname}.zip")
    except:
        logger.error("Preprocessing failed")
        error_label = customtkinter.CTkLabel(
            status_label.master,
            text="Preprocessing failed",
            text_font=(FONT, -14),
            width=200,
        )
        error_label.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        return


def play_song(parent_dir, nightcore=False):

    end = ".wav"
    if nightcore == True:
        end = "_nc.wav"

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


def get_album_art(abspathsong):
    try:
        im = Image.open(f"{abspathsong}/cover.png")
        im = im.resize((40, 40))
    except Exception as e:
        logger.error(f"Error getting album art: {e}")
        return None
    return im


def global_checks(search_entry, lyric_box):
    server_connection = False
    entry_val = None
    num = 0
    songs = []
    for _ in os.listdir(importsdest):
        num += 1
        songs.append(f"{num}. {_}")
    while True:
        time.sleep(0.5)
        if server_connection == False:
            threading.Thread(target=server_status).start()
        if len(os.listdir(importsdest)) != num:
            num = 0
            songs = []
            for _ in os.listdir(importsdest):
                num += 1
                songs.append(f"{num}. {_}")
        lyric_box.configure(
            bg=lyric_box.master.fg_color[
                1 if customtkinter.get_appearance_mode() == "Dark" else 0
            ],
            fg="white" if customtkinter.get_appearance_mode() == "Dark" else "black",
        )
        if len(songs) == 0:
            lyric_box.configure(state="normal")
            lyric_box.delete("1.0", tkinter.END)
            lyric_box.insert(tkinter.END, "No songs Imported!")
            lyric_box.configure(state=tkinter.DISABLED)
        search = search_entry.get()
        found_songs = []
        for _ in songs:
            if search.lower() in _.lower():
                found_songs.append(_)
        if entry_val == search_entry.get():
            pass
        else:
            lyric_box.configure(state="normal")
            lyric_box.delete("1.0", tkinter.END)
            lyric_box.insert(tkinter.END, "\n\n".join(found_songs))
            lyric_box.configure(state=tkinter.DISABLED)
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


def nightcore(song, tones=3):
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
        return None
    if value == "off":
        if song.text == "":
            return None
        play_song(os.path.abspath(os.path.join(importsdest, song.text)))
        return None


## USER INTERFACE ----------------------------------------------------------------------------------------------------

FONT = "Roboto Medium"
north_frame = customtkinter.CTkFrame(master=app, width=350, height=100, corner_radius=8)
north_frame.place(relx=0.5, rely=0.13, anchor=tkinter.CENTER)

center_frame = customtkinter.CTkFrame(
    master=app, width=350, height=200, corner_radius=8
)
center_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

south_frame = customtkinter.CTkFrame(master=app, width=350, height=100, corner_radius=8)
south_frame.place(relx=0.5, rely=0.87, anchor=tkinter.CENTER)

west_frame = customtkinter.CTkFrame(master=app, width=175, height=445, corner_radius=8)
west_frame.place(relx=0, rely=0.5, anchor=tkinter.W)

east_frame = customtkinter.CTkFrame(master=app, width=175, height=445, corner_radius=8)
east_frame.place(relx=1, rely=0.5, anchor=tkinter.E)

raise_above_all(app)

## EAST FRAME ----------------------------------------------------------------------------------------------------

east_frame_title = customtkinter.CTkLabel(
    master=east_frame, text="Imported", text_font=(FONT, -16)
)
east_frame_title.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

search_entry = customtkinter.CTkEntry(
    master=east_frame,
    width=150,
    height=25,
    placeholder_text="Search for audio",
)
search_entry.place(relx=0.5, rely=0.17, anchor=tkinter.CENTER)

listframe = customtkinter.CTkFrame(
    master=east_frame, width=150, height=250, corner_radius=8
)
listframe.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

lyric_box = tkinter.Text(
    bd=0,
    bg=listframe.fg_color[1],
    fg="white",
    highlightthickness=0,
    borderwidth=0,
    master=listframe,
    width=16,
    height=16,
    font=(FONT, -12),
)
lyric_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
lyric_box.configure(state=tkinter.DISABLED)

index_entry = customtkinter.CTkEntry(
    master=east_frame,
    width=150,
    height=25,
    placeholder_text="Enter index of audio",
)
index_entry.place(relx=0.5, rely=0.83, anchor=tkinter.CENTER)

playbutton = customtkinter.CTkButton(
    master=east_frame,
    text="Play",
    width=150,
    height=25,
    command=lambda: play_search(index_entry.get(), os.listdir(importsdest)),
)
playbutton.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

east_checks = threading.Thread(target=global_checks, args=(search_entry, lyric_box))
east_checks.daemon = True
east_checks.start()

## WEST FRAME ----------------------------------------------------------------------------------------------------

logolabel = customtkinter.CTkLabel(
    master=west_frame, text=f"MISST {version}", text_font=(FONT, -16)
)
logolabel.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

themelabel = customtkinter.CTkLabel(master=west_frame, text="Appearance Mode:")
themelabel.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

thememenu = customtkinter.CTkOptionMenu(
    master=west_frame,
    values=["System", "Dark", "Light"],
    command=change_theme,
)
thememenu.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

github_button = customtkinter.CTkButton(
    master=west_frame,
    image=PhotoImage(file="./Assets/github.png"),
    command=lambda: webbrowser.open("https://github.com/Frikallo/MISST", new=2),
    text="",
    width=25,
    height=25,
    fg_color=west_frame.fg_color,
    hover_color=west_frame.fg_color,
)
profile_button = customtkinter.CTkButton(
    master=west_frame,
    image=PhotoImage(file="./Assets/profile.png"),
    command=lambda: webbrowser.open("https://github.com/Frikallo", new=2),
    text="",
    width=25,
    height=25,
    fg_color=west_frame.fg_color,
    hover_color=west_frame.fg_color,
)

profile_button.place(relx=0.6, rely=0.17, anchor=tkinter.CENTER)
github_button.place(relx=0.4, rely=0.17, anchor=tkinter.CENTER)

back_button = customtkinter.CTkButton(
    master=west_frame,
    text=f"<--",
    command=lambda: print("back"),
    corner_radius=0,
    width=75,
    fg_color=west_frame.fg_color,
    hover_color=app.fg_color,
    state=tkinter.DISABLED,
)
back_button.place(relx=0.3, rely=0.9, anchor=tkinter.CENTER)

forward_button = customtkinter.CTkButton(
    master=west_frame,
    text=f"-->",
    command=lambda: print("forward"),
    corner_radius=0,
    width=75,
    fg_color=west_frame.fg_color,
    hover_color=app.fg_color,
    state=tkinter.DISABLED,
)
forward_button.place(relx=0.7, rely=0.9, anchor=tkinter.CENTER)

## NORTH FRAME ----------------------------------------------------------------------------------------------------

songlabel = customtkinter.CTkButton(
    master=north_frame,
    text=f"(song name)",
    width=240,
    height=50,
    text_font=(FONT, -14),
    command=lambda: threading.Thread(target=get_lyrics, daemon=True).start(),
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
