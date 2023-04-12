import os
import struct
import wave
from os.path import join as pjoin

import matplotlib.pyplot as plt
import morse_translator as mt
import numpy as np
import scipy.io
import soundfile as sf
from kivy.core.audio import SoundLoader
from pydub import AudioSegment
from scipy.io import wavfile

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
# create_sounds(TIME_UNIT)


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

    def get_current_position(self):
        if self.track.state == "stop":
            return 0

        percentage = self.track.get_pos() / self.track.length
        return percentage

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
    
    def toggle_loop(self):
        if self.track.loop:
            self.track.loop = False
            self.track.stop()
        elif not self.track.loop:
            self.track.loop = True
            self.track.stop()
            self.track.play()

class SoundTranslator():
    def __init__(self, path: str):
        self.path = path
        self.name = path
        self.data, self.samplerate, self.length = None, None, None
        self.audio_time_list, self.audio_ticks_list, self.silence_ticks_list, self.silence_time_list = None, None, None, None
        self.dit, self.dah = [], []
        self.morse_text = None
        self.zero_buffer = 0

    def __del__(self):
        self.remove_wav_file()

    def transform_to_right_wav(self):
        data_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "sounds/imports"))
        old_wav = os.path.abspath(os.path.join(
            os.path.dirname(__file__), self.path))
        new_wav = pjoin(data_dir, 'new.wav')

        # Transform the audio file into a readable wav file
        data, samplerate = sf.read(old_wav)
        sf.write(new_wav, data, samplerate, subtype='PCM_16')

    def load(self, path=None):
        if path is None:
            self.transform_to_right_wav()
            path = "sounds/imports/new.wav"

        self.samplerate, self.data = wavfile.read(path)
        if len(self.data.shape) == 2:
            print(f"number of channels = {self.data.shape[1]}")
            self.data = self.data[:, 0]
        else:
            print("number of channels = 1")
        self.length = self.data.shape[0] / self.samplerate
        print(f"length = {round(self.length, 4)}s")

        self.zero_buffer = max(self.data) * 0.2
        print(f"Buffer is: {self.zero_buffer}")

    def transform_to_morse(self):
        if self.data is None:
            self.load()
        self.audio_ticks_list = self.get_all_audio_parts()
        self.silence_ticks_list = self.get_all_inbetween_parts()
        self.audio_time_list = self.ticks_to_time(self.audio_ticks_list)
        self.silence_time_list = self.ticks_to_time(self.silence_ticks_list)
        self.dit, self.dah = self.get_dit_and_dah(
            self.audio_time_list)
        self.morse_text = self.time_to_morse()

        return self.morse_text

    def get_dit_and_dah(self, iterable_list: list):
        """Returns the average dit and dah timings"""
        dit, dah = 0, 0
        if len(iterable_list) < 2:
            dit, dah = self.__get_default_dit_and_dah()

        else:
            temp_list = iterable_list[:]
            temp_list.sort()
            dit = min(temp_list)
            dah = dit*3
            for val in temp_list:
                if val > dit and val < dah-dit*1.5:
                    dit = val
                    dah = dit*3

        return dit, dah

    def get_closest_to(self, arguments, values):
        # make sure array is a numpy array
        array = np.array(arguments)

        # get insert positions
        idxs = np.searchsorted(array, values, side="left")

        # find indexes where previous index is closer
        prev_idx_is_less = ((idxs == len(array)) | (np.fabs(
            values - array[np.maximum(idxs-1, 0)]) < np.fabs(values - array[np.minimum(idxs, len(array)-1)])))
        idxs[prev_idx_is_less] -= 1

        return array[idxs]

    def __get_default_dit_and_dah(self):
        return 0.1, 0.3

    def get_silent_length(self, data=None, start_tick=0):
        """Returns the last tick of the silence before it ends"""
        if data is None:
            data = self.data
        try:
            if not self._check_loud_enough(data[start_tick]):
                # print("Not a valid starting position")
                # print("Make sure the starting pos has data")
                return start_tick
        except IndexError:
            # Got the last frame
            return start_tick

        period = 20
        for tick, value in enumerate(data[start_tick:], start_tick):
            if not self._check_loud_enough(value):
                avg_amplitude = np.median(abs(data[tick:tick+period]))
                if not self._check_loud_enough(avg_amplitude):
                    return tick - 1

        # If there is only trailing silent space left of the audio return the last tick
        print(
            f"end of audiofile, returning tick: {tick} at length: {tick / self.samplerate}")
        return tick

    def get_sine_length(self, data=None, start_tick=0):
        """Returns the last tick of the sine before it ends"""
        if data is None:
            data = self.data
        try:
            if self._check_loud_enough(data[start_tick]):
                # print("Not a valid starting position")
                # print("Make sure the starting pos has data")
                return start_tick
        except IndexError:
            # Got the last frame
            return start_tick

        period = 20
        for tick, value in enumerate(data[start_tick:], start_tick):
            # If the current two values pass the noisegate return the previous tick
            if self._check_loud_enough(value):
                avg_amplitude = np.median(abs(data[tick:tick+period]))
                if self._check_loud_enough(avg_amplitude):
                    return tick - 1

        # If there is no trailing silent space left of the audio return the last tick
        print(
            f"end of audiofile, returning tick: {tick} at length: {tick / self.samplerate}")
        return tick

    def get_next_sound_start_and_end(self, data=None, start_pos=0):
        """Seeks the next non-silent audio part until it gets silent again.
        Returns the first and last tick of the audio part."""
        if data is None:
            data = self.data
        # skip the silent part of the audio
        # start where there is frequency by adding 1 to last tick of the silence
        audio_start = self.get_silent_length(data, start_tick=start_pos) + 1
        audio_end = self.get_sine_length(data, start_tick=audio_start)

        return audio_start, audio_end

    def get_all_audio_parts(self, data=None):
        """Returns a list of all parts in the file that has audio"""
        if data is None:
            data = self.data
        audio_start_tick = 0
        audio_end_tick = 0
        audio_ticks_list = []
        # While we havent gone through all ticks
        while audio_end_tick != len(data):
            # Get the next audio part beginning at tick 0, skips audio part for next iteration
            audio_start_tick, audio_end_tick = self.get_next_sound_start_and_end(
                data, audio_end_tick)
            # Making sure to not add empty audio parts to list
            if audio_start_tick != audio_end_tick:
                length = (audio_end_tick - audio_start_tick) / self.samplerate
                if length > 0.01:
                    audio_ticks_list.append([audio_start_tick, audio_end_tick])

        print("Finished finding audio parts.")
        print(f"Found {len(audio_ticks_list)} audio parts")
        return audio_ticks_list

    def get_all_inbetween_parts(self, audio_ticks_list=None):
        """Returns a list of a list of all parts in a list that arent in the list"""
        if audio_ticks_list is None:
            audio_ticks_list = self.audio_ticks_list
        silence_ticks_list = []
        begin = 0
        for start_tick, end_tick in audio_ticks_list:
            # new end tick should be before the old start tick
            silence_ticks_list.append([begin, start_tick - 1])
            begin = end_tick + 1  # New start tick should go 1 after the old end tick
        print(f"Found {len(silence_ticks_list)} silent parts")
        return silence_ticks_list

    def print_audio_and_silence_ticks(self):
        for audio, silence in zip(self.audio_ticks_list, self.silence_ticks_list):
            if silence[0] < audio[0]:
                print(f"{silence}s {audio}a", end=" ")
            else:
                print(f"{audio}a {silence}s", end=" ")

        print("\nWhere s = Silent and a = Audio")

    def ticks_to_time(self, tick_list: list):
        """Returns the time between two values(ticks) in a listed list rounded to 4 decimals"""
        time_list = [round((end-start) / self.samplerate, 4)
                     for start, end in tick_list if round((end-start) / self.samplerate, 4)]
        return time_list

    def time_to_morse(self):
        """Takes the audio_time_list and silence_time_list and turns them into morse according to the current dit & dah values"""
        
        nrml_audio_time_list = []
        for audio in self.audio_time_list:
            nrml_audio_time_list.append(
                *list(self.get_closest_to([self.dit, self.dah], [audio])))
            
        nrml_silence_time_list = []
        for silence in self.silence_time_list:
            nrml_silence_time_list.append(
                *list(self.get_closest_to([self.dit, self.dah, self.dit*14], [silence])))
        
        morse_text = ""
        for audio, silence in zip(nrml_audio_time_list, nrml_silence_time_list):
            # if the silence is shorter than a dah do nothing
            if silence == self.dit:
                morse_text += ""
            # if silence is equal or longer than a dah and shorter than a dah+dit (should be 4xdit)
            elif silence == self.dah:
                morse_text += " "
            else:
                morse_text += " / "

            if audio == self.dit:
                morse_text += "."
            elif audio == self.dah:
                morse_text += "-"

        return morse_text

    def _check_loud_enough(self, value):
        """Evaluates the frequency value to the set buffer. Increase buffer with louder background noise"""
        # I think this is basically a noise gate?
        return bool(-self.zero_buffer < value < self.zero_buffer)

    def remove_wav_file(self):
        path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "sounds/imports/new.wav"))
        if os.path.exists(path):
            os.remove(path)

        else:
            print("failed to delete: ", path)
            print("file not found")


translator = SoundTranslator("sounds/imports/cj3a-60681.mp3")
morse_string = translator.transform_to_morse()
print(morse_string)
mt.translate(morse_string)
