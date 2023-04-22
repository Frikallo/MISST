import os
from PIL import Image
import io
from werkzeug.utils import secure_filename
import music_tag
import threading
import shutil
import time
import tkinter
from MISSThelpers import MISSThelpers

class MISSTpreprocess():
    def __init__(self, server):
        self.server = server
    
    def preprocess(self, file, outDir):
        print(f"Preprocessing {file}...")
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        try:
            savename = os.path.basename(file).replace('.mp3', '').replace('.wav', '').replace('.flac', '')
            webname = secure_filename(savename)
            console.update("\nMISST> In Queue")
            self.server.startDemucsQueue()
            console.endUpdate()
            console.addLine("\nMISST> Out of Queue.")
            console.update("\nMISST> Preprocessing")
            self.server.prepDemucs(file)
            console.endUpdate()
            console.addLine("\nMISST> Preprocessed.")
            console.update("\nMISST> Downloading")

            if os.path.isdir(f"{outDir}/{savename}"): # If the folder already exists, add a number to the end of the name
                n = 1 
                name = f"{savename} ({n})" 
                while os.path.isdir(f"{outDir}/{name}"):
                    n += 1
                    name = f"{savename} ({n})"
                savename = secure_filename(name)

            self.server.getDemucs(webname, outDir, savename)
            console.endUpdate()
            console.addLine("\nMISST> Downloaded.")
            console.update("\nMISST> Getting cover art")
            try:
                metadata = music_tag.load_file(file)
                metaart = metadata["artwork"]
                metaimg = Image.open(io.BytesIO(metaart.first.data))
                metaimg.save(f"{outDir}/{savename}/{secure_filename(savename)}.png")
                self.server.postDemucsCoverArt(f"{outDir}/{savename}/{secure_filename(savename)}.png")
                console.endUpdate()
                console.addLine("\nMISST> Got cover art.")
            except Exception as e:
                print(e)
                console.endUpdate()
                console.addLine("\nMISST> No cover art found.")
                pass
        except Exception as e:
            print(e)
            console.endUpdate()
            console.addLine("\nMISST> Error.")
            pass
        console.addLine("\nMISST> Done.")
        self.import_file_button.configure(state='normal')
        self.import_button.configure(state='normal')
        return
    
    def importSpotify(self, link, outDir):
        self.import_file_button.configure(state=tkinter.DISABLED)
        self.import_button.configure(state=tkinter.DISABLED)
        spotify = os.path.abspath("./Binaries/spotdl.exe")
        ffmpeg = os.path.abspath("./ffmpeg.exe")
        if link.startswith('https://open.spotify.com/track'):
            console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
            console.update("\nMISST> Downloading")
            os.system(f'{spotify} "{link}" --output ./dl-songs --ffmpeg {ffmpeg}')
            console.endUpdate()
            console.addLine("\nMISST> Downloaded.")
            MISSTpreprocess.preprocess(self, f"./dl-songs/{os.listdir('./dl-songs')[0]}", outDir)
            shutil.rmtree('./dl-songs')

        elif link.startswith('https://open.spotify.com/album') or link.startswith('https://open.spotify.com/playlist'):
            console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
            console.update("\nMISST> Downloading")
            os.system(f'./Binaries/spotdl.exe "{link}" --output ./dl-songs --ffmpeg ./ffmpeg.exe')
            console.endUpdate()
            console.addLine("\nMISST> Downloaded.")
            for song in os.listdir('./dl-songs'):
                MISSTpreprocess.preprocess(self, f"./dl-songs/{song}", outDir)
            shutil.rmtree('./dl-songs')
        else:
            console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
            console.addLine("\nMISST> Not a Spotify link.")
            print("Invalid Spotify Link.")
        self.import_file_button.configure(state='normal')
        self.import_button.configure(state='normal')
    
    def importYoutube(self, link, outDir):
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        console.addLine("\nMISST> Not implemented yet. Sorry!")
        return
    
    def importDeezer(self, link, outDir):
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        console.addLine("\nMISST> Not implemented yet. Sorry!")
        return
    
    def importSoundcloud(self, link, outDir):
        self.import_file_button.configure(state=tkinter.DISABLED)
        self.import_button.configure(state=tkinter.DISABLED)
        dlBin = os.path.abspath("./Binaries/musicdl.exe")
        try:
            console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
            console.update("\nMISST> Downloading")
            curChdir = os.getcwd()
            os.mkdir(f"./dl-songs")
            os.chdir(f"./dl-songs")
            os.system(f'{dlBin} "{link}"')
            os.chdir(curChdir)
            console.endUpdate()
            console.addLine("\nMISST> Downloaded.")
            MISSTpreprocess.preprocess(self, f"./dl-songs/{os.listdir('./dl-songs')[0]}", outDir)
            shutil.rmtree('./dl-songs')
        except:
            console.endUpdate()
            console.addLine("\nMISST> Error.")
            pass
        return
    
class MISSTconsole():
    def __init__(self, terminal, ogText):
        self.consoleText = ogText
        self.terminal = terminal
        self.curThread = None
        self.terminal.delete("0.0", "end")  # delete all text
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")

    def print(self, text):
        self.consoleText += text

    def updateThread(self, text):
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

    def update(self, text):
        self.curThread = threading.Thread(target=self.updateThread, args=(text,), daemon=True)
        self.curThread.start()

    def endUpdate(self):
        print(self.curThread)
        MISSThelpers.terminate_thread(self, self.curThread)
        self.terminal.configure(state="normal")
        self.terminal.delete("0.0", "end")
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")

    def addLine(self, text):
        self.consoleText += f"{text}"
        self.terminal.configure(state="normal")
        self.terminal.delete("0.0", "end")
        self.terminal.insert("0.0", self.consoleText)
        self.terminal.configure(state="disabled")


if __name__ == '__main__':
    pass