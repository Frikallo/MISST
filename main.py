import pygame
import threading
import customtkinter
import tkinter
from tkinter import filedialog
import os
import time

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
app.geometry("400x290")

check_var1 = tkinter.StringVar(value="on")
check_var2 = tkinter.StringVar(value="on")
check_var3 = tkinter.StringVar(value="on")
check_var4 = tkinter.StringVar(value="on")

def preprocess_song():
    os.system(f"python3 -m demucs \"{abspath_song}\"")


def button_event1():
    #unseperated_song
    global abspath_song
    abspath_song = filedialog.askopenfilename(filetypes=(("Audio Files", ".mp3"),   ("All Files", "*.*")))
    print(abspath_song)
    label = customtkinter.CTkLabel(master=app, text=f"Preprocessing... Can take 10-15 seconds", width=240, height=50, corner_radius=1)
    label.place(relx=0.5, rely=1, anchor=tkinter.S)
    time.sleep(1)
    thread = threading.Thread(target=preprocess_song)
    thread.start()
    thread.join()
    label.config(text="Playing...")
    song = os.path.basename(abspath_song).replace(".mp3", "")
    label = customtkinter.CTkLabel(master=app, text=f"{song}", width=240, height=50,)
    label.place(relx=0.6, rely=0.1, anchor=tkinter.N)
    thread1 = threading.Thread(target=play_thread, args=(f"./separated/mdx_extra_q/{song}/bass.wav", 0))#
    thread2 = threading.Thread(target=play_thread, args=(f"./separated/mdx_extra_q/{song}/drums.wav", 1))#
    thread3 = threading.Thread(target=play_thread, args=(f"./separated/mdx_extra_q/{song}/other.wav", 2))#
    thread4 = threading.Thread(target=play_thread, args=(f"./separated/mdx_extra_q/{song}/vocals.wav", 3))#
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()


def button_event2():
    #preseparated_song
    varpath = filedialog.askdirectory()
    thread1 = threading.Thread(target=play_thread, args=(f"{varpath}/bass.wav", 0))#
    thread2 = threading.Thread(target=play_thread, args=(f"{varpath}/drums.wav", 1))#
    thread3 = threading.Thread(target=play_thread, args=(f"{varpath}/other.wav", 2))#
    thread4 = threading.Thread(target=play_thread, args=(f"{varpath}/vocals.wav", 3))#
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    song = os.path.basename(varpath)
    label = customtkinter.CTkLabel(master=app, text=f"{song}", width=240, height=50,)
    label.place(relx=0.6, rely=0.1, anchor=tkinter.N)


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

slider1 = customtkinter.CTkSlider(master=app, from_=0, to=1, command=slider_event)
slider1.place(relx=0.6, rely=0.3, anchor=tkinter.CENTER)

slider2 = customtkinter.CTkSlider(master=app, from_=0, to=1, command=slider_event)
slider2.place(relx=0.6, rely=0.4, anchor=tkinter.CENTER)

slider3 = customtkinter.CTkSlider(master=app, from_=0, to=1, command=slider_event)
slider3.place(relx=0.6, rely=0.5, anchor=tkinter.CENTER)

slider4 = customtkinter.CTkSlider(master=app, from_=0, to=1, command=slider_event)
slider4.place(relx=0.6, rely=0.6, anchor=tkinter.CENTER)

label = customtkinter.CTkLabel(master=app, text=f"sources", width=240, height=50,)
label.place(relx=-0.1, rely=0.1, anchor=tkinter.NW)

checkbox1 = customtkinter.CTkCheckBox(master=app, text="bass", command=checkbox_event,
                                     variable=check_var1, onvalue="on", offvalue="off")
checkbox1.place(relx=0.1, rely=0.3, anchor=tkinter.W)

checkbox2 = customtkinter.CTkCheckBox(master=app, text="drums", command=checkbox_event,
                                     variable=check_var2, onvalue="on", offvalue="off")
checkbox2.place(relx=0.1, rely=0.4, anchor=tkinter.W)

checkbox3 = customtkinter.CTkCheckBox(master=app, text="other", command=checkbox_event,
                                     variable=check_var3, onvalue="on", offvalue="off")
checkbox3.place(relx=0.1, rely=0.5, anchor=tkinter.W)

checkbox4 = customtkinter.CTkCheckBox(master=app, text="vocals", command=checkbox_event,
                                     variable=check_var4, onvalue="on", offvalue="off")
checkbox4.place(relx=0.1, rely=0.6, anchor=tkinter.W)

button = customtkinter.CTkButton(master=app, text="Import New Song", command=button_event1)
button.place(relx=0.85, rely=0.8, anchor=tkinter.SE)

button = customtkinter.CTkButton(master=app, text="Import Seperated Song", command=button_event2)
button.place(relx=0.09, rely=0.8, anchor=tkinter.SW)

app.mainloop()