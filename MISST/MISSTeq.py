from pydub import AudioSegment
from scipy.signal import butter, sosfilt
import pygame
import threading
import multiprocessing as mp

class MISSTeq():
    def __init__(self, files, gains, chunk_size=2048, bands=9, freqs=[60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000], filter_order=2):
        self.FILES = files
        self.GAINS = gains
        self.CHUNK = chunk_size

        # Define equalizer settings
        self.BANDS = bands
        self.FREQS = freqs  # center frequencies for each band
        self.FILTER_ORDER = filter_order  # filter order for each band
        self.dict = mp.Manager().dict({0: [], 1: [], 2: [], 3: []})

    def stereo_to_ms(self, audio_segment):
        channel = audio_segment.split_to_mono()
        channel = [channel[0].overlay(channel[1]), channel[0].overlay(channel[1].invert_phase())]
        return AudioSegment.from_mono_audiosegments(channel[0], channel[1])

    def ms_to_stereo(self, audio_segment):
        channel = audio_segment.split_to_mono()
        channel = [channel[0].overlay(channel[1]) - 3, channel[0].overlay(channel[1].invert_phase()) - 3]
        return AudioSegment.from_mono_audiosegments(channel[0], channel[1])

    def _mk_butter_filter(self, freq, type, order):
        def filter_fn(seg):
            assert seg.channels == 1

            nyq = 0.5 * seg.frame_rate
            try:
                freqs = [f / nyq for f in freq]
            except TypeError:
                freqs = freq / nyq

            sos = butter(order, freqs, btype=type, output='sos')
            y = sosfilt(sos, seg.get_array_of_samples())

            return seg._spawn(y.astype(seg.array_type))

        return filter_fn

    def band_pass_filter(self, seg, low_cutoff_freq, high_cutoff_freq, order=2):
        filter_fn = self._mk_butter_filter([low_cutoff_freq, high_cutoff_freq], 'band', order=order)
        return seg.apply_mono_filter_to_each_channel(filter_fn)

    def high_pass_filter(self, seg, cutoff_freq, order=2):
        filter_fn = self._mk_butter_filter(cutoff_freq, 'highpass', order=order)
        return seg.apply_mono_filter_to_each_channel(filter_fn)

    def low_pass_filter(self, seg, cutoff_freq, order=2):
        filter_fn = self._mk_butter_filter(cutoff_freq, 'lowpass', order=order)
        return seg.apply_mono_filter_to_each_channel(filter_fn)

    def _eq(self, seg, focus_freq, bandwidth=100, mode="peak", gain_dB=0, order=2):
        filt_mode = ["peak", "low_shelf", "high_shelf"]
        if mode not in filt_mode:
            raise ValueError("Incorrect Mode Selection")
            
        if gain_dB >= 0:
            if mode == "peak":
                sec = self.band_pass_filter(seg, focus_freq - bandwidth/2, focus_freq + bandwidth/2, order = order)
                seg = seg.overlay(sec - (3 - gain_dB))
                return seg
            
            if mode == "low_shelf":
                sec = self.low_pass_filter(seg, focus_freq, order=order)
                seg = seg.overlay(sec - (3 - gain_dB))
                return seg
            
            if mode == "high_shelf":
                sec = self.high_pass_filter(seg, focus_freq, order=order)
                seg = seg.overlay(sec - (3 - gain_dB))
                return seg
            
        if gain_dB < 0:
            if mode == "peak":
                sec = self.high_pass_filter(seg, focus_freq - bandwidth/2, order=order)
                seg = seg.overlay(sec - (3 + gain_dB)) + gain_dB
                sec = self.low_pass_filter(seg, focus_freq + bandwidth/2, order=order)
                seg = seg.overlay(sec - (3 + gain_dB)) + gain_dB
                return seg
            
            if mode == "low_shelf":
                sec = self.high_pass_filter(seg, focus_freq, order=order)
                seg = seg.overlay(sec - (3 + gain_dB)) + gain_dB
                return seg
            
            if mode=="high_shelf":
                sec=self.low_pass_filter(seg, focus_freq, order=order)
                seg=seg.overlay(sec - (3 + gain_dB)) +gain_dB
                return seg

    def eq(self, seg, focus_freq, bandwidth=100, channel_mode="L+R", filter_mode="peak", gain_dB=0, order=2):
        channel_modes = ["L+R", "M+S", "L", "R", "M", "S"]
        if channel_mode not in channel_modes:
            raise ValueError("Incorrect Channel Mode Selection")
            
        if seg.channels == 1:
            return self._eq(seg, focus_freq, bandwidth, filter_mode, gain_dB, order)
            
        if channel_mode == "L+R":
            return self._eq(seg, focus_freq, bandwidth, filter_mode, gain_dB, order)
            
        if channel_mode == "L":
            seg = seg.split_to_mono()
            seg = [self._eq(seg[0], focus_freq, bandwidth, filter_mode, gain_dB, order), seg[1]]
            return AudioSegment.from_mono_audio_segements(seg[0], seg[1])
            
        if channel_mode == "R":
            seg = seg.split_to_mono()
            seg = [seg[0], self._eq(seg[1], focus_freq, bandwidth, filter_mode, gain_dB, order)]
            return AudioSegment.from_mono_audio_segements(seg[0], seg[1])
            
        if channel_mode == "M+S":
            seg = self.stereo_to_ms(seg)
            seg = self._eq(seg, focus_freq, bandwidth, filter_mode, gain_dB, order)
            return self.ms_to_stereo(seg)
            
        if channel_mode == "M":
            seg = self.stereo_to_ms(seg).split_to_mono()
            seg = [self._eq(seg[0], focus_freq, bandwidth, filter_mode, gain_dB, order), seg[1]]
            seg = AudioSegment.from_mono_audio_segements(seg[0], seg[1])
            return self.ms_to_stereo(seg)
            
        if channel_mode == "S":
            seg = self.stereo_to_ms(seg).split_to_mono()
            seg = [seg[0], self._eq(seg[1], focus_freq, bandwidth, filter_mode, gain_dB, order)]
            seg = AudioSegment.from_mono_audio_segements(seg[0], seg[1])
            return self.ms_to_stereo(seg)
        
    def play(self, channel):
        pygame.mixer.init()
        while True:
            print(len(self.dict[0]), len(self.dict[1]), len(self.dict[2]), len(self.dict[3]))
            if len(self.dict[0]) > 0 and len(self.dict[1]) > 0 and len(self.dict[2]) > 0 and len(self.dict[3]) > 0:
                pygame.mixer.Channel(channel).play(pygame.mixer.Sound(buffer=self.datas.pop(0)))
                while pygame.mixer.Channel(channel).get_busy():                    
                    pass

    def apply_eq(self, audio_seg, pygame_channel, gains):
        pygame.mixer.init()
        self.datas = []
        threading.Thread(target=self.play, args=(pygame_channel,), daemon=True).start()
        for i in range(0, len(audio_seg), self.CHUNK):
            # Extract chunk from audio file
            chunk = audio_seg[i:i+self.CHUNK]
            # Apply equalizer
            for j in range(0, self.BANDS):
                chunk = self.eq(chunk, self.FREQS[j], bandwidth=audio_seg.sample_width, channel_mode="L+R", filter_mode="peak", gain_dB=gains[j], order=self.FILTER_ORDER)
            self.datas.append(chunk._data)
            self.dict[pygame_channel] = [None]*len(self.datas)

        while len(self.dict[pygame_channel]) > 0:
            pass

    def run(self, file):
        self.apply_eq(AudioSegment.from_file(file), self.FILES.index(file), self.GAINS)

if __name__ == "__main__":
    files = ["./MISST/separated/z_test/bass.wav", "./MISST/separated/z_test/drums.wav", "./MISST/separated/z_test/other.wav", "./MISST/separated/z_test/vocals.wav"]

    with mp.Manager() as manager:
        eq = MISSTeq(files, [0, 0, 0, 0, 0, 0, 0, 0, 0])
        args = [file for file in files]
        with mp.Pool(processes=4) as pool:
            pool.map(eq.run, args)