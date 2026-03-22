from machine import Pin
import time

from lcd import LCD_0inch96, BLACK, CYAN, WHITE, YELLOW, GRAY
from core.controls import A_LABEL, B_LABEL
from core.buttons import ButtonManager
from core.ui import draw_header, draw_footer, draw_tile, center_x, HOME_HINT
from apps import build_apps


class Launcher:
    def __init__(self):
        self.lcd = LCD_0inch96()
        self.buttons = ButtonManager()
        self.apps = build_apps()
        self.selected_index = 0
        self.active_app = None
        self.led = None
        try:
            self.led = Pin("LED", Pin.OUT)
            self.led.on()
        except Exception:
            self.led = None

    def app_count(self):
        return len(self.apps)

    def page_count(self):
        return (self.app_count() + 3) // 4

    def current_page(self):
        return self.selected_index // 4

    def open_app(self, index):
        if index < 0 or index >= len(self.apps):
            return
        self.active_app = self.apps[index]
        if hasattr(self.active_app, "on_open"):
            self.active_app.on_open(self)

    def go_home(self):
        if self.active_app and hasattr(self.active_app, "on_close"):
            self.active_app.on_close(self)
        self.active_app = None

    def move_selection(self, delta):
        new_index = self.selected_index + delta
        if 0 <= new_index < len(self.apps):
            self.selected_index = new_index

    def next_page(self):
        if self.page_count() <= 1:
            return
        page = (self.current_page() + 1) % self.page_count()
        self.selected_index = min(len(self.apps) - 1, page * 4)

    def draw_boot(self):
        self.lcd.fill(BLACK)
        self.lcd.text("PICO", center_x("PICO"), 18, CYAN)
        self.lcd.text("LAUNCHER", center_x("LAUNCHER"), 32, WHITE)
        self.lcd.text("Pico 2 W", center_x("Pico 2 W"), 48, YELLOW)
        self.lcd.text(A_LABEL + " page", 20, 56, GRAY)
        self.lcd.text(B_LABEL + " open", 84, 56, GRAY)
        self.lcd.text(HOME_HINT, 20, 66, GRAY)
        self.lcd.display()
        time.sleep(0.7)

    def draw_home(self):
        self.lcd.fill(BLACK)
        detail = str(self.current_page() + 1) + "/" + str(self.page_count())
        draw_header(self.lcd, "Launcher", detail, WHITE)

        start = self.current_page() * 4
        layout = [
            (2, 13),
            (81, 13),
            (2, 42),
            (81, 42),
        ]

        for offset, app in enumerate(self.apps[start:start + 4]):
            x, y = layout[offset]
            is_selected = (start + offset) == self.selected_index
            draw_tile(self.lcd, x, y, 77, 27, app.title, is_selected, app.accent, app.draw_icon, True)

        draw_footer(self.lcd, A_LABEL + " page", WHITE)
        self.lcd.text(B_LABEL + " open", 80, 71, WHITE)

    def step_home(self):
        if self.buttons.down("A") and self.buttons.down("B"):
            self.draw_home()
            return
        if self.buttons.repeat("LEFT"):
            self.move_selection(-1)
        if self.buttons.repeat("RIGHT"):
            self.move_selection(1)
        if self.buttons.repeat("UP"):
            self.move_selection(-2)
        if self.buttons.repeat("DOWN"):
            self.move_selection(2)
        if self.buttons.pressed("A"):
            self.next_page()
        if self.buttons.pressed("B"):
            self.open_app(self.selected_index)
        self.draw_home()

    def run(self):
        self.draw_boot()
        while True:
            self.buttons.update()
            if self.active_app is None:
                self.step_home()
            else:
                if self.buttons.home_triggered():
                    self.go_home()
                    self.draw_home()
                else:
                    action = self.active_app.step(self)
                    if action == "home":
                        self.go_home()
                        self.draw_home()
            self.lcd.display()
            time.sleep(0.03)
