import numpy as np
import scipy.signal as sg
import soundfile as sf
from pydub import AudioSegment
import multiprocessing as mp
import pyaudio
import threading
import gc

class MISSTeq:
    def __init__(self, sample_rate, volume, paused):
        self.sample_rate = sample_rate
        self.bands = np.array([62, 125, 250, 500, 1000, 2500, 4000, 8000, 16000])
        self.Q = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        self.gain_db = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.chunk_size = 1024
        self._calculate_coefficients()

        self.dict = mp.Manager().dict({'bass': [], 'drums': [], 'vocals': [], 'other': []})

        self.volume = volume
        self.paused = paused
        self.buffer = np.zeros(self.chunk_size, dtype=np.float32)

    def start_stream(self):
        self.stream = pyaudio.PyAudio().open(
                                  format=pyaudio.paFloat32,
                                  channels=2,
                                  rate=self.sample_rate,
                                  frames_per_buffer=self.chunk_size,
                                  output=True)

    def pause(self):
        self.paused.value = True
        
    def resume(self):
        self.paused.value = False

    def set_volume(self, volume):
        self.volume.value = volume
        
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        pyaudio.PyAudio().terminate()

    def _calculate_coefficients(self):
        self.coeffs = []
        for i in range(len(self.bands)):
            w0 = 2 * np.pi * self.bands[i] / self.sample_rate
            alpha = np.sin(w0) / (2 * self.Q[i])
            A = 10**(self.gain_db[i] / 40)
            b0 = 1 + alpha * A
            b1 = -2 * np.cos(w0)
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * np.cos(w0)
            a2 = 1 - alpha / A
            self.coeffs.append([b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0])
    
    def set_gain(self, gain_db):
        self.gain_db = gain_db
        self._calculate_coefficients()

    def process(self, signal):
        out = np.zeros_like(signal)
        if signal.ndim == 1:  # mono signal
            for i in range(len(self.bands)):
                b0, b1, b2, a1, a2 = self.coeffs[i]
                b = np.array([b0, b1, b2])
                a = np.array([1, a1, a2])
                out += signal * b[0]
                out = sg.lfilter(b, a, out)
        elif signal.ndim == 2:  # stereo signal
            for i in range(len(self.bands)):
                b0, b1, b2, a1, a2 = self.coeffs[i]
                b = np.array([b0, b1, b2])
                a = np.array([1, a1, a2])
                out[:, 0] += signal[:, 0] * b[0] + signal[:, 1] * b[1]
                out[:, 1] += signal[:, 0] * b[0] + signal[:, 1] * b[1]
                out[:, 0], out[:, 1] = sg.lfilter(b, a, out[:, 0]), sg.lfilter(b, a, out[:, 1])
        else:
            raise ValueError("Unsupported number of channels: %d" % signal.ndim)
        return out
    
    def prep_for_eq(self, file, start_ms):
        ### Convert to mono, cut to length, and export as wav
        sound = AudioSegment.from_wav(file)
        sound = sound[start_ms:sound.duration_seconds * 1000]
        sound = sound.set_channels(1)
        sound.export(file, format="wav")
        audio, sr = sf.read(file)
        return audio, sr
    
    def apply_eq(self, args):
        ### Convert to stereo, apply eq, and play
        file, channel, start_ms = args # Unpack args
        audio, sr = self.prep_for_eq(file, start_ms) # Prep for eq
        eq_audio = np.tile(audio, (2, 1)).T # Convert to stereo
        self.start_stream() # Start stream
        for i in range(0, eq_audio.shape[0], self.chunk_size): # Apply eq
            if self.paused.value: # Pause
                self.stream.write(self.buffer * 0, pyaudio.paContinue) # Write empty buffer
                while True: # Wait for resume
                    if not self.paused.value:
                        break
                    else:
                        pass
            chunk = eq_audio[i:i+self.chunk_size] # Get chunk
            processed_chunk = self.process(chunk) # Process chunk
            processed_chunk *= self.volume.value # Apply volume
            self.dict[channel] = ["ready"] # Set channel to ready
            while True: # Wait for all channels to be ready
                if len(self.dict["bass"]) > 0 and len(self.dict["drums"]) > 0 and len(self.dict["vocals"]) > 0 and len(self.dict["other"]) > 0:
                    break
                else:
                    pass
            self.stream.write(processed_chunk.astype(np.float32).tobytes()) # Write chunk
        self.close() # Close stream
        del audio, eq_audio, sr, processed_chunk, chunk # Delete variables
        gc.collect() # Collect garbage

def run(eq):
    files = ["MISST/separated/CantinaBand3/bass.wav", "MISST/separated/CantinaBand3/drums.wav", "MISST/separated/CantinaBand3/other.wav", "MISST/separated/CantinaBand3/vocals.wav"]
    start_ms = 0

    args = [(file, file.split("/")[-1].replace(".wav", ""), start_ms) for file in files]

    with mp.Pool(processes=4) as pool:
        pool.map(eq.apply_eq, args)    

if __name__ == '__main__':
    volume = mp.Manager().Value('d', 10.0)
    paused = mp.Manager().Value('b', False)
    eq = MISSTeq(44100, volume, paused)
    eq.set_gain(np.array([0,0,0,0,0,0,0,0,0]))
    threading.Thread(target=run, args=(eq,)).start()
    while True:
        paused.value = input("Paused: ") == "True" # Pause
        pass