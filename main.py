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
    loop = BooleanProperty(False)
    flashlight_color = ObjectProperty((0, 0, 0, 1))
    upload_label = ObjectProperty()
    pause_position = 0
    mute = False
    sound = Sound()
    translator = SoundTranslator()

    def __init__(self, **kwargs):
        super(DemorsifierScreen, self).__init__(**kwargs)
        self.update_soundpos = Clock.create_trigger(self.update_timestamp, .1)

    def translate_to_morse(self):
        self.sound.unload()
        translate_path = self.ids.upload_label.hidden_text

        self.translator.load(translate_path)

        morse_code = self.translator.transform_to_morse()
        self.ids.morselabel_upper.text = morse_code  # Placeholder
        self.ids.morselabel_upper.hidden_text = morse_code
        translated_text = mt.translate(morse_code)
        translated_text = translated_text.strip()
        self.ids.morselabel_lower.text = translated_text
        self.ids.morselabel_lower.hidden_text = translated_text

        self.sound.load(translate_path)
        track_len = self.sound.track.length
        self.ids.audio_slider.max = track_len

        timestamp_max = datetime.datetime.fromtimestamp(
            self.sound.track.length)
        timestamp_max = timestamp_max.strftime('%M:%S')

        self.ids.track_position.text = f"00:00 | {timestamp_max}"

    def update_timestamp(self, dt):
        timestamp_max = datetime.datetime.fromtimestamp(
            self.sound.track.length)
        timestamp_max = timestamp_max.strftime('%M:%S')

        if self.sound.get_current_position() != 0:
            self.ids.track_position.text = f"{self.sound.get_current_position()} | {timestamp_max}"
        else:
            self.ids.track_position.text = f"{self.sound.get_current_position()} | {timestamp_max}"

        self.ids.audio_slider.value = self.sound.track.get_pos()

        if self.sound.track.state == "stop":
            self.ids.play_pause.state = "normal"
            self.sound.set_position(0)
            self.ids.track_position.text = f"00:00 | {timestamp_max}"
            self.ids.audio_slider.value = 0
        else:

            timestamp_current = datetime.datetime.fromtimestamp(
                self.sound.track.get_pos())
            timestamp_current = timestamp_current.strftime('%M:%S')
            self.ids.track_position.text = f"{timestamp_current} | {timestamp_max}"
            self.update_soundpos()

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
        check = self.ids.loop_toggle
        self.check_loop = Clock.create_trigger(self.activate_loop, 0.1)
        self.loop_update = Clock.create_trigger(self.update_loop, 0)
        if check.state == "normal":
            self.loop = False
            self.sound.toggle_loop(state="False")
        elif check.state == "down":
            try:
                self.scroll(self.ids.scroll_layout.children[0])
                self.scroll(self.ids.scroll_layout2.children[0])
            except IndexError as e:
                print(e)
            self.check_loop()
            self.loop_update()

    def activate_loop(self, dt):
        """Waits for the unaltered full morse string to appear on screen"""
        if self.ids.audio_slider.value >= self.sound.track.length*0.99:
            self.loop = True
            self.sound.toggle_loop(state="True")
            self.ids.play_pause.state = "down"
        else:
            self.check_loop()
        if self.ids.loop_toggle.state == "normal":
            self.check_loop.cancel()
            
    def update_loop(self, dt):
        if self.loop:
            
            self.loop_update()

    def mute_sound(self):
        if self.sound:
            if self.sound().volume > 0:
                self.sound.mute()
            else:
                self.sound.unmute()

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
    
    def load(self):
        
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
            self.sound.play()
        except Exception as e:
            print(e)

    def pause_audio(self):
        self.pause_position = self.sound.track.get_pos()
        self.sound.stop()
        print(self.pause_position)

    def resume_audio(self):

        if self.ids.play_pause.state == "down":
            self.play_audio()
            self.sound.set_position(self.pause_position)
            self.pause_position = 0
        elif self.ids.play_pause.state == "normal":
            self.pause_audio()
            if self.pause_position == 0:
                self.play_audio()
                self.sound.set_position(0)


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
