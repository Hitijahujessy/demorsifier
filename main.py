import morse_code_sound as ms
from morse_code_sound import Sound
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.app import App
import os
import platform
import shutil

import kivy
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

REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# threading multiprocessing


class MainWidget(Widget):
    morse_string = ObjectProperty()
    text_string = ObjectProperty()
    clipboard = ObjectProperty()
    loop = BooleanProperty(False)
    sound = BooleanProperty(True)
    savefile = ObjectProperty(None)
    test_sound = ObjectProperty(None)
    downtime = NumericProperty(0)
    wpm = NumericProperty(12)
    downtime_sum = NumericProperty(0)
    flashlight_color = ObjectProperty((0, 0, 0, 1))

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.typewriter = Clock.create_trigger(self.type_morse, self.downtime)
        self.morse_loop = Clock.create_trigger(self.repeat, self.downtime)
        self.test_sound = Sound(" ", wpm=12)
        self.create_buttons()

    def translate_to_morse(self):
        self.morse_string = self.create_morse_string(self.text_string)
        self.create_labels(self.morse_string)
        # Make sure that copy_morse copies the correct string
        self.clipboard = self.morse_string
        ms.create_wav_file(self.morse_string)
        self.test_sound.set_morse_string(self.morse_string)
        self.test_sound.play()

    def create_labels(self, string_to_label):
        string_list = []
        MAX_CHAR = 25
        lines = 1 + len(string_to_label) // MAX_CHAR

        while lines > 0:
            n = 0
            line = None
            while not line:
                try:
                    if string_to_label[MAX_CHAR+1-n] == " ":
                        line = string_to_label[:MAX_CHAR+1-n]
                    else:
                        n += 1
                        if n > 6:
                            print("n shouldnt be higher than 6, n ==: " + str(n))
                except IndexError:
                    line = string_to_label[:]
            string_to_label = string_to_label[MAX_CHAR+1-n:]
            string_list.append(line)
            lines -= 1
            if string_to_label == "":
                break

        print(string_list)

        for i, string in enumerate(string_list):
            morse_label = Factory.MorseLabel()
            self.ids.scroll_layout.add_widget(morse_label)
            morse_label.hidden_text = ''.join(string)
            morse_label.id = "morse" + str(i)

    def get_label(self):
        """Returns a label if its displayed text is different than its hidden text"""
        for label in reversed(self.ids.scroll_layout.children):
            if label.text == label.hidden_text:
                continue
            # print(label.id)
            return label
        print("no labels have a hidden text")

    def delete_labels(self):
        temp = self.ids.scroll_layout.children[:]
        for label in temp:
            self.ids.scroll_layout.remove_widget(label)
        if len(self.ids.scroll_layout.children) == 0:
            print("succesfully deleted all scroll labels")
        else:
            for label in self.ids.scroll_layout.children:
                print("failed to delete label:" + label.id)

    def create_buttons(self):
        """Create wpm buttons"""
        speed_list = [6, 8, 10, 12, 14, 16, 20, 22, 24, 26]
        for speed in speed_list:
            button = Factory.SpeedButton()
            self.ids.button_grid.add_widget(button)
            button.text = str(speed)

    def update_buttons(self):
        for button in self.ids.button_grid.children:
            button.disabled = False
        for button in self.ids.button_grid.children:
            if button.text == str(self.test_sound.wpm):
                button.disabled = True
                break

    def create_morse_string(self, string):
        string = string.strip()
        string = string.replace(" ", "+")
        string = string.replace(".", "·")
        string = string.replace("-", "–")
        string = string.replace("/", "|")
        for char in string:
            if char in MORSE_CODE_DICT:
                string = string.replace(
                    char, MORSE_CODE_DICT[char] + " ")
        string = string.replace(" +", " / ")
        string = string.replace("+", "")

        return string

    def type_morse(self, dt):
        label = self.get_label()
        if label:
            self.morse_string = label.hidden_text
            index = len(label.hidden_text) - len(label.text)
            label.text += label.hidden_text[-index]
            self.set_downtime(label.text[-1])
            if label.text == label.hidden_text:
                self.scroll(label)
            if self.ids.morse_light.active == True:
                if label.text[-1] == "." or label.text[-1] == "-":
                    self.set_light_bar(self.get_downtime(label.text[-1])+self.test_sound._time_unit/6)

            self.typewriter = Clock.create_trigger(
                self.type_morse, self.downtime)
            self.typewriter()

        else:
            print("finished type writing")
            self.downtime = 0
            self.loop_toggle()

    def repeat(self, dt):
        self.typewriter.cancel()

        if self.test_sound().state == "stop":
            self.test_sound.restart()
            self.scroll(self.ids.scroll_layout.children[-1])

        # Highlight the next character in red
        # t returns a string that tells you how it finished
        t = self.highlight()

        # Will set the downtime according the next occuring character
        # If there is none then the downtime will be set to 2
        try:
            self.set_downtime(self.morse_string[0])
        except IndexError:
            self.downtime = 2
        self.morse_loop = Clock.create_trigger(self.repeat, self.downtime)
        

        # Flash light if its active
        if self.ids.morse_light.active is True:
            if self.morse_string[0] == "." or self.morse_string[0] == "-":
                self.set_light_bar(self.get_downtime(self.morse_string[0])+self.test_sound._time_unit/6)

        # Remove the first character of the string
        self.morse_string = self.morse_string[1:]
        self.morse_loop()
        
        # If the morse string is finished decide if it will loop again
        if len(self.morse_string) == 0:
            self.downtime = self.test_sound._time_unit * 7
            self.morse_loop.cancel()
            self.morse_loop = Clock.create_trigger(self.repeat, self.downtime)
            self.morse_loop()
            if self.ids.loop_toggle.state == "down":
                self.morse_string = self.clipboard
            else:
                self.morse_loop.cancel()
            # make sure the label texts are correctly set
            for label in self.ids.scroll_layout.children:
                label.text = label.hidden_text[:]

    def set_downtime(self, char):

        # The sound generator halves the time [ms.TIME_UNIT] when creating the file so we do it again here
        try: 
            TIME_UNIT = self.test_sound._time_unit
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
            TIME_UNIT = self.test_sound._time_unit
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

    def change_tempo(self, wpm):
        self.test_sound.stop()
        self.test_sound.change_speed(wpm)

        for label in self.ids.scroll_layout.children:
            if "[color" in label.text:
                label.text = label.hidden_text
                self.morse_loop.cancel()
                self.check_loop()
                break
            elif label.text != label.hidden_text and label.text != "":
                for label in self.ids.scroll_layout.children:
                    label.text = ""
                self.test_sound.restart()
                print(self.test_sound().state)
                break

    def highlight(self):
        next_label = self.ids.scroll_layout.children[-1]
        do_next_label = False
        for label in reversed(self.ids.scroll_layout.children):
            # Check which label the highlight is currently in
            if "[color=ff0000]" in label.text:
                i = list(label.text).index("[") + 1
                try:
                    label.text = label.hidden_text[:i] + "[color=ff0000]" + \
                        label.hidden_text[i] + "[/color]" + \
                        label.hidden_text[i+1:]
                    return "changed inline highlight at index: " + str(i) + " of label: " + str(label.id)
                except IndexError:
                    label.text = label.hidden_text[:]
                    do_next_label = True
            elif do_next_label:
                next_label = label
                self.scroll(label)
                break

        if len(self.ids.scroll_layout.children) > 0:
            if next_label.id == "morse0" and do_next_label is True:
                return "Got to the end of the loop"
            else:
                next_label.text = "[color=ff0000]" + next_label.hidden_text[0] + \
                    "[/color]" + next_label.hidden_text[1:]
                return "started highlight at index 0 of the label: " + str(next_label.id)
        else:
            print("No scroll labels exist")

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
        self.check_loop = Clock.create_trigger(self.activate_loop, 0)
        if check.state == "normal":
            self.loop = False
        elif check.state == "down":
            try:
                self.scroll(self.ids.scroll_layout.children[-1])
            except IndexError:
                pass
            self.check_loop()

    def activate_loop(self, dt):
        """Waits for the full morse string to appear on screen"""
        if len(self.ids.scroll_layout.children) > 0:
            listx = [True if x.text ==
                     x.hidden_text else False for x in self.ids.scroll_layout.children]
            if False in listx:
                self.check_loop()
            else:
                self.morse_string = self.clipboard
                self.loop = True
                self.morse_loop()
        else:
            self.check_loop()
        if self.ids.loop_toggle.state == "normal":
            self.check_loop.cancel()

    def do_proceed(self):
        if self.ids.scroll_layout.children[-1].text == '':
            self.downtime = 0
            self.typewriter = Clock.create_trigger(
                self.type_morse, self.downtime)
            self.typewriter()
        else:
            self.morse_loop()

    def mute_sound(self):
        if self.test_sound:
            if self.sound is True:
                self.sound = False
                self.test_sound.mute()
            else:
                self.sound = True
                self.test_sound.unmute()

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

    def show_save(self):
        if os.path.exists("./sounds/morse_code.wav"):
            content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
            self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
            self._popup.open()
        

    def save(self, path, filename):
        src_dir = "sounds/morse_code.wav"
        dst_dir = path + "//" + filename + ".wav"
        shutil.copy(src_dir, dst_dir)

        self.dismiss_popup()


class SaveDialog(Widget):
    save = ObjectProperty()
    text_input = ObjectProperty()
    cancel = ObjectProperty()


class MorsifierApp(App):
    MainWidget = MainWidget()

    def build(self):
        return self.MainWidget


MorsifierApp().run()
MainWidget().delete_file()
