import pygame
import threading
import customtkinter
import tkinter
from tkinter import filedialog
import os
import time
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pygame.mixer.init()
pygame.mixer.set_num_channels(10)


def play_thread(sound, channel):
    thread = pygame.mixer.Sound(sound)
    while True:
        pygame.mixer.Channel(channel).play(thread)
        while pygame.mixer.get_busy():
            pygame.time.delay(100)


bass = pygame.mixer.Channel(0)
drums = pygame.mixer.Channel(1)
other = pygame.mixer.Channel(2)
vocals = pygame.mixer.Channel(3)

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.title("SUCK MY NUTS KANYE")
app.iconbitmap(r"./icon.ico")
app.geometry("600x290")

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


def button_event1():
    # unseperated_song
    global abspath_song
    abspath_song = filedialog.askopenfilename(
        filetypes=(("Audio Files (*.mp3)", ".mp3"), ("All Files", "*.*"))
    )
    print(abspath_song)
    label2.configure(text=f"Preprocessing... Can take 10-15 seconds")
    thread = threading.Thread(target=preprocess_song)
    thread.start()


def button_event2():
    # preseparated_song
    label2.configure(text=" ")
    varpath = filedialog.askdirectory()
    thread1 = threading.Thread(target=play_thread, args=(f"{varpath}/bass.wav", 0))  #
    thread2 = threading.Thread(target=play_thread, args=(f"{varpath}/drums.wav", 1))  #
    thread3 = threading.Thread(target=play_thread, args=(f"{varpath}/other.wav", 2))  #
    thread4 = threading.Thread(target=play_thread, args=(f"{varpath}/vocals.wav", 3))  #
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    song = os.path.basename(varpath)
    label.configure(
        text=f"{song}", width=240, height=50,
    )
    label.place(relx=0.6, rely=0.05, anchor=tkinter.N)


def button_event3():
    label2.configure(text=" ")
    global folder
    folder = filedialog.askdirectory()
    left_button1.destroy()
    left_button2.destroy()
    frame_info = customtkinter.CTkFrame(master=frame_left, width=150, height=175)
    frame_info.place(relx=0.5, rely=0.05, anchor=tkinter.N)
    n = 0
    songs = []
    global song_names_valid
    song_names_valid = ""
    for file in os.listdir(folder):
        n += 1
        songs.append(f"{n}. {file}")
        song_names_valid += f"{file}\n"

    info_songs = customtkinter.CTkTextbox(master=frame_info, width=150, height=175)
    info_songs.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    info_songs.insert(tkinter.END, "\n\n".join(songs))

    global input_box
    input_box = customtkinter.CTkEntry(
        master=frame_left, width=150, height=25, placeholder_text="Enter index of song"
    )
    input_box.place(relx=0.5, rely=0.85, anchor=tkinter.S)

    play_button = customtkinter.CTkButton(
        master=frame_left, text="Play", width=150, height=25, command=button_event4
    )
    play_button.place(relx=0.5, rely=0.95, anchor=tkinter.S)


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
    label.configure(
        text=f"{song}", width=240, height=50,
    )
    label.place(relx=0.6, rely=0.05, anchor=tkinter.N)


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
    status_label.configure(text=f"Done! Separated songs can be found in ./separated")


def dl_playlist(url):
    playlist_name = url.split("/")[-1]
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


def button_event7():
    folder = filedialog.askdirectory()
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
        bass.set_volume(1)
    else:
        bass.set_volume(0)
    if checkbox2.get() == "on":
        drums.set_volume(1)
    else:
        drums.set_volume(0)
    if checkbox3.get() == "on":
        other.set_volume(1)
    else:
        other.set_volume(0)
    if checkbox4.get() == "on":
        vocals.set_volume(1)
    else:
        vocals.set_volume(0)


frame = customtkinter.CTkFrame(master=app, width=350, height=250, corner_radius=8)
frame.place(relx=0.95, rely=0.5, anchor=tkinter.E)

frame_left = customtkinter.CTkFrame(master=app, width=175, height=250, corner_radius=8)
frame_left.place(relx=0.05, rely=0.5, anchor=tkinter.W)

left_button1 = customtkinter.CTkButton(
    master=frame_left,
    text="Import Separated Playlist",
    corner_radius=8,
    command=button_event3,
)
left_button1.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER)

left_button2 = customtkinter.CTkButton(
    master=frame_left,
    text="Import New Playlist",
    corner_radius=8,
    command=button_event5,
    width=165,
)
left_button2.place(relx=0.5, rely=0.6, anchor=tkinter.CENTER)

global label2
label2 = customtkinter.CTkLabel(
    master=frame, text=f" ", width=240, height=50, corner_radius=1
)
label2.place(relx=0.5, rely=1, anchor=tkinter.S)

slider1 = customtkinter.CTkSlider(master=frame, from_=0, to=1, command=slider_event)
slider1.place(relx=0.6, rely=0.3, anchor=tkinter.CENTER)

slider2 = customtkinter.CTkSlider(master=frame, from_=0, to=1, command=slider_event)
slider2.place(relx=0.6, rely=0.4, anchor=tkinter.CENTER)

slider3 = customtkinter.CTkSlider(master=frame, from_=0, to=1, command=slider_event)
slider3.place(relx=0.6, rely=0.5, anchor=tkinter.CENTER)

slider4 = customtkinter.CTkSlider(master=frame, from_=0, to=1, command=slider_event)
slider4.place(relx=0.6, rely=0.6, anchor=tkinter.CENTER)

sources = customtkinter.CTkLabel(master=frame, text=f"sources", width=240, height=50,)
sources.place(relx=-0.15, rely=0.15, anchor=tkinter.W)

global label
label = customtkinter.CTkLabel(master=frame, text=f"(song name)", width=240, height=50,)
label.place(relx=0.6, rely=0.05, anchor=tkinter.N)

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
checkbox2.place(relx=0.1, rely=0.4, anchor=tkinter.W)

checkbox3 = customtkinter.CTkCheckBox(
    master=frame,
    text="other",
    command=checkbox_event,
    variable=check_var3,
    onvalue="on",
    offvalue="off",
)
checkbox3.place(relx=0.1, rely=0.5, anchor=tkinter.W)

checkbox4 = customtkinter.CTkCheckBox(
    master=frame,
    text="vocals",
    command=checkbox_event,
    variable=check_var4,
    onvalue="on",
    offvalue="off",
)
checkbox4.place(relx=0.1, rely=0.6, anchor=tkinter.W)

button = customtkinter.CTkButton(
    master=frame, text="Import New Song", command=button_event1, width=50
)
button.place(relx=0.7, rely=0.8, anchor=tkinter.CENTER)

button = customtkinter.CTkButton(
    master=frame, text="Import Seperated Song", command=button_event2, width=50
)
button.place(relx=0.3, rely=0.8, anchor=tkinter.CENTER)

app.mainloop()
