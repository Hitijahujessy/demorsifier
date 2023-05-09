from threading import Thread
import time
import numpy as np
import pygame

import morse_translator as mt

def get_closest_to( arguments, values) -> list:
        # make sure array is a numpy array
        array = np.array(arguments)

        # get insert positions
        idxs = np.searchsorted(array, values, side="left")

        # find indexes where previous index is closer
        prev_idx_is_less = ((idxs == len(array)) | (np.fabs(
            values - array[np.maximum(idxs-1, 0)]) < np.fabs(values - array[np.minimum(idxs, len(array)-1)])))
        idxs[prev_idx_is_less] -= 1

        return list(array[idxs])


class MorseMaker():
    wpm = None
    time_unit = None
    running = False
    timing_list = []
    active = True
    text = None
    _start, _end = 0, 0
    quantized_track_list = []
    quantized_timing_list = []
    old_time = None

    def __init__(self, wpm: int = 12):
        self.wpm = wpm
        pygame.init()
        self.screen = pygame.display.set_mode((500, 400))
        self.bg_surf = pygame.Surface(self.screen.get_rect().size)
        self.bg_surf.fill((0, 0, 0))
        self.clock_object = pygame.time.Clock()
        self.pygame_thread = Thread(target=self.update_pygame,
                                    args=(self.clock_object, ))
        self.input_thread = Thread(target=self.catch_inputs)
        self.run()

    def run(self):
        self.running = True
        self.start_of_run = time.time()
        self.set_dit()
        self.old_time = time.time()

        while self.active:
            if self.running:
                self.update_track_normal()
                self.catch_inputs()
                self.do_time_stuff()
            self.update_pygame(self.clock_object, self.screen)

    def set_dit(self):
        self.dit = 60 / (50*self.wpm)

    def update_text(self, text):
        font = pygame.font.SysFont('Arial', 50)
        self.text = font.render(text, True, pygame.Color('aliceblue'))

    def catch_inputs(self):
        _time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._start = _time
                elif event.key == pygame.K_KP_ENTER:
                    self.stop_running()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self._end = _time

    def stop_running(self):
        self.running = False

    def do_time_stuff(self):
        _time = time.time()
        self.update_text("")

        if self._end < self._start:
            self._end = 0

        if self._start > 0 and self._end == 0:
            if _time - self._start >= self.dit*3:
                self._end = _time

            elif _time - self._start >= self.dit*1:
                self.update_text("dah")
            else:
                self.update_text("dit")

        if self._start > 0 and self._end > 0:
            self.timing_list.append([self._start, self._end])
            # print([round(end - start, 2) for start, end in self.timing_list])
            self._start, self._end = 0, 0
            
    def update_track_normal(self):
        if time.time() - self.old_time >= self.dit:
            self.old_time = time.time()
            self.quantized_track_list.append(self.dit*(len(self.quantized_track_list) + 1))
            
        # If a new dit or dah has been added to the list add a dictionary of the pos and dit/dah to another list (quantized)
        if len(self.quantized_timing_list) < len(self.timing_list):
            # Hook the starting position to whichever acceptable point is closest
            start_pos = get_closest_to(self.quantized_track_list, [self.timing_list[-1][0] - self.start_of_run])[-1]
            # Transform the length of your press into the preset dit and dah lengths
            length = get_closest_to([self.dit, self.dit*3], [self.timing_list[-1][1] - self.timing_list[-1][0]])[-1]
            if length == self.dit:
                length = "."
            elif length == self.dit*3:
                length = "-"
            self.quantized_timing_list.append({start_pos: length})
            self.track_to_morse_string()
    
    def track_to_morse_string(self) -> str:
        self.morse_string = ""
        old_time = 0
        end_time = 0
        for _dict in self.quantized_timing_list:
            for start_time, code in _dict.items():
                a = get_closest_to([self.dit, self.dit*3, self.dit*7], [start_time - old_time])[-1]
                if a == self.dit:
                    self.morse_string += ""
                    end_time = start_time + self.dit
                elif a == self.dit*3:
                    self.morse_string += " "
                    end_time = start_time + self.dit*3
                else:
                    self.morse_string += " / "
                    end_time = start_time + self.dit*7
                self.morse_string += code
                old_time = end_time
        
        print(mt.translate(self.morse_string))

    def update_pygame(self, clock_obj, screen):
        clock_obj.tick(60)
        screen.blit(self.bg_surf, self.bg_surf.get_rect())
        if self.text:
            screen.blit(self.text, self.screen.get_rect().center)
        pygame.display.flip()


if __name__ == "__main__":
    morse_maker = MorseMaker()
