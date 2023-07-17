import concurrent.futures
import logging
import os
import pathlib
import wave

import julius
import numpy as np
import soundfile
import soundfile as sf
import torch
from demucs.apply import BagOfModels, apply_model
from demucs.pretrained import get_model
from MISSThelpers import MISSTconsole
from MISSThelpers import MISSThelpers

# Modified functions from https://github.com/facebookresearch/demucs, 
#                         https://pytorch.org/audio/main/tutorials/hybrid_demucs_tutorial.html 
#                         and https://github.com/CarlGao4/Demucs-Gui

class MISSTpreprocess():
    """
    MISSTpreprocess class
    """
    def __init__(self) -> None:
        pass

    def LoadModel(self, name:str, repo:str = None, device:str = "cuda" if torch.cuda.is_available() else "cpu",) -> BagOfModels:
        """
        Load the model

        Args:
            name (str): Name of the model
            repo (str): Repository of the model
            device (str): Device to use
        """
        model = get_model(name=name, repo=repo)
        model.to(device)
        model.eval()
        return model

    def GetData(self, model:BagOfModels) -> dict:
        """
        Get the data from the model

        Args:
            model (demucs.pretrained.BagOfModels): Model to get the data from
        """
        res = {}
        res["channels"] = model.audio_channels
        res["samplerate"] = model.samplerate
        if isinstance(model, BagOfModels):
            res["models"] = len(model.models)
        else:
            res["models"] = 1
        res["sources"] = model.sources
        return res

    def Apply(self, model:BagOfModels, wav:np.ndarray, shifts:int = 1) -> dict:
        """
        Apply the model to the audio

        Args:
            model (demucs.pretrained.BagOfModels): Model to apply
            wav (numpy.ndarray): Audio data
            shifts (int): Number of shifts
        """
        audio = wav
        ref = audio.mean(0)
        audio -= ref.mean()
        audio /= ref.std()
        sources = apply_model(model, audio[None], shifts=shifts, split=False, overlap=0.25, progress=False)[0]
        sources *= ref.std()
        sources += ref.mean()
        return dict(zip(model.sources, sources))

    def convert_audio_channels(self, wav:np.ndarray, channels:int = 2) -> np.ndarray:
        """
        Convert the audio channels

        Args:
            wav (numpy.ndarray): Audio data
            channels (int): Number of channels
        """
        *shape, src_channels, length = wav.shape
        if src_channels == channels:
            pass
        elif channels == 1:
            wav = wav.mean(dim=-2, keepdim=True)
        elif src_channels == 1:
            wav = wav.expand(*shape, channels, length)
        elif src_channels >= channels:
            wav = wav[..., :channels, :]
        else:
            raise Exception("Error changing audio dims")
        return wav

    def write_wav(self, wav:np.ndarray, filename:str, samplerate:int) -> None:
        """
        Write the audio to a WAV file

        Args:
            wav (numpy.ndarray): Audio data
            filename (str): Filename
            samplerate (int): Samplerate
        """
        if wav.dtype.is_floating_point:
            wav = (wav.clamp_(-1, 1) * (2**15 - 1)).short()
        with wave.open(filename, "wb") as f:
            f.setnchannels(wav.shape[1])
            f.setsampwidth(2)
            f.setframerate(samplerate)
            f.writeframes(bytearray(wav.numpy()))

    def compress_wav_to_flac(self, wav_file:str, flac_file:str) -> None:
        """
        Compress the WAV file to a FLAC file

        Args:
            wav_file (str): WAV filename
            flac_file (str): FLAC filename
        """
        # Read the WAV file
        data, samplerate = sf.read(wav_file)

        # Write the FLAC file and delete the WAV file
        sf.write(flac_file, data, samplerate, format='FLAC')
        os.remove(wav_file)

    def convert_audio(self, wav:np.ndarray, from_samplerate:int, to_samplerate:int, channels:int) -> np.ndarray:
        """
        Convert the audio

        Args:
            wav (numpy.ndarray): Audio data
            from_samplerate (int): From samplerate
            to_samplerate (int): To samplerate
            channels (int): Number of channels
        """
        wav = self.convert_audio_channels(wav, channels)
        return julius.resample_frac(wav, from_samplerate, to_samplerate)

    def load_audio(self, fn:str, sr:int) -> np.ndarray:
        """
        Load the audio

        Args:
            fn (str): Filename
            sr (int): Samplerate
        """
        audio, raw_sr = soundfile.read(fn, dtype="float32")
        if len(audio.shape) == 1:
            audio = np.atleast_2d(audio).transpose()
        converted = self.convert_audio(torch.from_numpy(audio.transpose()), raw_sr, sr, 2)
        return converted.numpy()
    
    def apply_fade_in_out(self, input_file:str, output_file:str, fade_duration:float) -> None:
        """
        Apply fade in and out to the audio

        Args:
            input_file (str): Input filename
            output_file (str): Output filename
            fade_duration (float): Fade duration
        """
        # Read the audio file
        audio_data, sample_rate = sf.read(input_file)
        
        # Calculate the number of samples for the fade duration
        fade_samples = int(fade_duration * sample_rate)
        
        # Apply fade-in
        fade_in_curve = np.linspace(0.0, 1.0, fade_samples)
        audio_data[:fade_samples] *= fade_in_curve[:, np.newaxis]
        
        # Apply fade-out
        fade_out_curve = np.linspace(1.0, 0.0, fade_samples)
        audio_data[-fade_samples:] *= fade_out_curve[:, np.newaxis]
        
        # Save the modified audio to a new file
        sf.write(output_file, audio_data, sample_rate)

    def process(
        self, 
        model:BagOfModels, 
        infile:str, 
        write:bool = True, 
        outpath:pathlib.Path = pathlib.Path(""), 
        split:float = 5.0, 
        overlap:float = 0.25, 
        sample_rate:int = 44100, 
        device:str = "cuda" if torch.cuda.is_available() else "cpu", 
        logger:logging.Logger = logging.getLogger("MISST"),
        console:MISSTconsole = None,
    ) -> None:
        """
        Process the audio

        Args:
            model (demucs.pretrained.BagOfModels): Model to apply
            infile (str): Input filename
            write (bool): Write the output
            outpath (pathlib.Path): Output path
            split (float): Split (seconds)
            overlap (float): Overlap
            sample_rate (int): Sample rate
            device (str): Device
            logger (logging.Logger): Logger
            console (MISSTConsole): Console
        """
        split = int(split * sample_rate)
        overlap = int(overlap * split)
        logger.info("Loading file")
        audio = self.load_audio(str(infile), sample_rate)
        logger.info(f"Loaded audio of shape {audio.shape}")
        orig_len = audio.shape[1]
        n = int(np.ceil((orig_len - overlap) / (split - overlap)))
        audio = np.pad(audio, [(0, 0), (0, n * (split - overlap) + overlap - orig_len)])
        logger.info("Loading model to device %s" % device)
        model.to(device)
        stems = self.GetData(model)["sources"]
        new_audio = np.zeros((len(stems), 2, audio.shape[1]))
        total = np.zeros(audio.shape[1])
        logger.info("Total splits of '%s' : %d" % (str(infile), n))

        def separation(i):
            logger.info("Separation %d/%d" % (i + 1, n))
            console.editLine(f"MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n\nMISST> Split {i + 1}/{n} ({((i + 1)/n) * 100:.1f}%)", 0)
            l = i * (split - overlap)
            r = l + split
            result = self.Apply(model, torch.from_numpy(audio[:, l:r]).to(device))
            for (j, stem) in enumerate(stems):
                new_audio[j, :, l:r] += result[stem].cpu().numpy()
            total[l:r] += 1

        workers = 1 if device == "cuda" else (os.cpu_count() // 2) # CPU parallelization on half the cores available, CUDA kernels are already parallelized

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(separation, i) for i in range(n)]
            concurrent.futures.wait(futures)

        if write:
            console.endUpdate()
            console.addLine("\nMISST> Preprocessed.")
            console.update("\nMISST> Writing to file")
            outpath.mkdir(exist_ok=True)
            for i in range(len(stems)):
                if np.all(total == 0):
                    stem = np.zeros_like(new_audio[i])
                else:
                    stem = (new_audio[i] / total)[:, :orig_len]
                self.write_wav(torch.from_numpy(stem.transpose()), str(outpath / f"{stems[i]}.wav"), sample_rate)
                self.compress_wav_to_flac(str(outpath / f"{stems[i]}.wav"), str(outpath / f"{stems[i]}.flac"))
                self.apply_fade_in_out(str(outpath / f"{stems[i]}.flac"), str(outpath / f"{stems[i]}.flac"), 3.5)
            console.endUpdate()
        else:
            pass
        del model # Free up memory

    def preprocess(self, file:str, outDir:str, chosen_model:str, device:str = "cuda") -> None:
        """
        Preprocess the audio

        Args:
            file (str): Input filename
            outDir (str): Output directory
            device (str): Device
        """
        self.logger.info(f"Preprocessing {file}...")
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        try:
            savename = os.path.basename(file).replace('.mp3', '').replace('.wav', '').replace('.flac', '')
            console.update("\nMISST> Loading model")
            processor = MISSTpreprocess()
            model = processor.LoadModel(name=chosen_model, repo=pathlib.Path("Pretrained"))
            console.endUpdate()
            console.addLine("\nMISST> Model loaded.")
            console.update("\nMISST> Preprocessing")
            processor.process(model, infile=pathlib.Path(file), outpath=pathlib.Path(f"{outDir}/{savename}"), device=device, console=console)
            del model # Free up memory
        except Exception as e:
            self.logger.error(e)
            console.addLine("\nMISST> Error.")
            pass
        console.addLine("\nMISST> Done.")
        self.import_file_button.configure(state='normal')
        self.import_button.configure(state='normal')
        return