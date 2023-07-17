import os
import re
import subprocess
import sys
import threading
import typing

import customtkinter
import requests
import torch
from __version__ import __version__ as version

# Unviable for now, will be implemented in the future (maybe) 
# Right now I cant figure out how to update the main script without closing it first

class MISSTupdater(customtkinter.CTkFrame): 
    """
    Class for handling the update of MISST
    """
    def __init__(self, parent:typing.Any) -> None:
        """
        Initialize the updater
        """
        super().__init__(parent)
        self.width = 755
        self.height = 430
        self.FONT = "Roboto Medium"
        self.configure(width=self.width, height=self.height)

        self.parent = parent
        self.version = int(version.replace(".", ""))
        self.new_version = None
        self.url = "https://raw.githubusercontent.com/Frikallo/MISST/main/MISST/__version__.py"
        self.update = False
        self.progress_var = customtkinter.DoubleVar()

        self.check()
        if not self.update:
            self.parent.logger.info("MISST is up to date")
            self.destroy()
            return
        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Create the widgets
        """
        self.title = customtkinter.CTkLabel(self, text="Update available", font=(self.FONT, 20))
        self.title.place(x=self.width/2, y=140, anchor="center")

        self.update_button = customtkinter.CTkButton(self, text="Update", font=(self.FONT, 15), command=lambda: threading.Thread(target=self.download, daemon=True).start())
        self.update_button.place(x=self.width/2, y=200, anchor="center")

        self.ignore_button = customtkinter.CTkButton(self, text="Ignore", font=(self.FONT, 15), command=self.destroy)
        self.ignore_button.place(x=self.width/2, y=250, anchor="center")
        
    def check(self) -> bool:
        """
        Check if an update is available
        """
        r = requests.get(self.url)
        r.raise_for_status()
        self.new_version = r.text.split("=")[1].strip().strip("'")
        new_version = int(self.new_version.replace(".", ""))
        if self.version < new_version:
            self.update = True
        return self.update
    
    def download(self) -> None:
        """
        Download the update
        """
        self.update_button.destroy()
        self.ignore_button.destroy()
        self.title.destroy()

        if not os.path.exists("MISSTupdate"):
            os.mkdir("MISSTupdate")
        os.chdir("MISSTupdate")
        self.label = customtkinter.CTkLabel(self, text="Installing Update", font=(self.FONT, 20))
        self.label.place(relx=0.5, rely=0.45, anchor="center")

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", width=300, height=15, variable=self.progress_var)
        self.progressbar.place(relx=0.5, rely=0.55, anchor="center")
        # Download 7zr.exe
        self.label.configure(text="Downloading extracting tool")
        sevenzip = "https://www.7-zip.org/a/7zr.exe"
        r = requests.get(sevenzip)
        r.raise_for_status()
        total_length = r.headers.get('content-length')
        with open("7zr.exe", "wb") as f:
            dl = 0
            for data in r.iter_content(chunk_size=len(r.content)//50):
                dl += len(data)
                f.write(data)
                self.progress_var.set((dl / int(total_length)))
        self.progress_var.set(0)
        # Download MISST
        # get newest release from github
        self.label.configure(text="Downloading MISST")
        github_url = "https://api.github.com/repos/Frikallo/MISST/releases/latest"
        r = requests.get(github_url)
        r.raise_for_status()
        release = r.json()

        device = "CPU" if not torch.cuda.is_available() else "CUDA"
        misst_url = None
        for asset in release["assets"]:
            if asset["name"] == f"MISST_{device}_{str(self.new_version)}_Release_Win.7z":
                misst_url = asset["browser_download_url"]
                break
        if misst_url is None:
            self.parent.logger.info("Error: MISST.7z not found")

        r = requests.get(misst_url)
        r.raise_for_status()
        total_length = r.headers.get('content-length')
        with open("MISST.7z", "wb") as f:
            dl = 0
            for data in r.iter_content(chunk_size=len(r.content)//50):
                dl += len(data)
                f.write(data)
                self.progress_var.set((dl / int(total_length)))
        # Extract MISST
        self.label.configure(text="Extracting Update (This may take a while)")
        # use sdout to update progressbar
        threading.Thread(target=self.extract_with_progress, args=("MISST.7z"), daemon=True).start()

    def extract_with_progress(self, zip_file) -> None:
        """
        Extract the update
        """
        cmd = ['7zr.exe', 'x', zip_file, "-bsp1", "-aoa"]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        # Regular expression pattern to match the extraction progress
        progress_pattern = re.compile(r'(\d+)%')

        while process.poll() is None:
            output = process.stdout.readline()
            match = progress_pattern.search(output)

            if match:
                percentage = int(match.group(1))
                self.progress_var.set(percentage / 100)

        # Remove 7zr.exe and MISST.7z
        self.label.configure(text="Cleaning up")
        os.remove("7zr.exe")
        os.remove("MISST.7z")
        self.label.configure(text="Update installed")
        # Restart MISST
        os.execl(sys.executable, sys.executable, *sys.argv)