import os
import threading
import typing

import customtkinter
import requests
from pathlib import Path


class MISSTSetup(customtkinter.CTkFrame):
    """
    Class for handling the setup of MISST
    """
    def __init__(self, parent:typing.Any, model:str) -> None:
        """
        Initialize the setup

        Args:
            parent (tkinter.Tk): The parent of the frame
            model (str): The chosen model
        """
        super().__init__(parent)
        self.parent = parent

        self.model_urls = self.get_model_urls(model)
        for url in self.model_urls:
            if not os.path.isfile("Pretrained/"+url.split("/")[-1]):
                break
        else:
            self.parent.logger.info("All models are already downloaded")
            self.destroy()
            return
        
        # delete old model files
        for file in os.listdir("Pretrained/"):
            if file.endswith(".th"):
                os.remove("Pretrained/" + file)
                
        self.progress_var = customtkinter.DoubleVar()
        self.width = 755
        self.height = 430
        self.FONT = "Roboto Medium"
        self.configure(width=self.width, height=self.height)
        self.create_widgets()

    def get_model_urls(self, model:str) -> typing.List[str]:
        models = []
        with open("Pretrained/" + model + ".yaml", "r") as f:
            for line in f.readlines():
                if "models: " in line:
                    models = line.split("'")[1::2]
                    break
        remote_file = Path("Pretrained/files.txt")
        root: str = ''
        remote_models = {}
        for line in remote_file.read_text().split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
            elif line.startswith('root:'):
                root = line.split(':', 1)[1].strip()
            else:
                sig = line.split('-', 1)[0]
                assert sig not in remote_models
                remote_models[sig] = "https://dl.fbaipublicfiles.com/demucs/" + root + line
        urls = []
        for model in models:
            urls.append(remote_models[model])
        return urls

    def create_widgets(self) -> None:
        """
        Create the widgets
        """
        self.label = customtkinter.CTkLabel(self, text="Setting up models...", font=(self.FONT, 20))
        self.label.place(relx=0.5, rely=0.45, anchor="center")

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", width=300, height=15, variable=self.progress_var)
        self.progressbar.place(relx=0.5, rely=0.55, anchor="center")

        try:
            self.start_setup()
        except:
            self.label.configure(text="Download failed. Please try again.")
            threading.Timer(2, self.destroy).start()

    def start_setup(self) -> None:
        """
        Start the setup
        """
        self.thread = threading.Thread(target=self.setup_models)
        self.thread.start()

    def setup_models(self) -> None:
        """
        Setup the models
        """
        total_files = len(self.model_urls)
        for i, url in enumerate(self.model_urls):
            self.label.configure(text="Setting up models {}/{}".format(i + 1, total_files))
            if not os.path.isfile(url.split("/")[-1]):
                self.download_file(url)
            self.progress_var.set((i + 1) / total_files * 100)
        self.label.configure(text="Setup is complete. Welcome to MISST!")
        threading.Timer(2, self.destroy).start()

    def download_file(self, url:str) -> None:
        """
        Download a file

        Args:
            file (str): The file to download
        """
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        try:
            with open("Pretrained/" + url.split("/")[-1], 'wb') as f:
                if total_length is None:  # no content length header
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    chunk = total_length // 50
                    for data in response.iter_content(chunk_size=chunk):
                        dl += len(data)
                        f.write(data)
                        self.progress_var.set((dl / total_length))
                        self.update_idletasks()  # Update the GUI to refresh the progress bar
        except:
            os.remove("Pretrained/" + url.split("/")[-1])
            self.label.configure(text="Downloaded file is corrupted or an Error occured. Please try again.")
            raise Exception("Downloaded file is corrupted or an Error occured. Please try again.")