import os
import threading

import customtkinter
import requests


class MISSTSetup(customtkinter.CTkFrame):
    def __init__(self, parent, model_files):
        super().__init__(parent)
        self.parent = parent
        self.model_files = model_files
        self.progress_var = customtkinter.DoubleVar()
        self.width = 755
        self.height = 430
        self.FONT = "Roboto Medium"
        self.expected_sizes = [167_399, 167_391, 167_391, 167_399] # Expected sizes (in kB) of the models
        self.configure(width=self.width, height=self.height)
        self.create_widgets()

    def create_widgets(self):
        self.label = customtkinter.CTkLabel(self, text="Setting up models...", font=(self.FONT, 20))
        self.label.place(relx=0.5, rely=0.45, anchor="center")

        self.progressbar = customtkinter.CTkProgressBar(self, orientation="horizontal", width=300, height=15, variable=self.progress_var)
        self.progressbar.place(relx=0.5, rely=0.55, anchor="center")

        try:
            self.start_setup()
        except:
            self.label.configure(text="Download failed. Please try again.")
            threading.Timer(2, self.destroy).start()

    def start_setup(self):
        self.thread = threading.Thread(target=self.setup_models)
        self.thread.start()

    def setup_models(self):
        total_files = len(self.model_files)
        for i, file in enumerate(self.model_files):
            self.label.configure(text="Setting up models {}/{}".format(i + 1, total_files))
            if not os.path.isfile(file):
                self.download_file(file)
            self.progress_var.set((i + 1) / total_files * 100)
        self.label.configure(text="Setup is complete. Welcome to MISST!")
        threading.Timer(2, self.destroy).start()

    def download_file(self, file):
        url = "https://dl.fbaipublicfiles.com/demucs/mdx_final/" + file.replace("Pretrained/","")
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        with open(file, 'wb') as f:
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
        self.parent.logger.info("{0} Downloaded size: {1}kB | Expected size: ~{2}kB".format(file, os.path.getsize(file), self.expected_sizes[self.model_files.index(file)] * 1000))
        if os.path.getsize(file) < self.expected_sizes[self.model_files.index(file)] * 1000:
            self.parent.logger.error("{0} Downloaded size: {1}kB | Expected size: ~{2}kB".format(file, os.path.getsize(file), self.expected_sizes[self.model_files.index(file)] * 1000))
            os.remove(file)
            self.label.configure(text="Downloaded file is corrupted. Please try again.")
            raise Exception("Downloaded file is corrupted. Please try again.")