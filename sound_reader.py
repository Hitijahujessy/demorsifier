from os.path import join as pjoin

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy.io import wavfile

data_dir = "sounds\\imports"
old_wav = pjoin(data_dir, 'foreign.wav')
new_wav = pjoin(data_dir, 'new.wav')

# Transform the audio file into a readable wav file
data, samplerate = sf.read(old_wav)

sf.write(new_wav, data, samplerate, subtype='PCM_16')


samplerate, data = wavfile.read(new_wav)
if len(data.shape) == 2:
    print(f"number of channels = {data.shape[1]}")
    data = data[:, 0]
else:
    print(f"number of channels = 1")
length = data.shape[0] / samplerate
print(f"length = {length}s")


peak = max(data)
valley = min(data)


def get_period(data):
    start = None
    end = None
    for index, value in enumerate(data):
        if value == peak and start is None:
            start = index

        elif value == peak and start is not None:
            end = index

        if start and end:
            val = data[(end - start) + index]
            if val == peak:
                return (end - start)
            else:
                start, end = None, None


period = get_period(data)
print(period / samplerate)


def get_1st_and_2nd_lowest_value(iterable_list):
    minv1 = min(iterable_list)
    minv2 = min([val for val in iterable_list if val != minv1])
    print(f"minv1 == {minv1} | minv2 == {minv2}")
    return minv1, minv2


def get_silent_length(data=data, start_tick=0):
    """Returns the last tick of the silence before it ends"""
    try:
        if data[start_tick] != 0:
            # print("Not a valid starting position")
            # print("Make sure the starting pos has data")
            return start_tick
    except IndexError:
        # Got the last frame
        return start_tick

    for tick, value in enumerate(data[start_tick:]):
        if value != 0:
            return tick - 1 + start_tick
    # If there is only trailing silent space left of the audio return the last tick
    print(
        f"end of audiofile, returning tick: {tick} at length: {tick / samplerate}")
    return tick + start_tick


def get_sine_length(data=data, start_tick=0):
    """Returns the last tick of the sine before it ends"""
    try:
        if data[start_tick] == 0:
            # print("Not a valid starting position")
            # print("Make sure the starting pos has data")
            return start_tick
    except IndexError:
        # Got the last frame
        return start_tick

    for tick, value in enumerate(data[start_tick:]):
        # If the current two values are 0 return the previous tick
        if value == 0 and data[tick+1+start_tick] == 0:
            return tick - 1 + start_tick

    # If there is no trailing silent space left of the audio return the last tick
    print(
        f"end of audiofile, returning tick: {tick + 1 + start_tick} at length: {(tick + 1 + start_tick) / samplerate}")
    return tick + 1 + start_tick


def get_next_sound_start_and_end(data=data, start_pos=0):
    """seeks the next non-silent audio part until it gets silent again.
    Returns the first and last tick of the audio part."""
    audio_start = get_silent_length(data, start_tick=start_pos) + 1
    audio_end = get_sine_length(data, start_tick=audio_start)

    return audio_start, audio_end


def get_all_audio_parts(data=data):
    audio_start_tick = 0
    audio_end_tick = 0
    audio_ticks_list = []
    while audio_end_tick != len(data):
        audio_start_tick, audio_end_tick = get_next_sound_start_and_end(
            data, audio_end_tick)
        if audio_start_tick != audio_end_tick:
            audio_ticks_list.append([audio_start_tick, audio_end_tick])
    print("Finished finding audio parts.")
    print(f"Found {len(audio_ticks_list)} audio parts")
    return audio_ticks_list


audio_ticks_list = get_all_audio_parts()


def get_all_inbetween_parts(audio_ticks_list):
    silence_ticks_list = []
    begin = 0
    for start_tick, end_tick in audio_ticks_list:
        silence_ticks_list.append([begin, start_tick - 1])
        begin = end_tick + 1
    return silence_ticks_list


silence_ticks_list = get_all_inbetween_parts(audio_ticks_list)

def print_audio_and_silence_ticks(audio_ticks_list, silence_ticks_list):
    for audio, silence in zip(audio_ticks_list, silence_ticks_list):
        if silence[0] < audio[0]:
            print(f"{silence}s {audio}a", end=" ")
        else:
            print(f"{audio}a {silence}s", end=" ")

    print("\nWhere s = Silent and a = Audio")

print_audio_and_silence_ticks(audio_ticks_list, silence_ticks_list)

def ticks_to_time(tick_list):
    time_list = [round((end-start)/ samplerate, 4) for start, end in tick_list]
    return time_list

def ticks_to_morse(audio_time_list, silence_time_list, dit, dah):
    morse_text = ""
    for audio, silence in zip(audio_time_list, silence_time_list):
        if silence == dit:
            morse_text += ""
        elif silence == dah:
            morse_text += " "
        else:
            morse_text += " / "
        
        if audio == dit:
            morse_text += "."
        elif audio == dah:
            morse_text += "-"
    print(morse_text)

audio_time_list = ticks_to_time(audio_ticks_list)
silence_time_list = ticks_to_time(silence_ticks_list)
dit, dah = get_1st_and_2nd_lowest_value(audio_time_list)
ticks_to_morse(audio_time_list, silence_time_list, dit, dah)

time = np.linspace(0., length, data.shape[0])
plt.plot(time, data, label="Left channel")
plt.plot(time, data, label="Right channel")
# plt.plot(time_list)
plt.legend()
plt.xlabel("Time [s]")
plt.ylabel("Amplitude")
plt.show()
