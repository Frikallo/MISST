from MISSTsettings import MISSTsettings
import pyaudio
import wave
import threading
import numpy as np

class MISSTplayer:
    def __init__(self, files, volumes):
        self.files = files
        self.p = pyaudio.PyAudio()
        self.streams = []
        self.paused = False
        self.positions = [0] * len(files)
        self.volumes = volumes
        self.chunk_size = 1024
        self.fade_duration = 1  # Fade duration in seconds
        self.nightcore = False
        self.settings = MISSTsettings()
        self.bands = lambda: [self.settings.getSetting(f"eq_{n}") for n in range(1,10)] # lambda so the player can access the latest information 
        self.eq = lambda: True if self.settings.getSetting("eq") == "true" else False
        self.center_freqs = [62, 125, 250, 500, 1_000, 2_500, 4_000, 8_000, 16_000] # 62 Hz, 125 Hz, 250 Hz, 500 Hz, 1 KHz, 2.5 KHz, 4 KHz, 8 KHz, 16 KHz
        
        for file in self.files:
            wf = wave.open(file, 'rb')
            self.frame_rate = wf.getframerate()
            self.duration = wf.getnframes() / self.frame_rate
            self.channels = wf.getnchannels()
            stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                                 channels=wf.getnchannels(),
                                 rate=wf.getframerate(),
                                 output=True)
            self.streams.append(stream)
        
    def play(self):
        self.paused = False
        while not self.paused:
            for i, stream in enumerate(self.streams):
                data = self.get_data(i)
                if data:
                    if self.positions[i] == 0:
                        data = self.fade_in(data)
                    stream.write(data)
                else:
                    break
        
    def get_data(self, stream_index):
        wf = wave.open(self.files[stream_index], 'rb')
        wf.setpos(self.positions[stream_index])
        data = wf.readframes(self.chunk_size)
        if data:
            self.positions[stream_index] = wf.tell()
            data = self.adjust_volume(data, self.volumes[stream_index])
            if self.nightcore == True:
                data = self.apply_nightcore(data)
            try:
                if self.eq() == True:
                    data = self.apply_eq(data) # apply eq last so it can be applied to nightcore data aswell
            except:
                # json error
                pass
        wf.close()
        return data
    
    def adjust_volume(self, data, volume):
        data = bytearray(data)
        for i in range(0, len(data), 2):
            sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
            sample = int(sample * volume)
            data[i:i+2] = sample.to_bytes(2, byteorder='little', signed=True)
        return bytes(data)
    
    def fade_in(self, data):
        samples = np.frombuffer(data, dtype=np.int16)
        fade_samples = int(self.fade_duration * self.frame_rate)
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        samples_copy = samples.copy()  # Make a copy of the samples array
        samples_copy[:fade_samples] = (samples_copy[:fade_samples] * fade_in[:len(samples_copy[:fade_samples])]).astype(np.int16)
        return samples_copy.tobytes()
    
    def fade_out(self, data):
        samples = np.frombuffer(data, dtype=np.int16)
        fade_samples = int(self.fade_duration * self.frame_rate)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        samples_copy = samples.copy()  # Make a copy of the samples array
        samples_copy[-fade_samples:] = (samples_copy[-fade_samples:] * fade_out[:len(samples_copy[-fade_samples:])]).astype(np.int16)
        return samples_copy.tobytes()
    
    def apply_nightcore(self, data):
        samples = np.frombuffer(data, dtype=np.int16)
        samples = samples.astype(np.float32)
        samples = samples.reshape((len(samples) // 2, 2)).T
        samples = samples.mean(axis=0)
        
        # Apply nightcore effect (increase speed and higher pitch)
        speedup_factor = 1.25  # Adjust the speedup factor as desired
        samples = np.interp(np.arange(0, len(samples), speedup_factor), np.arange(len(samples)), samples)
        
        samples = samples.astype(np.int16)
        samples = np.repeat(samples, 2)
        
        return samples.tobytes()

    def apply_eq(self, data):
        # Convert data to float32
        audio_data = np.frombuffer(data, dtype=np.int16)

        try:
            gains = np.array(self.bands(), dtype=np.float32)  # Gain values in dB
        except:
            gains = np.array([0] * 9, dtype=np.float32)

        # Number of frequency bands
        num_bands = len(gains)

        # Generate frequency range (20Hz to 20kHz)
        frequencies = np.fft.rfftfreq(len(audio_data), d=1 / 44100)

        # Create equalizer response
        response = np.zeros_like(frequencies)

        # Apply gain to each frequency band
        for i in range(num_bands):
            lower_cutoff = self.center_freqs[i] / np.sqrt(2)  # Lower cutoff frequency
            upper_cutoff = self.center_freqs[i] * np.sqrt(2)  # Upper cutoff frequency

            # Find indices within the frequency range
            indices = np.where((frequencies >= lower_cutoff) & (frequencies <= upper_cutoff))[0]

            # Apply gain to the corresponding indices
            response[indices] += gains[i]

        # Convert response to linear scale and normalize
        response_linear = 10 ** (response / 20)
        response_linear /= np.max(response_linear)

        # Apply equalization to audio data
        audio_fft = np.fft.rfft(audio_data)
        audio_fft *= response_linear[:len(audio_fft)]
        equalized_audio = np.fft.irfft(audio_fft).astype(np.int16)

        return equalized_audio.tobytes()
    
    def set_nightcore(self, nightcore):
        self.nightcore = nightcore
        
    def set_volume(self, stream_index, volume):
        self.volumes[stream_index] = volume
    
    def set_position(self, stream_index, position):
        self.positions[stream_index] = position
    
    def pause(self):
        self.paused = True
        for i, stream in enumerate(self.streams):
            if self.positions[i] > 0:
                data = self.get_data(i)
                if data:
                    data = self.fade_out(data)
                    stream.write(data)

    def resume(self):
        if self.paused:
            self.paused = False
            threading.Thread(target=self.play, daemon=True).start()
    
    def stop(self):
        for i, stream in enumerate(self.streams):
            if self.positions[i] > 0:
                data = self.get_data(i)
                if data:
                    data = self.fade_out(data)
                    stream.write(data)
            stream.stop_stream()
            stream.close()
        self.p.terminate()