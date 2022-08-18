import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
import datetime
from scipy.io import wavfile
import threading
import customtkinter
import tkinter
from tkinter import filedialog
import os
import time
from clientsecrets import client_id, genius_access_token
import lyricsgenius as lg
from pypresence import Presence
import time
import nest_asyncio

nest_asyncio.apply()
import gc

gc.enable()

pygame.mixer.init()
pygame.mixer.set_num_channels(10)

discord_rpc = client_id
genius_access_token = genius_access_token

GENIUS = True
try:
    genius_object = lg.Genius(genius_access_token)
except:
    GENIUS = False
    print('connection failed')

RPC = Presence(discord_rpc)
try:
    RPC.connect()
    print("Connected to Discord")
    RPC_CONNECTED = True
except:
    RPC_CONNECTED = False
    print("RPC connection failed")


def play_thread(sound, channel):
    timestamp = 0
    thread = pygame.mixer.Sound(sound)
    sample_rate, audio_data = wavfile.read(sound)
    duration = audio_data.shape[0] / sample_rate
    progressbar = customtkinter.CTkProgressBar(
        master=timestamp_frame, width=225, height=10
    )
    progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
    progressbar.set(0)
    progress_label_left = customtkinter.CTkLabel(
        master=timestamp_frame, text="0:00", text_font=("Roboto Medium", -12), width=50
    )
    progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)
    progress_label_right = customtkinter.CTkLabel(
        master=timestamp_frame, text="0:00", text_font=("Roboto Medium", -12), width=50
    )
    progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)
    while True:
        try:
            pygame.mixer.Channel(channel).play(thread)
            del thread
            gc.collect()
        except:
            print("done")
            label.configure(text="(song name)")
            progressbar.set(0)
            progress_label_left.configure(text="0:00")
            progress_label_right.configure(text="0:00")
            try:
                RPC.update(
                    large_image="kanye",
                    start=start_time,
                    large_text="SUCK MY NUTS KANYE",
                    state="Exploring The Client",
                )
            except:
                return
            return
        while pygame.mixer.get_busy():
            pygame.time.delay(100)
            if pygame.mixer.Channel(channel).get_busy() == True:
                try:
                    time.sleep(1)
                    timestamp += 1
                    timestamp_percent = timestamp / duration
                    progressbar.set(timestamp_percent)
                    left = str(datetime.timedelta(seconds=int(timestamp)))
                    left = left[2:]
                    right = str(datetime.timedelta(seconds=int(duration - timestamp)))
                    right = right[2:]
                    progress_label_left.configure(text=left)
                    progress_label_right.configure(text=right)
                except:
                    return


bass = pygame.mixer.Channel(0)
drums = pygame.mixer.Channel(1)
other = pygame.mixer.Channel(2)
vocals = pygame.mixer.Channel(3)

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.title("SUCK MY NUTS KANYE")
app.iconbitmap(r"./icon.ico")
geometry = "580x435"
app.geometry(geometry)

check_var1 = tkinter.StringVar(value="on")
check_var2 = tkinter.StringVar(value="on")
check_var3 = tkinter.StringVar(value="on")
check_var4 = tkinter.StringVar(value="on")


def preprocess_song():
    os.system(f'python3 -m demucs "{abspath_song}"')
    label2.configure(text="Playing...")
    song = os.path.basename(abspath_song).replace(".mp3", "")
    label.configure(text=f"{song}", width=240, height=50)
    thread1 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/bass.wav", 0)
    )  #
    thread2 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/drums.wav", 1)
    )  #
    thread3 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/other.wav", 2)
    )  #
    thread4 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/vocals.wav", 3)
    )  #
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    try:
        RPC.update(
            large_image="kanye",
            start=start_time,
            large_text="SUCK MY NUTS KANYE",
            state="Listening to seperated audio",
            details=f"{song}",
        )
    except:
        pass
    if window:
        window.destroy()
    del song
    del thread1
    del thread2
    del thread3
    del thread4
    gc.collect


def button_event1():
    global window
    window = customtkinter.CTkToplevel(app)
    window.geometry("400x200")
    window.title("SUCK MY NUTS KANYE")
    window.iconbitmap(r"./icon.ico")

    global playlist_frame
    playlist_frame = customtkinter.CTkFrame(window, width=350, height=150)
    playlist_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    playlist_button1 = customtkinter.CTkButton(
        master=playlist_frame,
        text="Import from Spotify",
        width=150,
        height=25,
        command=isong_1,
    )
    playlist_button1.place(relx=0.23, rely=0.45, anchor=tkinter.CENTER)

    global playlist_input1
    playlist_input1 = customtkinter.CTkEntry(
        master=playlist_frame, width=150, height=25, placeholder_text="Enter song url",
    )
    playlist_input1.place(relx=0.23, rely=0.65, anchor=tkinter.CENTER)

    playlist_button2 = customtkinter.CTkButton(
        master=playlist_frame,
        text="Import from .mp3",
        width=150,
        height=25,
        command=isong_2,
    )
    playlist_button2.place(relx=0.72, rely=0.5, anchor=tkinter.CENTER)

    global status_label
    status_label = customtkinter.CTkLabel(
        master=playlist_frame, text=" ", width=150, height=25
    )
    status_label.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)


def download_pp_song(url):
    os.mkdir("./dl-songs")
    try:
        os.system(f"python -m spotdl {url} -o ./dl-songs")
    except:
        print("Download failed")
        status_label.configure(text=f"Link is invalid")
        return
    status_label.configure(text=f"Preprocessing... Can take 10-15 seconds")
    for i in os.listdir("./dl-songs"):
        if i.endswith(".mp3"):
            abspath_song = os.path.join("./dl-songs", i)
            break
    os.system(f'python3 -m demucs "{abspath_song}"')
    for i in os.listdir("./dl-songs"):
        os.remove(os.path.join("./dl-songs", i))
    os.rmdir("./dl-songs")
    label2.configure(text="Playing...")
    song = os.path.basename(abspath_song).replace(".mp3", "")
    label.configure(text=f"{song}", width=240, height=50)
    thread1 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/bass.wav", 0)
    )  #
    thread2 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/drums.wav", 1)
    )  #
    thread3 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/other.wav", 2)
    )  #
    thread4 = threading.Thread(
        target=play_thread, args=(f"./separated/mdx_extra_q/{song}/vocals.wav", 3)
    )  #
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    try:
        RPC.update(
            large_image="kanye",
            start=start_time,
            large_text="SUCK MY NUTS KANYE",
            state="Listening to seperated audio",
            details=f"{song}",
        )
    except:
        pass
    window.destroy()
    del thread1
    del thread2
    del thread3
    del thread4
    del song
    del i
    gc.collect


def isong_1():
    url = playlist_input1.get()
    if url == "":
        return
    if not url.startswith("https://open.spotify.com/track/"):
        status_label.configure(text=f"Invalid url")
        return
    status_label.configure(text=f"Downloading... Can take 5-10 seconds")
    thread = threading.Thread(target=download_pp_song, args=(url,))
    thread.start()


def isong_2():
    # unseperated_song
    global abspath_song
    abspath_song = filedialog.askopenfilename(
        filetypes=(("Audio Files (*.mp3)", ".mp3"), ("All Files", "*.*"))
    )
    print(abspath_song)
    if abspath_song == "":
        return
    label2.configure(text=f"Preprocessing... Can take 10-15 seconds")
    thread = threading.Thread(target=preprocess_song)
    thread.start()


def button_event2():
    # preseparated_song
    label2.configure(text=" ")
    varpath = filedialog.askdirectory()
    if varpath == "":
        return
    thread1 = threading.Thread(target=play_thread, args=(f"{varpath}/bass.wav", 0))  #
    thread2 = threading.Thread(target=play_thread, args=(f"{varpath}/drums.wav", 1))  #
    thread3 = threading.Thread(target=play_thread, args=(f"{varpath}/other.wav", 2))  #
    thread4 = threading.Thread(target=play_thread, args=(f"{varpath}/vocals.wav", 3))  #
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    song = os.path.basename(varpath)
    label.configure(text=f"{song}")
    try:
        RPC.update(
            large_image="kanye",
            start=start_time,
            large_text="SUCK MY NUTS KANYE",
            state="Listening to seperated audio",
            details=f"{song}",
        )
    except:
        pass


def button_event3():

    global frame_left_copy
    global frame_info
    global info_songs
    global input_box
    global play_button
    global back_button

    label2.configure(text=" ")
    global folder
    folder = filedialog.askdirectory()
    if folder == "":
        return
    frame_left_copy = customtkinter.CTkFrame(
        master=app, width=175, height=445, corner_radius=8
    )
    frame_left_copy.place(relx=0, rely=0.5, anchor=tkinter.W)
    frame_info = customtkinter.CTkFrame(
        master=frame_left_copy, width=150, height=320, corner_radius=8
    )
    frame_info.place(relx=0.5, rely=0.1, anchor=tkinter.N)
    n = 0
    global songs
    songs = []
    global song_names_valid
    song_names_valid = ""
    for file in os.listdir(folder):
        n += 1
        songs.append(f"{n}. {file}")
        song_names_valid += f"{file}\n"

    global info_songs
    info_songs = customtkinter.CTkTextbox(master=frame_info, width=150, height=310, text_font=("Roboto Medium", -12))
    info_songs.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    info_songs.insert(tkinter.END, "\n\n".join(songs))

    global input_box
    input_box = customtkinter.CTkEntry(
        master=frame_left_copy,
        width=150,
        height=25,
        placeholder_text="Enter index of song",
    )
    input_box.place(relx=0.5, rely=0.885, anchor=tkinter.S)

    global search_entry
    search_entry = customtkinter.CTkEntry(
        master=frame_left_copy,
        width=150,
        height=25,
        placeholder_text="Search for song",
    )
    search_entry.place(relx=0.5, rely=0.035, anchor=tkinter.N)

    play_button = customtkinter.CTkButton(
        master=frame_left_copy, text="Play", width=100, height=25, command=button_event4
    )
    play_button.place(relx=0.65, rely=0.95, anchor=tkinter.S)

    back_button = customtkinter.CTkButton(
        master=frame_left_copy, text="<--", width=50, height=25, command=button_event8
    )
    back_button.place(relx=0.21, rely=0.95, anchor=tkinter.S)


def button_event4():
    label2.configure(text=" ")
    index = input_box.get()
    songs = song_names_valid.split("\n")
    song = songs[int(index) - 1]
    thread1 = threading.Thread(
        target=play_thread, args=(f"{folder}/{song}/bass.wav", 0)
    )  #
    thread2 = threading.Thread(
        target=play_thread, args=(f"{folder}/{song}/drums.wav", 1)
    )  #
    thread3 = threading.Thread(
        target=play_thread, args=(f"{folder}/{song}/other.wav", 2)
    )  #
    thread4 = threading.Thread(
        target=play_thread, args=(f"{folder}/{song}/vocals.wav", 3)
    )  #
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    label.configure(text=f"{song}")
    try:
        RPC.update(
            large_image="kanye",
            start=start_time,
            large_text="SUCK MY NUTS KANYE",
            state="Listening to seperated audio",
            details=f"{song}",
        )
    except:
        pass


def button_event5():
    window = customtkinter.CTkToplevel(app)
    window.geometry("400x200")
    window.title("SUCK MY NUTS KANYE")
    window.iconbitmap(r"./icon.ico")

    global playlist_frame
    playlist_frame = customtkinter.CTkFrame(window, width=350, height=150)
    playlist_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    playlist_button1 = customtkinter.CTkButton(
        master=playlist_frame,
        text="Import from Spotify",
        width=150,
        height=25,
        command=button_event6,
    )
    playlist_button1.place(relx=0.23, rely=0.45, anchor=tkinter.CENTER)

    global playlist_input1
    playlist_input1 = customtkinter.CTkEntry(
        master=playlist_frame,
        width=150,
        height=25,
        placeholder_text="Enter playlist url",
    )
    playlist_input1.place(relx=0.23, rely=0.65, anchor=tkinter.CENTER)

    playlist_button2 = customtkinter.CTkButton(
        master=playlist_frame,
        text="Import from folder of *.mp3's",
        width=150,
        height=25,
        command=button_event7,
    )
    playlist_button2.place(relx=0.72, rely=0.5, anchor=tkinter.CENTER)


def pp_playlist():
    for i in os.listdir(songs_path):
        i = f"{songs_path}/{i}"
        if i.endswith(".mp3"):
            os.system(f'python3 -m demucs "{os.path.abspath(i)}"')
    end = time.time() - start
    print(f"Time taken: {end/60}")
    status_label.configure(text=f"Done! Separated songs can be found in ./separated")
    del end  # delete end to prevent memory leak
    del i  # delete i to prevent memory leak
    gc.collect()  # garbage collection


def dl_playlist(url):
    global start
    start = time.time()
    playlist_name = url.split("/")[-1]
    playlist_name = playlist_name.split("?")[0]
    playlist_name = playlist_name.split(".")[0]
    playlist_name = playlist_name.replace("=", "")
    os.mkdir(f"./songs_from_{playlist_name}")
    os.chdir(f"./songs_from_{playlist_name}")
    os.system(f"python -m spotdl {url}")
    os.chdir("..")
    status_label.configure(text="Downloaded!")
    time.sleep(1)
    status_label.configure(text="Preprocessing... (can take 5-10mins)")
    time.sleep(1)
    global songs_path
    songs_path = os.path.abspath(f"./songs_from_{playlist_name}")
    threadpp = threading.Thread(target=pp_playlist)
    threadpp.start()
    del threadpp  # delete threadpp to prevent memory leak
    del songs_path
    del playlist_name
    del start
    gc.collect()  # garbage collection


def button_event6():
    spotify_url = playlist_input1.get()
    print(spotify_url)
    global status_label
    status_label = customtkinter.CTkLabel(
        master=playlist_frame, text="Downloading playlist...", width=150, height=25
    )
    status_label.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
    threaddl = threading.Thread(target=dl_playlist, args=(spotify_url,))
    threaddl.start()


def pp_folder():
    for i in os.listdir(songs_path):
        i = f"{songs_path}/{i}"
        if i.endswith(".mp3"):
            os.system(f'python3 -m demucs "{os.path.abspath(i)}"')
    status_label.configure(text=f"Done! Separated songs can be found in ./separated")
    del i  # delete i to prevent memory leak
    gc.collect()  # garbage collection


def button_event7():
    folder = filedialog.askdirectory()
    if folder == "":
        return
    global songs_path
    songs_path = os.path.abspath(folder)
    print(songs_path)
    global status_label
    status_label = customtkinter.CTkLabel(
        master=playlist_frame,
        text="Preprocessing... (can take 5-10mins)",
        width=150,
        height=25,
    )
    status_label.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)
    threadpp = threading.Thread(target=pp_folder)
    threadpp.start()


def button_event8():
    frame_left_copy.destroy()
    frame_info.destroy()
    info_songs.destroy()
    input_box.destroy()
    play_button.destroy()
    back_button.destroy()

window = None
def button_event9():
    global window
    try:
        window.destroy()
    except:
        pass
    try:
        if GENIUS == True:
            songartist = label.text.split(" - ")
            song = songartist[0]
            artist = songartist[1]
            song = genius_object.search_song(title =song, artist =artist)
            lyrics = song.lyrics
        else:
            lyrics = 'Internet connection is not available'
        window = customtkinter.CTkToplevel(app)
        window.geometry("580x435")
        window.title("SUCK MY NUTS KANYE")
        window.iconbitmap(r"./icon.ico")

        lyric_box = customtkinter.CTkTextbox(
            master=window,
            width=580,
            height=435,
            corner_radius=0, 
            text_font=("Roboto Medium", -14)
        )
        lyric_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        lyric_box.insert(tkinter.END, lyrics)

    except:
        lyrics = 'Lyrics are not available'
        window = customtkinter.CTkToplevel(app)
        window.geometry("580x435")
        window.title("SUCK MY NUTS KANYE")
        window.iconbitmap(r"./icon.ico")

        lyric_box = customtkinter.CTkTextbox(
            master=window,
            width=580,
            height=435,
            corner_radius=0, 
            text_font=("Roboto Medium", -14)
        )
        lyric_box.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        lyric_box.insert(tkinter.END, lyrics)
        return


def slider_event(value):
    if slider1.get() != 0:
        checkbox1.select()
    if slider2.get() != 0:
        checkbox2.select()
    if slider3.get() != 0:
        checkbox3.select()
    if slider4.get() != 0:
        checkbox4.select()
    bass.set_volume(slider1.get())
    drums.set_volume(slider2.get())
    other.set_volume(slider3.get())
    vocals.set_volume(slider4.get())


def checkbox_event():
    if checkbox1.get() == "on":
        bass.set_volume(slider1.get())
    else:
        slider1.set(0)
        bass.set_volume(slider1.get())
    if checkbox2.get() == "on":
        drums.set_volume(slider2.get())
    else:
        slider2.set(0)
        drums.set_volume(slider2.get())
    if checkbox3.get() == "on":
        other.set_volume(slider3.get())
    else:
        slider3.set(0)
        other.set_volume(slider3.get())
    if checkbox4.get() == "on":
        vocals.set_volume(slider4.get())
    else:
        slider4.set(0)
        vocals.set_volume(slider4.get())


frame = customtkinter.CTkFrame(master=app, width=350, height=200, corner_radius=8)
frame.place(relx=0.95, rely=0.5, anchor=tkinter.E)

option_frame = customtkinter.CTkFrame(
    master=app, width=350, height=100, corner_radius=8
)
option_frame.place(relx=0.95, rely=0.87, anchor=tkinter.E)

timestamp_frame = customtkinter.CTkFrame(
    master=app, width=350, height=100, corner_radius=8
)
timestamp_frame.place(relx=0.95, rely=0.13, anchor=tkinter.E)

frame_left = customtkinter.CTkFrame(master=app, width=175, height=445, corner_radius=8)
frame_left.place(relx=0, rely=0.5, anchor=tkinter.W)

left_label_1 = customtkinter.CTkLabel(
    master=frame_left, text="StemPlayer", text_font=("Roboto Medium", -16)
)
left_label_1.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

label_mode = customtkinter.CTkLabel(master=frame_left, text="Appearance Mode:")
label_mode.place(relx=0.5, rely=0.8, anchor=tkinter.CENTER)

optionmenu_1 = customtkinter.CTkOptionMenu(
    master=frame_left,
    values=["System", "Dark", "Light"],
    command=customtkinter.set_appearance_mode,
)
optionmenu_1.place(relx=0.5, rely=0.9, anchor=tkinter.CENTER)

button1 = customtkinter.CTkButton(
    master=option_frame,
    text="Import Playlist",
    corner_radius=8,
    command=button_event3,
    width=140,
    height=28,
)

button2 = customtkinter.CTkButton(
    master=option_frame,
    text="Import New Playlist",
    corner_radius=8,
    command=button_event5,
    width=140,
    height=28,
)

button3 = customtkinter.CTkButton(
    master=option_frame,
    text="Import New Song",
    corner_radius=8,
    command=button_event1,
    width=140,
    height=28,
)

button4 = customtkinter.CTkButton(
    master=option_frame,
    text="Import Song",
    corner_radius=8,
    command=button_event2,
    width=140,
    height=28,
)

button_optionlabel = customtkinter.CTkLabel(master=option_frame, text="Options:")

button_optionlabel.place(relx=0.5, rely=0.2, anchor=tkinter.CENTER)
button1.place(relx=0.29, rely=0.8, anchor=tkinter.CENTER)
button2.place(relx=0.71, rely=0.8, anchor=tkinter.CENTER)
button3.place(relx=0.71, rely=0.5, anchor=tkinter.CENTER)
button4.place(relx=0.29, rely=0.5, anchor=tkinter.CENTER)

global label2
label2 = customtkinter.CTkLabel(
    master=frame, text=f" ", width=240, height=50, corner_radius=1
)
label2.place(relx=0.5, rely=1.02, anchor=tkinter.S)

slider1 = customtkinter.CTkSlider(
    master=frame, from_=0, to=1, command=slider_event, number_of_steps=10
)
slider1.place(relx=0.6, rely=0.3, anchor=tkinter.CENTER)

slider2 = customtkinter.CTkSlider(
    master=frame, from_=0, to=1, command=slider_event, number_of_steps=10
)
slider2.place(relx=0.6, rely=0.45, anchor=tkinter.CENTER)

slider3 = customtkinter.CTkSlider(
    master=frame, from_=0, to=1, command=slider_event, number_of_steps=10
)
slider3.place(relx=0.6, rely=0.6, anchor=tkinter.CENTER)

slider4 = customtkinter.CTkSlider(
    master=frame, from_=0, to=1, command=slider_event, number_of_steps=10
)
slider4.place(relx=0.6, rely=0.75, anchor=tkinter.CENTER)

global label
label = customtkinter.CTkButton(
    master=timestamp_frame,
    text=f"(song name)",
    width=240,
    height=50,
    text_font=("Roboto Medium", -14),
    command=button_event9,
    fg_color="#2A2D2E",
    hover_color="#2A2D2E",
)
label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

checkbox1 = customtkinter.CTkCheckBox(
    master=frame,
    text="bass",
    command=checkbox_event,
    variable=check_var1,
    onvalue="on",
    offvalue="off",
)
checkbox1.place(relx=0.1, rely=0.3, anchor=tkinter.W)

checkbox2 = customtkinter.CTkCheckBox(
    master=frame,
    text="drums",
    command=checkbox_event,
    variable=check_var2,
    onvalue="on",
    offvalue="off",
)
checkbox2.place(relx=0.1, rely=0.45, anchor=tkinter.W)

checkbox3 = customtkinter.CTkCheckBox(
    master=frame,
    text="other",
    command=checkbox_event,
    variable=check_var3,
    onvalue="on",
    offvalue="off",
)
checkbox3.place(relx=0.1, rely=0.6, anchor=tkinter.W)

checkbox4 = customtkinter.CTkCheckBox(
    master=frame,
    text="vocals",
    command=checkbox_event,
    variable=check_var4,
    onvalue="on",
    offvalue="off",
)
checkbox4.place(relx=0.1, rely=0.75, anchor=tkinter.W)

progressbar = customtkinter.CTkProgressBar(master=timestamp_frame, width=225, height=10)
progressbar.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)
progressbar.set(0)

progress_label_left = customtkinter.CTkLabel(
    master=timestamp_frame, text="0:00", text_font=("Roboto Medium", -12), width=50
)
progress_label_left.place(relx=0.1, rely=0.7, anchor=tkinter.CENTER)

progress_label_right = customtkinter.CTkLabel(
    master=timestamp_frame, text="0:00", text_font=("Roboto Medium", -12), width=50
)
progress_label_right.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

start_time = time.time()
try:
    RPC.update(
        large_image="kanye",
        start=start_time,
        large_text="SUCK MY NUTS KANYE",
        state="Exploring The Client",
    )
except:
    pass


def to_int(string):
    l = []
    m = []
    for i in string:
        l.append(ord(i))
    for i in l:
        m.append(int(bin(i)[2:]))
    result = 0
    for i in m:
        result += i
    return result

info_songs = None
def checks():
    global info_songs
    entry_val = 0
    while True:
        time.sleep(1)
        try:
            found_songs = []
            for i in songs:
                if search_entry.get().lower() in i.lower():
                    found_songs.append(i)
            if entry_val != to_int(search_entry.get()):
                entry_val -= entry_val
                info_songs = customtkinter.CTkTextbox(
                    master=frame_info, width=150, height=310, text_font=("Roboto Medium", -12)
                )
                info_songs.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
                info_songs.insert(tkinter.END, "\n\n".join(found_songs))
                entry_val += to_int(search_entry.get())
        except:
            pass
        try:
            state = app.state()
        except:
            print("no state")
            if RPC_CONNECTED == True:
                RPC.close()
            # sys.exit(1)
            os._exit(1)


check_thread = threading.Thread(target=checks)
check_thread.start()

app.mainloop()
