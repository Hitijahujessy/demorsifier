import datetime
import os
import platform
import time

import kivy
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
                             StringProperty)
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen

import morse_code_sound as ms
import morse_translator as mt
from morse_code_sound import Sound, SoundTranslator
from morsifier_main import MorsifierScreen

kivy.require("2.1.0")

if "macOS" in platform.platform():
    root_widget = Builder.load_file('app.kv')
    os.environ["KIVY_AUDIO"] = "audio_sdl2"
else:
    # Enable to prevent OpenGL error
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
    root_widget = Builder.load_file('app.kv')

MORSE_CODE_DICT = {'A': '.-', 'B': '-...',
                   'C': '-.-.', 'D': '-..', 'E': '.',
                   'F': '..-.', 'G': '--.', 'H': '....',
                   'I': '..', 'J': '.---', 'K': '-.-',
                   'L': '.-..', 'M': '--', 'N': '-.',
                   'O': '---', 'P': '.--.', 'Q': '--.-',
                   'R': '.-.', 'S': '...', 'T': '-',
                   'U': '..-', 'V': '...-', 'W': '.--',
                   'X': '-..-', 'Y': '-.--', 'Z': '--..',
                   '1': '.----', '2': '..---', '3': '...--',
                   '4': '....-', '5': '.....', '6': '-....',
                   '7': '--...', '8': '---..', '9': '----.',
                   '0': '-----', ',': '--..--', '·': '.-.-.-',
                   '?': '..--..', '|': '-..-.', '–': '-....-',
                   '(': '-.--.', ')': '-.--.-', "'": '.----.',
                   '"': '.-..-.', '!': '-·-·--'}


class DemorsifierScreen(Screen):
    morse_string = ObjectProperty("")
    text_string = ObjectProperty("")
    clipboard = ObjectProperty("")
    loop = BooleanProperty(False)
    sound = BooleanProperty(True)
    downtime = NumericProperty(0)
    downtime_sum = NumericProperty(0)
    flashlight_color = ObjectProperty((0, 0, 0, 1))
    upload_label = ObjectProperty()
    pause_position = 0
    translator = ObjectProperty()
    highlight_start_time = NumericProperty(0)
    highlight_time_list = []
    char_index = -1
    time_index = -1

    def __init__(self, **kwargs):
        super(DemorsifierScreen, self).__init__(**kwargs)
        self.sound = Sound()
        self.translator = SoundTranslator()
        self.highlighter = Clock.create_trigger(self.highlight, 0)

        # v Testing stuff v
        self.test_sound = Sound()
        self.test_sound.load("sounds/imports/w1aw-nov-09-80m-snip.wav")
        self.update_soundpos = Clock.create_trigger(self.update_timestamp, .1)

        translator = SoundTranslator("sounds/imports/w1aw-nov-09-80m-snip.wav")
        morse_string = translator.transform_to_morse()
        print(morse_string)
        mt.translate(morse_string)

    def translate_to_morse(self):
        self.sound.unload()
        translate_path = self.ids.upload_label.text

        self.translator.load(translate_path)
        morse_code = self.translator.transform_to_morse()

        self.ids.morselabel_upper.text = morse_code  # Placeholder
        self.ids.morselabel_upper.hidden_text = morse_code
        translated_text = mt.translate(morse_code)
        translated_text = translated_text.strip()
        self.ids.morselabel_lower.text = translated_text
        self.ids.morselabel_lower.hidden_text = translated_text

        self.sound.load(translate_path)
        self.ids.audio_slider.max = self.sound.track.length
        self.sound.play()
        self.highlighter()

        timestamp_max = datetime.datetime.fromtimestamp(
            self.sound.track.length)
        timestamp_max = timestamp_max.strftime('%M:%S')

        self.ids.track_position.text = f"00:00 | {timestamp_max}"

    def update_timestamp(self, dt):
        timestamp_max = datetime.datetime.fromtimestamp(
            self.sound.track.length)
        timestamp_max = timestamp_max.strftime('%M:%S')

        self.ids.track_position.text = f"{self.sound.get_current_position()} | {timestamp_max}"

        self.ids.audio_slider.value = self.sound.track.get_pos()

        # if self.sound.track.state == "stop":
        #     self.ids.play_pause.state = "normal"

        self.update_soundpos()
        timestamp_current = datetime.datetime.fromtimestamp(
            self.sound.track.get_pos())
        timestamp_current = timestamp_current.strftime('%M:%S')
        self.highlighter()
        self.ids.track_position.text = f"{timestamp_current} | {timestamp_max}"

    def highlight(self, dt):

        # Set the starting variables
        if not self.highlight_start_time:
            self.highlight_start_time = time.time()
        if not self.highlight_time_list:
            self.highlight_time_list = self.translator.get_time_list()
        if self.char_index < 0 or self.char_index >= len(self.ids.morselabel_upper.hidden_text):
            self.char_index = 0
        if self.time_index < 0:
            self.time_index = 0

        CURRENT_TIME = time.time() - self.highlight_start_time
        morse_label = self.ids.morselabel_upper
        text_label = self.ids.morselabel_lower
        COLOR = "[color=ff0000]"
        COLOR_END = "[/color]"

        # create the timer for the next loop
        time_pos = self.highlight_time_list[int(self.time_index)]
        if time_pos is not self.highlight_time_list[-1]:
            time_delta = time_pos - self.highlight_time_list[int(
                self.time_index)-1]
        else:
            time_delta = 0
        self.highlighter = Clock.create_trigger(self.highlight, time_delta)

        # UPDATE MORSE LABEL
        while morse_label.hidden_text[int(self.char_index)] == " ":
            self.char_index+=1
        try:
            morse_label.text = morse_label.hidden_text[:int(self.char_index)] + COLOR + \
                morse_label.hidden_text[int(self.char_index)] + COLOR_END + \
                morse_label.hidden_text[int(self.char_index)+1:]
        except IndexError:
            """End of string reached"""
        if morse_label.hidden_text[int(self.char_index)] == "/":
            self.char_index +=1
            self.time_index -=1

        # UPDATE TEXT LABEL

        # count the spaces
        i = morse_label.text.index("[")
        space_count = len(
            list(val for val in morse_label.hidden_text[:i] if val == "/"))

        # get the first and end index for the word to highlight
        split_hidden_text = text_label.hidden_text.split(" ")
        word_start = 0
        for i, word in enumerate(split_hidden_text):
            if i == space_count:
                break
            word_start += len(word) + 1
        word_end = word_start + len(split_hidden_text[space_count])

        # Update the label
        text_label.text = text_label.hidden_text[:word_start] + COLOR + \
            text_label.hidden_text[word_start:word_end] + \
            COLOR_END + text_label.hidden_text[word_end:]

        # update the index to be the next one
        self.char_index += 1
        self.time_index += 1
        
        if self.time_index == len(self.highlight_time_list):
            self.reset_highlight()

        if self.sound().state == "play":
            self.highlighter()
        else:
            self.reset_highlight()

    def reset_highlight(self):
        self.ids.morselabel_upper.text = self.ids.morselabel_upper.hidden_text
        self.ids.morselabel_lower.text = self.ids.morselabel_lower.hidden_text
        self.highlight_time_list = []
        self.highlight_start_time = 0
        self.char_index = -1
        self.time_index = -1

    def scroll(self, label):
        self.ids.scroll_view.scroll_to(label)

    def set_light_bar(self, dt):
        if self.ids.morse_light.state == "down":
            if self.flashlight_color == (0, 0, 0, 1):
                self.flashlight_color = (1, 1, 1, 1)
                deactivate = Clock.schedule_once(self.set_light_bar, dt)
            elif self.flashlight_color == (1, 1, 1, 1):
                self.flashlight_color = (0, 0, 0, 1)

    def loop_toggle(self):
        self.sound.toggle_loop()
        check = self.ids.loop_toggle
        self.check_loop = Clock.create_trigger(self.activate_loop, 0)
        if check.state == "normal":
            self.loop = False
        elif check.state == "down":
            try:
                self.scroll(self.ids.scroll_layout.children[0])
                self.scroll(self.ids.scroll_layout2.children[0])
            except IndexError:
                pass
            self.check_loop()

    def activate_loop(self, dt):
        """Waits for the unaltered full morse string to appear on screen"""
        if len(self.ids.scroll_layout.children) > 0:
            listx = (True if x.text ==
                     x.hidden_text else False for x in self.ids.scroll_layout.children)
            if False in listx:
                self.check_loop()
            else:
                self.morse_string = self.clipboard
                self.loop = True
        else:
            self.check_loop()
        if self.ids.loop_toggle.state == "normal":
            self.check_loop.cancel()

    def do_proceed(self):
        if self.ids.scroll_layout.children[-1].text == '':
            self.downtime = 0

    def mute_sound(self):
        if self.sound:
            if self.sound().volume > 0:
                self.sound.mute()
            else:
                self.sound.unmute()

    def delete_file(self, f="./sounds/morse_code.wav"):
        if os.path.exists(f):
            if self.sound():
                self.sound.unload()
            os.remove(f)

        else:
            print("failed to delete: ", f)
            print("file not found")

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):

        self.dismiss_popup()

    def minimize_label(self):
        if self.scrollview_no == 1:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .5325}, size_hint=(.95, .05), duration=.1)
            anim2 = Animation(opacity=0, duration=.1)
            anim2.start(self.ids.morselabel_upper)
            anim.start(self.ids.scroll_view)

        elif self.scrollview_no == 2:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .25}, size_hint=(.95, .05), duration=.1)
            anim2 = Animation(opacity=0, duration=.1)
            anim2.start(self.ids.morselabel_lower)
            anim.start(self.ids.scroll_view2)

    def maximize_label(self):
        if self.scrollview_no == 1:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .4325}, size_hint=(.95, .25), duration=.1)
            anim2 = Animation(opacity=1, duration=.1)
            anim2.start(self.ids.morselabel_upper)
            anim.start(self.ids.scroll_view)

        elif self.scrollview_no == 2:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .15}, size_hint=(.95, .25), duration=.1)
            anim2 = Animation(opacity=1, duration=.1)
            anim2.start(self.ids.morselabel_lower)
            anim.start(self.ids.scroll_view2)

    def play_audio(self):
        try:
            self.sound = ms.Sound()
            self.sound.load(self.ids.upload_label.text)

        except Exception as e:
            print(e)
        try:
            self.sound.play()
            while self.sound().state == "play":
                self.ids.audio_slider.value = self.sound.get_current_position()
                if self.ids.audio_slider.value > 0.99:
                    break
        except Exception as e:
            print(e)

    def pause_audio(self):
        self.pause_position = self.sound.track.get_pos()
        self.sound.stop()

    def resume_audio(self):
        if self.pause_position != 0:
            self.play_audio()
        elif self.ids.play_pause.state == "down":
            # self.pause_audio()
            # f self.sound.track.state == "stop":
            self.sound.set_position(self.sound.track.get_pos())
            self.play_audio()
        elif self.ids.play_pause.state == "normal":
            self.pause_audio()


class LoadDialog(Widget):
    load = ObjectProperty()
    text_input = ObjectProperty()
    cancel = ObjectProperty()


class DemorsifierApp(App):

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(DemorsifierScreen(name="demorsifier"))
        sm.add_widget(MorsifierScreen(name="morsifier"))
        return sm


class MenuScreen(Screen):
    pass


DemorsifierApp().run()
DemorsifierScreen().delete_file()
