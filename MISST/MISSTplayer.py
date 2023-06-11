import threading

import numpy as np
import pyaudio
import soundfile as sf

from MISSTsettings import MISSTsettings


class MISSTplayer:
    """
    MISSTplayer class
    """
    def __init__(self, files, volumes):
        """
        Initialize the player

        Args:
            files (list): List of file paths
            volumes (list): List of volume values
        """
        self.files = files
        self.p = pyaudio.PyAudio()
        self.streams = []
        self.paused = False
        self.positions = [0] * len(files)
        self.volumes = volumes
        self.chunk_size = 1024
        self.nightcore = False
        self.settings = MISSTsettings()
        self.bands = lambda: [self.settings.getSetting(f"eq_{n}") for n in range(1,10)] # lambda so the player can access the latest information 
        self.eq = lambda: True if self.settings.getSetting("eq") == "true" else False
        self.center_freqs = [62, 125, 250, 500, 1_000, 2_500, 4_000, 8_000, 16_000] # 62 Hz, 125 Hz, 250 Hz, 500 Hz, 1 KHz, 2.5 KHz, 4 KHz, 8 KHz, 16 KHz
        
        for file in self.files:
            data, self.frame_rate = sf.read(file, dtype='int16')
            self.duration = len(data) / self.frame_rate
            self.channels = data.shape[1]
            stream = self.p.open(format=self.p.get_format_from_width(2),
                                 channels=self.channels,
                                 rate=self.frame_rate,
                                 output=True)
            self.streams.append(stream)
        
    def play(self):
        """
        Play the audio
        """
        self.paused = False
        while not self.paused:
            for i, stream in enumerate(self.streams):
                data = self.get_data(i)
                if data:
                    stream.write(data)
                else:
                    break
        
    def get_data(self, stream_index):
        """
        Get the audio data

        Args:
            stream_index (int): Index of the stream
        """
        data, _ = sf.read(self.files[stream_index], dtype='int16', start=self.positions[stream_index], frames=self.chunk_size)
        if len(data) > 0:
            self.positions[stream_index] += len(data)
            data = self.adjust_volume(data, self.volumes[stream_index])
            if self.nightcore == True:
                data = self.apply_nightcore(data)
            try:
                if self.eq() == True:
                    data = self.apply_eq(data)  # apply eq last so it can be applied to nightcore data as well
            except:
                # json error
                pass
        return data
    
    def get_position(self, stream_index):
        """
        Get the position of the audio

        Args:
            stream_index (int): Index of the stream
        """
        return self.positions[stream_index] / float(self.frame_rate)
    
    def adjust_volume(self, data, volume):
        """
        Adjust the volume of the audio

        Args:
            data (bytes): Audio data
            volume (float): Volume value
        """
        data = bytearray(data)
        for i in range(0, len(data), 2):
            sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
            sample = int(sample * volume)
            data[i:i+2] = sample.to_bytes(2, byteorder='little', signed=True)
        return bytes(data)
    
    def apply_nightcore(self, data):
        """
        Apply the nightcore effect to the audio

        Args:
            data (bytes): Audio data
        """
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
        """
        Apply the equalizer effect to the audio

        Args:
            data (bytes): Audio data
        """
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
        """
        Set the nightcore effect

        Args:
            nightcore (bool): Nightcore effect
        """
        self.nightcore = nightcore
        
    def set_volume(self, stream_index, volume):
        """
        Set the volume of the audio

        Args:
            stream_index (int): Index of the stream
            volume (float): Volume value
        """
        self.volumes[stream_index] = volume
    
    def set_position(self, stream_index, position):
        """
        Set the position of the audio

        Args:
            stream_index (int): Index of the stream
            position (float): Position value
        """
        self.positions[stream_index] = position
    
    def pause(self):
        """
        Pause the audio
        """
        self.paused = True

    def resume(self):
        """
        Resume the audio
        """
        if self.paused:
            self.paused = False
            threading.Thread(target=self.play, daemon=True).start()
    
    def stop(self):
        """
        Stop the audio
        """
        for i, stream in enumerate(self.streams):
            stream.stop_stream()
            stream.close()
        self.p.terminate()

    def change_files(self, new_files, volumes):
        """
        Change the files of the audio

        Args:
            new_files (list): List of new files
            volumes (list): List of volumes
        """
        self.paused = True
        self.volumes = volumes

        for i, stream in enumerate(self.streams):
            stream.stop_stream()
            stream.close()

        self.streams.clear()
        self.files = new_files
        self.positions = [0] * len(new_files)

        for file in self.files:
            data, self.frame_rate = sf.read(file, dtype='int16')
            self.duration = len(data) / self.frame_rate
            self.channels = data.shape[1]
            stream = self.p.open(format=self.p.get_format_from_width(2),
                                channels=self.channels,
                                rate=self.frame_rate,
                                output=True)
            self.streams.append(stream)

        self.paused = False
        threading.Thread(target=self.play, daemon=True).start()