import struct
import wave
import os
import scipy

from kivy.core.audio import SoundLoader
import numpy as np
from pydub import AudioSegment

RATE = 44100


def sine_samples(freq, dur):
    x = (2*np.pi*freq/RATE) * np.arange(RATE*dur)

    sine = (32767*np.sin(x)).astype(int)

    as_packed_bytes = (map(lambda v: struct.pack('h', v), sine))
    return as_packed_bytes


def output_wave(path, frames):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), path))
    output = wave.open(path, 'w')
    output.setparams((2, 2, RATE, 0, 'NONE', 'not compresses'))
    output.writeframes(frames)
    output.close()


def output_sound(path, freq, dur):
    frames = b''.join(sine_samples(freq, dur))

    output_wave(path, frames)



def create_sounds(time_unit):
    time_unit *= 2
    output_sound('sounds/sine320s.wav', 320, time_unit)  # .
    output_sound('sounds/sine320l.wav', 320, time_unit * 3)  # -
    output_sound('sounds/sine0.wav', 0, time_unit)  # /
    print("Created wav files with TIME_UNIT: " + str(time_unit))
TIME_UNIT = 0.2
create_sounds(TIME_UNIT)

def create_wav_file(morse_string):
    play_sound = AudioSegment.from_wav('sounds/sine0.wav')
    tone_short = AudioSegment.from_wav('sounds/sine320s.wav')
    tone_long = AudioSegment.from_wav('sounds/sine320l.wav')
    tone_silent = AudioSegment.from_wav('sounds/sine0.wav')
    
    for i, morse in enumerate(morse_string):
        if morse == '.':
            play_sound += tone_short
            try:
                if morse_string[i+1] == "." or morse_string[i+1] == "-":
                    play_sound += tone_silent
            except IndexError:
                pass
            
        elif morse == '-':
            play_sound += tone_long
            try:
                if morse_string[i+1] == "." or morse_string[i+1] == "-":
                    play_sound += tone_silent
            except IndexError:
                pass
            
        elif morse == ' ':
            try:
                if morse_string[i+1] == "/":
                    play_sound += tone_silent * 7
                elif morse_string[i-1 if i > 0 else i] == "/":
                    continue
                else:
                    play_sound += tone_silent * 3
            except IndexError:
                pass        
        
    play_sound.export("sounds/morse_code.wav", format='wav')

class Sound():
    def __init__(self, morse_string: str, wpm) -> None:
        self.morse_string = morse_string
        self.wpm = wpm
        self._time_unit = self.wpm_to_time_unit(self.wpm)
        # Create the right length dits and dots
        create_sounds(self._time_unit)
        # Then create the right morse wav file
        create_wav_file(self.morse_string)
        self.load()
        
    def __call__(self):
        return self.track
        
    def wpm_to_time_unit(self, wpm: float):
        time_unit = 60/(50*wpm)
        return time_unit
    
    def change_speed(self, wpm):
        self.unload()
        self.wpm = wpm
        self._time_unit = self.wpm_to_time_unit(wpm)
        create_sounds(self._time_unit)
        create_wav_file(self.morse_string)
        self.load()
        
    def set_morse_string(self, morse_string, wpm=None):
        self.morse_string = morse_string
        if wpm:
            self.change_speed(wpm)
    
    def load(self, path="./sounds/morse_code.wav"):
        if os.path.exists(path):
            self.track = SoundLoader.load(path)
        else:
            print(path + " does not exist")
        
    def unload(self):
        try:
            self.track.unload()
        except:
            print("Couldnt unload track")
            
    def play(self):
        try:
            self.track.play()
            print("Now playing with volume: " + str(self.track.volume))
        except:
            print("Couldnt play the track")
    
    def stop(self):
        try:
            self.track.stop()
        except:
            print("Couldnt stop the track")
        
    def restart(self):
        self.play()
    
    def mute(self):
        self.track.volume = 0
        
    def unmute(self):
        self.track.volume = 1
        
class SoundTranslator():
    def __init__(self, path):
        self.path = path
        self.name = path
    
    def load(self):
        self.sound = Sound(" ", 0)
        self.sound.load(self.path)