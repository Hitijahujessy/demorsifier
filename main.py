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
from morsifier.main import MorsifierScreen

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
    translator = ObjectProperty()
    highlight_start_time = NumericProperty(0)

    def __init__(self, **kwargs):
        super(DemorsifierScreen, self).__init__(**kwargs)
        self.sound = Sound()
        self.sound.unload()
        self.translator = SoundTranslator()
        self.highlighter = Clock.create_trigger(self.highlight, 0)

    def translate_to_morse(self):
        self.sound.unload()
        translate_path = self.ids.upload_label.text

        self.translator.load(translate_path)
        morse_code = self.translator.transform_to_morse()

        self.ids.morselabel.text = morse_code  # Placeholder
        self.ids.morselabel.hidden_text = morse_code
        translated_text = mt.translate(morse_code)
        translated_text = translated_text.strip()
        self.ids.morselabel2.text = translated_text
        self.ids.morselabel2.hidden_text = translated_text
        
        
        
        self.sound.load(translate_path)
        self.ids.audio_slider.max = self.sound.track.length
        self.sound.play()

        timestamp_max = datetime.datetime.fromtimestamp(
            self.sound.track.length)
        timestamp_max = timestamp_max.strftime('%M:%S')
        timestamp_current = datetime.datetime.fromtimestamp(
            self.sound.track.get_pos())
        timestamp_current = timestamp_current.strftime('%M:%S')
        self.highlighter()
        self.ids.track_position.text = f"{timestamp_current} | {timestamp_max}"

    def set_downtime(self, char):

        # The sound generator halves the time [ms.TIME_UNIT] when creating the file so we do it again here
        try:
            TIME_UNIT = self.sound._time_unit
        except AttributeError:
            TIME_UNIT = ms.TIME_UNIT / 2
        if char == '.':
            self.downtime = TIME_UNIT
            self.downtime += TIME_UNIT
        elif char == '-':
            self.downtime = TIME_UNIT * 3
            self.downtime += TIME_UNIT
        elif char == ' ':
            self.downtime = TIME_UNIT * 2
        elif char == '/':
            self.downtime = TIME_UNIT * 2

    def get_downtime(self, char) -> float:
        """Returns how much time it takes to go over given morse char"""
        try:
            TIME_UNIT = self.sound._time_unit
        except AttributeError:
            TIME_UNIT = ms.TIME_UNIT / 2
        time = 0
        if char == '.':
            time = TIME_UNIT
        elif char == '-':
            time = TIME_UNIT * 3
        elif char == ' ':
            time = TIME_UNIT * 5
        elif char == '/':
            time = TIME_UNIT * 7
        else:
            return 0
        return time

    def highlight(self, dt):
        
        if not self.highlight_start_time:
            self.highlight_start_time = time.time()
        CURRENT_TIME = time.time() - self.highlight_start_time
        CHAR_INDEX = self.translator.get_track_location(CURRENT_TIME)
        print(CHAR_INDEX)
        
        morse_label = self.ids.morselabel
        text_label = self.ids.morselabel2

        COLOR = "[color=ff0000]"
        COLOR_END = "[/color]"
        next_word = 0
        try:
            morse_label.text = morse_label.hidden_text[:CHAR_INDEX] + COLOR + morse_label.hidden_text[CHAR_INDEX] + COLOR_END + morse_label.hidden_text[CHAR_INDEX+1:]
            if morse_label.hidden_text[CHAR_INDEX] == "/":
                next_word = 1
        except IndexError:
            """End of string reached"""
        
        

        word_index = 0
        word_start = 0
        split_text = text_label.text.split(" ")
        for i, word in enumerate(split_text):
            if COLOR not in text_label.text:
                break
            if COLOR in word:
                word_index = i + next_word
                word_start = list(text_label.text).index("[")
                break
        
        if COLOR in split_text[word_index]:
            word_start -= len(COLOR)
        if COLOR_END in split_text[word_index]:
            word_start -= len(COLOR_END)
        end_word = len(split_text[word_index]) + word_start

        text_label.text = text_label.hidden_text[:word_start] + COLOR + \
            text_label.hidden_text[word_start:end_word] + \
            COLOR_END + text_label.hidden_text[end_word:]
            
        if CURRENT_TIME > len(self.translator.data):
            self.highlight_start_time = 0
            
        if self.sound().state == "play":
            self.highlighter()

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
            if self.test_sound():
                self.test_sound.unload()
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
            anim.start(self.ids.scroll_view)
        elif self.scrollview_no == 2:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .25}, size_hint=(.95, .05), duration=.1)
            anim.start(self.ids.scroll_view2)

    def maximize_label(self):
        if self.scrollview_no == 1:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .4325}, size_hint=(.95, .25), duration=.1)
            anim.start(self.ids.scroll_view)
        elif self.scrollview_no == 2:
            anim = Animation(
                pos_hint={"x": .92, "center_y": .15}, size_hint=(.95, .25), duration=.1)
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

    def update_slider(self, dt):
        Clock.schedule_once()


class LoadDialog(Widget):
    load = ObjectProperty()
    text_input = ObjectProperty()
    cancel = ObjectProperty()


class DemorsifierApp(App):

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(MorsifierScreen(name="morsifier"))
        sm.add_widget(DemorsifierScreen(name="demorsifier"))
        return sm


class MenuScreen(Screen):
    pass


DemorsifierApp().run()
DemorsifierScreen().delete_file()
