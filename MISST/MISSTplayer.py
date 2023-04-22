import pygame
import gc
import threading
from pydub import AudioSegment
from MISSThelpers import MISSThelpers
from MISSTeq import MISSTeq

class MISSTplayer():
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(4)

        self.bass = pygame.mixer.Channel(0)
        self.drums = pygame.mixer.Channel(1)
        self.other = pygame.mixer.Channel(2)
        self.vocals = pygame.mixer.Channel(3)

    def play_thread(self, channel, sound):
        while True:
            try:
                pygame.mixer.Channel(channel).play(sound)
                MISSTeq().run()
                gc.collect()
            except:
                self.songlabel.configure(text="")
                return
            while pygame.mixer.get_busy():
                pygame.time.delay(100)

    def play(self, audiosPath, start_ms):
        channels = ["bass", "drums", "other", "vocals"]
        threadPool = []
        sound_datas = {}
        for i in range(0, 4):
            sound = AudioSegment.from_file(f"{audiosPath}/{channels[i]}.wav", format="wav")
            sound_datas[channels[i]] = sound
            end_ms = sound.duration_seconds * 1000
            splice = sound[start_ms:end_ms]
            thread = pygame.mixer.Sound(splice.raw_data)
            threadPool.append(threading.Thread(target=MISSTplayer.play_thread, args=(self, i, thread), daemon=True))
            del sound, splice, thread, end_ms

        for thread in threadPool:
            thread.start()

        try:
            MISSThelpers.terminate_thread(self, self.uiThread)
        except:
            pass

        self.uiThread = threading.Thread(target=self.update_UI, args=(f"{audiosPath}/other.wav", start_ms), daemon=True)
        self.uiThread.start()
        self.cur_sound_datas = sound_datas

    def change_pos(self, audiosPath, start_ms):
        channels = ["bass", "drums", "other", "vocals"]
        threadPool = []
        for i in range(0, 4):
            sound = self.cur_sound_datas[channels[i]]
            end_ms = sound.duration_seconds * 1000
            splice = sound[start_ms:end_ms]
            thread = pygame.mixer.Sound(splice.raw_data)
            threadPool.append(threading.Thread(target=MISSTplayer.play_thread, args=(self, i, thread), daemon=True))
            del sound, splice, thread, end_ms

        for thread in threadPool:
            thread.start()

        try:
            MISSThelpers.terminate_thread(self, self.uiThread)
        except:
            pass

        self.uiThread = threading.Thread(target=self.update_UI, args=(f"{audiosPath}/other.wav", start_ms), daemon=True)
        self.uiThread.start()

if __name__ == "__main__":
    player = MISSTplayer()
    player.play("test", 10000)