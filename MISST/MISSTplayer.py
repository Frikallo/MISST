import base64
import io
import threading
from typing import List

import music_tag  # for exporting song metadata
import numpy as np
import pyaudio
import soundfile as sf
from MISSTsettings import MISSTsettings
from scipy.signal import fftconvolve, butter, filtfilt


class MISSTplayer:
    """
    MISSTplayer class
    """
    def __init__(self, files:list, volumes:list) -> None:
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
        self.effects = False
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

        reverb_length = int(self.frame_rate * 0.3)
        self.impulse_response = self.generate_impulse_response(reverb_length, 0.5)
        self.reverb_tails = [np.zeros(self.chunk_size, dtype=np.float32) for _ in self.streams]

    def play(self) -> None:
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
    
    def get_data(self, stream_index:int) -> bytes:
        """
        Get the audio data

        Args:
            stream_index (int): Index of the stream
        """
        data, _ = sf.read(self.files[stream_index], dtype='int16', start=self.positions[stream_index], frames=self.chunk_size)
        if len(data) > 0:
            self.positions[stream_index] += len(data)
            data = self.adjust_volume(data, self.volumes[stream_index])
            if self.effects == True:
                try:
                    data = self.apply_effects(data, float(self.settings.getSetting("speed")),
                                                    float(self.settings.getSetting("reverb")),
                                                    float(self.settings.getSetting("pitch")),
                                                    stream_index)
                except:
                    # json error
                    pass
            try:
                if self.eq() == True:
                        data = self.apply_eq(data)  # apply eq last so it can be applied to nightcore data as well
            except:
                # json error
                pass
        return data
    
    def get_position(self, stream_index:int) -> float:
        """
        Get the position of the audio

        Args:
            stream_index (int): Index of the stream
        """
        return self.positions[stream_index] / float(self.frame_rate)
    
    def adjust_volume(self, data:bytes, volume:float) -> bytes:
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
    
    def apply_effects(self, data: bytes, speed_factor: float, reverb_factor: float, pitch_shift: float, stream_index:int) -> bytes:
        """
        Modify the audio

        Args:
            data (bytes): Audio data
            speed_factor (float): Speed value between 0.5 and 2.0 (0.5 = half speed, 2.0 = double speed)
            reverb_factor (float): Reverb value between 0.0 and 1.0 (0.0 = no reverb, 1.0 = full reverb)
            delay_time (float): Delay time in seconds
            stream_index (int): Index of the stream
        """
        # Convert bytes to numpy array
        samples = np.frombuffer(data, dtype=np.int16)
        samples = samples.astype(np.float32)
        samples = samples.reshape((len(samples) // 2, 2)).T
        samples = samples.mean(axis=0)

        # Modify speed
        samples = self.modify_speed(samples, speed_factor)

        # Modify pitch
        samples = self.modify_pitch(samples, pitch_shift)

        # Add reverb
        samples = self.apply_reverb(samples, reverb_factor, stream_index)

        # Convert back to bytes
        samples = samples.astype(np.int16)
        samples = np.repeat(samples, 2)

        return samples.tobytes()
    
    def modify_speed(self, samples:np.ndarray, speed_factor:float) -> bytes:
        """
        Modify the speed of the audio

        Args:
            samples (np.ndarray): Audio data
            speed_factor (float): Speed value between 0.5 and 2.0 (0.5 = half speed, 2.0 = double speed)
        """
        if speed_factor == 1.0:
            return samples
        num_samples = len(samples)
        new_num_samples = int(num_samples / speed_factor)

        # Resample the audio to the new length
        resampled = np.interp(
            np.linspace(0, num_samples, new_num_samples, endpoint=False),
            np.arange(num_samples),
            samples
        )

        return resampled

    def apply_antialiasing_filter(self, samples: np.ndarray, cutoff_freq: float, frame_rate: int) -> np.ndarray:
        """
        Apply an anti-aliasing filter to the audio

        Args:
            samples (np.ndarray): Audio data
            cutoff_freq (float): Cutoff frequency in Hz
            frame_rate (int): Frame rate in Hz
        """
        # Create a low-pass Butterworth filter
        nyquist = 0.5 * frame_rate
        normal_cutoff = cutoff_freq / nyquist
        b, a = butter(8, normal_cutoff, btype='low', analog=False)
        
        # Apply the filter to the samples
        filtered_samples = filtfilt(b, a, samples, axis=0)
        return filtered_samples

    def modify_pitch(self, samples:np.ndarray, pitch_shift:float) -> bytes:
        """
        Modify the pitch of the audio

        Args:
            samples (np.ndarray): Audio data
            pitch_shift (float): Pitch value between -12.0 and 12.0 (-12.0 = one octave down, 12.0 = one octave up)
        """
        if pitch_shift == 0:
            return samples

        pitch_shift *= 12  # Convert pitch shift from octaves to semitones
        samples = samples.astype(np.float32) / np.iinfo(np.int16).max  # Convert samples to float32 between -1.0 and 1.0

        # Continue with the pitch shift as before
        shift_ratio = 2 ** (pitch_shift / 12)  # Shift by half-steps (semitones)
        time_axis = np.arange(samples.shape[0]) / self.frame_rate
        shifted_audio = np.interp(time_axis * shift_ratio, time_axis, samples)

        # Apply an anti-aliasing filter to attenuate high frequencies
        cutoff_freq = 0.9 * self.frame_rate / 2.0  # You can adjust the cutoff frequency as needed
        shifted_audio = self.apply_antialiasing_filter(shifted_audio, cutoff_freq, self.frame_rate)

        shifted_audio = np.clip(shifted_audio, -1.0, 1.0)  # Clip samples to prevent overflow
        
        # Convert samples back to 16-bit integer range
        return shifted_audio * np.iinfo(np.int16).max
    
    def generate_impulse_response(self, length:int, decay_factor:float) -> np.ndarray:
        """
        Generate impulse response

        Args:
            length (int): Length of the impulse response in samples (44100 samples = 1 second)
            decay_factor (float): Decay factor between 0.0 and 1.0 (0.0 = no decay, 1.0 = full decay)
        """
        impulse_response = np.zeros(length, dtype=np.float32)
        impulse_response[0] = 1.0

        # Generate decaying exponential tail
        for i in range(1, length):
            impulse_response[i] = impulse_response[i - 1] * decay_factor

        # Add some random noise for early reflections
        impulse_response += np.random.normal(0, 0.05, length)
        return impulse_response

    def apply_reverb(self, samples: np.ndarray, reverb_factor: float, stream_index: int) -> bytes:
        """
        Add reverb to the audio

        Args:
            samples (np.ndarray): Audio data
            reverb_factor (float): Reverb value between 0.0 and 1.0 (0.0 = no reverb, 1.0 = full reverb)
            stream_index (int): Index of the stream
        """
        if reverb_factor == 0:
            return samples

        samples = samples.astype(np.float32) / np.iinfo(np.int16).max  # Convert samples to float32 between -1.0 and 1.0

        # Apply reverb impulse response to the current chunk
        reverb_audio = fftconvolve(samples, self.impulse_response, mode='full')

        # Concatenate previous reverb tail with the current reverb tail
        reverb_audio[:len(self.reverb_tails[stream_index])] += self.reverb_tails[stream_index]

        # Store the current reverb tail for the next chunk
        self.reverb_tails[stream_index] = reverb_audio[len(samples):]

        mixed_audio = samples * (1 - reverb_factor) + reverb_audio[:len(samples)] * reverb_factor  # Mix original and reverb audio
        mixed_audio = np.clip(mixed_audio, -1.0, 1.0)  # Clip samples to prevent overflow

        # Convert samples back to 16-bit integer range
        return mixed_audio * np.iinfo(np.int16).max

    def apply_eq(self, data:bytes) -> bytes:
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

        # Apply equalization to audio data
        audio_fft = np.fft.rfft(audio_data)
        audio_fft *= response_linear[:len(audio_fft)]
        equalized_audio = np.fft.irfft(audio_fft).astype(np.int16)

        # Clip the audio to avoid distortion
        equalized_audio = np.clip(equalized_audio, -32768, 32767)

        return equalized_audio.tobytes()
    
    def set_effects(self, effects:bool) -> None:
        """
        Set the effects of the audio

        Args:
            effects (bool): Effects value
        """
        self.effects = effects

    def set_volume(self, stream_index:int, volume:float) -> None:
        """
        Set the volume of the audio

        Args:
            stream_index (int): Index of the stream
            volume (float): Volume value
        """
        self.volumes[stream_index] = volume
    
    def set_position(self, stream_index:int, position:float) -> None:
        """
        Set the position of the audio

        Args:
            stream_index (int): Index of the stream
            position (float): Position value
        """
        self.positions[stream_index] = position

    def save(self, files:List[str], volumes:List[int], filename:str, cover_art:bytes=None) -> None:
        """
        Save the audio

        Args:
            files (List[str]): List of audio files
            volumes (List[int]): List of volume values
            filename (str): Name of the file
        """
        # Load the audio files and get the sample rate
        audio_data = []
        sample_rate = None
        for file in files:
            data, sr = sf.read(file)
            audio_data.append(data)
            if sample_rate is None:
                sample_rate = sr

        adjusted_data = []
        for i in range(len(audio_data)):
            adjusted_data.append(audio_data[i] * volumes[i])

        overlapped_data = np.sum(adjusted_data, axis=0)

        sf.write(filename, overlapped_data, sample_rate)
        if cover_art is not None and cover_art != "null":
            byte_data = base64.b64decode(cover_art)
            byte_stream = io.BytesIO(byte_data)
            byte_stream.seek(0)
            f = music_tag.load_file(filename)
            f['artwork'] = byte_stream.read() 
            f.save()

    def pause(self) -> None:
        """
        Pause the audio
        """
        self.paused = True

    def resume(self) -> None:
        """
        Resume the audio
        """
        if self.paused:
            self.paused = False
            threading.Thread(target=self.play, daemon=True).start()
    
    def stop(self) -> None:
        """
        Stop the audio
        """
        for i, stream in enumerate(self.streams):
            stream.stop_stream()
            stream.close()
        self.p.terminate()

    def change_files(self, new_files:list, volumes:list) -> None:
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