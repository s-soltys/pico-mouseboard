from lcd import BLACK, WHITE, GRAY, YELLOW, GREEN, CYAN
from core.controls import BUTTON_ORDER
from core.ui import draw_header, draw_footer


LEFT_COLUMN = ("UP", "DOWN", "LEFT", "RIGHT")
RIGHT_COLUMN = ("CENTER", "A", "B")
ROW_Y = (16, 28, 40, 52)


class SelfTestApp:
    def __init__(self):
        self.runtime = None
        self.last_pressed = ""

    def _report_lcd(self, *lines):
        if self.runtime is not None and hasattr(self.runtime, "report_lcd"):
            self.runtime.report_lcd(*lines)

    def on_open(self, runtime):
        self.runtime = runtime
        self.last_pressed = ""
        return True

    def on_close(self, runtime):
        return None

    def _draw_column(self, lcd, buttons, names, x):
        for index, name in enumerate(names):
            y = ROW_Y[index]
            active = buttons.down(name)
            color = GREEN if active else GRAY
            state = "on" if active else "off"
            lcd.text(name, x, y, WHITE)
            lcd.text(state, x + 32, y, color)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        for name in BUTTON_ORDER:
            if buttons.pressed(name):
                self.last_pressed = name

        detail = self.last_pressed or "live"

        lcd.fill(BLACK)
        draw_header(lcd, "Self Test", detail, CYAN)
        self._draw_column(lcd, buttons, LEFT_COLUMN, 6)
        self._draw_column(lcd, buttons, RIGHT_COLUMN, 84)
        lcd.text("Press every key", 24, 64, YELLOW)
        draw_footer(lcd, "Reset A diag B tst", GRAY)

        self._report_lcd(
            "Self test",
            "last " + detail,
            "press every key",
        )
