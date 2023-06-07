from demucs.pretrained import get_model
from demucs.apply import BagOfModels, apply_model
import pathlib
import torch
import concurrent.futures
import numpy as np
import logging
import soundfile
import julius
import wave
import soundfile as sf
from MISSThelpers import MISSTconsole
import os

# Modified functions from https://github.com/facebookresearch/demucs, 
#                         https://pytorch.org/audio/main/tutorials/hybrid_demucs_tutorial.html 
#                         and https://github.com/CarlGao4/Demucs-Gui

class MISSTpreprocess():
    def __init__(self):
        pass

    def LoadModel(self, name = "mdx_extra", repo = None, device = "cuda" if torch.cuda.is_available() else "cpu",):
        model = get_model(name=name, repo=repo)
        model.to(device)
        model.eval()
        return model

    def GetData(self, model):
        res = {}
        res["channels"] = model.audio_channels
        res["samplerate"] = model.samplerate
        if isinstance(model, BagOfModels):
            res["models"] = len(model.models)
        else:
            res["models"] = 1
        res["sources"] = model.sources
        return res

    def Apply(self, model, wav, shifts=1):
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
            raise Exception("Error changing audio dims")
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
        wav = self.convert_audio_channels(wav, channels)
        return julius.resample_frac(wav, from_samplerate, to_samplerate)

    def load_audio(self, fn, sr):
        audio, raw_sr = soundfile.read(fn, dtype="float32")
        if len(audio.shape) == 1:
            audio = np.atleast_2d(audio).transpose()
        converted = self.convert_audio(torch.from_numpy(audio.transpose()), raw_sr, sr, 2)
        return converted.numpy()
    
    def apply_fade_in_out(self, input_file, output_file, fade_duration):
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
        model, 
        infile, 
        write = True, 
        outpath = pathlib.Path(""), 
        split = 10.0, 
        overlap = 0.25, 
        sample_rate = 44100, 
        device = "cuda" if torch.cuda.is_available() else "cpu", 
        logger = logging.getLogger("MISST"),
        console = None,
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

        def separation(i):
            logger.info("Separation %d/%d" % (i + 1, n))
            percent = ((i + 1)/n) * 100
            console.editLine(f"MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n\nMISST> [{'=' * int(percent / 4) + ' ' * (20 - int(percent / 4))}] {percent:.1f}%", 0)
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
            logger.info("Writing to file")
            console.addLine("\nMISST> Writing to file")
            outpath.mkdir(exist_ok=True)
            for i in range(len(stems)):
                stem = (new_audio[i] / total)[:, :orig_len]
                self.write_wav(torch.from_numpy(stem.transpose()), str(outpath / f"{stems[i]}.wav"), sample_rate)
                self.compress_wav_to_flac(str(outpath / f"{stems[i]}.wav"), str(outpath / f"{stems[i]}.flac"))
                self.apply_fade_in_out(str(outpath / f"{stems[i]}.flac"), str(outpath / f"{stems[i]}.flac"), 3.5)
        else:
            pass
        del model # Free up memory

    def preprocess(self, file, outDir, device="cuda"):
        self.logger.info(f"Preprocessing {file}...")
        console = MISSTconsole(self.preprocess_terminal_text, "MISST Preprocessor\nCopyright (C) @Frikallo Corporation.\n")
        try:
            savename = os.path.basename(file).replace('.mp3', '').replace('.wav', '').replace('.flac', '')
            console.update("\nMISST> Loading model")
            processor = MISSTpreprocess()
            model = processor.LoadModel(name="mdx_extra", repo=pathlib.Path("Pretrained"))
            console.endUpdate()
            console.addLine("\nMISST> Model loaded.")
            console.update("\nMISST> Preprocessing")
            processor.process(model, infile=pathlib.Path(file), outpath=pathlib.Path(f"{outDir}/{savename}"), device=device, console=console)
            del model # Free up memory
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