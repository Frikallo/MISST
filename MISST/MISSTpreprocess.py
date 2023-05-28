from demucs.pretrained import get_model as _gm
from demucs.hdemucs import HDemucs
from demucs.apply import BagOfModels, apply_model
import pathlib
import torch
from typing import Literal
import numpy as np
import logging
import soundfile
import julius
import wave
import soundfile as sf
from MISSThelpers import MISSTconsole
import os

class MISSTpreprocess():
    def __init__(self):
        pass

    def GetModel(
        self, 
        name: str = "mdx_extra_q",
        repo: pathlib.Path = None,
        device: Literal["cpu", "cuda"] = "cuda" if torch.cuda.is_available() else "cpu",
    ) -> HDemucs:
        model = _gm(name=name, repo=repo)
        model.to(device)
        model.eval()
        return model

    def GetData(self, model: HDemucs):
        res = {}
        # Number of audio channels
        res["channels"] = model.audio_channels
        # Require audio sample rate
        res["samplerate"] = model.samplerate
        # Number of models in the bag
        if isinstance(model, BagOfModels):
            res["models"] = len(model.models)
        else:
            res["models"] = 1
        # list of final output tracks
        res["sources"] = model.sources
        return res

    def Apply(
        self, 
        model: HDemucs,
        wav: torch.Tensor,
        shifts: int = 1,
    ) -> dict:
        audio = wav
        ref = audio.mean(0)
        audio = (audio - ref.mean()) / ref.std()
        sources = apply_model(model, audio[None], shifts=shifts, split=False, overlap=0.25, progress=False)[0]
        sources = sources * ref.std() + ref.mean()
        return dict(zip(model.sources, sources))

    def convert_audio_channels(self, wav, channels=2):
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
            raise ValueError("The audio file has less channels than requested but is not mono.")
        return wav

    def write_wav(self, wav, filename, samplerate):
        if wav.dtype.is_floating_point:
            wav = (wav.clamp_(-1, 1) * (2**15 - 1)).short()
        with wave.open(filename, "wb") as f:
            f.setnchannels(wav.shape[1])
            f.setsampwidth(2)
            f.setframerate(samplerate)
            f.writeframes(bytearray(wav.numpy()))

    def compress_wav_to_flac(self, wav_file, flac_file):
        # Read the WAV file
        data, samplerate = sf.read(wav_file)

        # Write the FLAC file and delete the WAV file
        sf.write(flac_file, data, samplerate, format='FLAC')
        os.remove(wav_file)

    def convert_audio(self, wav, from_samplerate, to_samplerate, channels):
        """Convert audio from a given samplerate to a target one and target number of channels."""
        wav = self.convert_audio_channels(wav, channels)
        return julius.resample_frac(wav, from_samplerate, to_samplerate)

    def load_audio(self, fn, sr):
        audio, raw_sr = soundfile.read(fn, dtype="float32")
        if len(audio.shape) == 1:
            audio = np.atleast_2d(audio).transpose()
        converted = self.convert_audio(torch.from_numpy(audio.transpose()), raw_sr, sr, 2)
        return converted.numpy()

    def process(
        self, 
        model: HDemucs,
        infile: pathlib.Path,
        write: bool = True,
        outpath: pathlib.Path = pathlib.Path(""),
        split: float = 10.0,
        overlap: float = 0.25,
        sample_rate: int = 44100,
        shifts: int = 1,
        device: Literal["cpu", "cuda"] = "cuda" if torch.cuda.is_available() else "cpu",
        callback=None,
        logger: logging.Logger = logging.getLogger("MISST"),
        console: MISSTconsole = None,
    ):
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
        for i in range(n):
            logger.info("Separation %d/%d" % (i + 1, n))
            console.editLine(f"MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n\nMISST> {((i + 1)/n) * 100:.1f}%", 0)
            l = i * (split - overlap)
            r = l + split
            result = self.Apply(model, torch.from_numpy(audio[:, l:r]).to(device))
            for (j, stem) in enumerate(stems):
                new_audio[j, :, l:r] += result[stem].cpu().numpy()
            total[l:r] += 1
        if write:
            logger.info("Writing to file")
            console.addLine("\nMISST> Writing to file")
            outpath.mkdir(exist_ok=True)
            for i in range(len(stems)):
                stem = (new_audio[i] / total)[:, :orig_len]
                self.write_wav(torch.from_numpy(stem.transpose()), str(outpath / f"{stems[i]}.wav"), sample_rate)
                self.compress_wav_to_flac(str(outpath / f"{stems[i]}.wav"), str(outpath / f"{stems[i]}.flac"))
        else:
            pass

    def preprocess(self, file, outDir, device="cuda"):
        self.logger.info(f"Preprocessing {file}...")
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        try:
            savename = os.path.basename(file).replace('.mp3', '').replace('.wav', '').replace('.flac', '')
            console.update("\nMISST> Loading model")
            processor = MISSTpreprocess()
            model = processor.GetModel(name="mdx_extra_q", repo=pathlib.Path("Pretrained"))
            console.endUpdate()
            console.addLine("\nMISST> Model loaded.")
            console.update("\nMISST> Preprocessing")
            processor.process(model, infile=pathlib.Path(file), outpath=pathlib.Path(f"{outDir}/{savename}"), device=device, console=console)
            console.endUpdate()
            console.addLine("\nMISST> Preprocessed.")
        except Exception as e:
            self.logger.error(e)
            console.endUpdate()
            console.addLine("\nMISST> Error.")
            pass
        console.addLine("\nMISST> Done.")
        self.import_file_button.configure(state='normal')
        self.import_button.configure(state='normal')
        return