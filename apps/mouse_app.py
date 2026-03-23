from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, GREEN, RED, TEAL
from core.controls import A_LABEL, B_LABEL
from core.hid import MouseController
from core.platform import sleep_ms
from core.ui import draw_header, draw_footer, fit_text


SPEEDS = (
    ("slow", 3),
    ("fast", 7),
)

OPEN_RETRY_MS = 1200
OPEN_RETRY_STEP_MS = 120

MOVE_BOX_X = 4
MOVE_BOX_Y = 14
MOVE_BOX_W = 72
MOVE_BOX_H = 44
MOVE_CENTER_X = MOVE_BOX_X + (MOVE_BOX_W // 2)
MOVE_CENTER_Y = MOVE_BOX_Y + 22

TILE_Y = 16
TILE_W = 20
TILE_H = 16
TILE_A_X = 86
TILE_B_X = 110
TILE_C_X = 134


class MouseApp:
    def __init__(self):
        self.hid = None
        self.runtime = None
        self.usb_state = "boot"
        self.activity = "idle"
        self.hid_detail = ""
        self.move_dx = 0
        self.move_dy = 0
        self.mouse_buttons = 0
        self.speed_index = 0

    def _log(self, message):
        if self.runtime is not None and hasattr(self.runtime, "log"):
            self.runtime.log(message)

    def _report_lcd(self, *lines):
        if self.runtime is not None and hasattr(self.runtime, "report_lcd"):
            self.runtime.report_lcd(*lines)

    def _set_boot_status(self, status, detail="", color=YELLOW):
        if self.runtime is not None and hasattr(self.runtime, "set_boot_status"):
            self.runtime.set_boot_status(status, detail, color)

    def _speed_name(self):
        return SPEEDS[self.speed_index][0]

    def _speed_step(self):
        return SPEEDS[self.speed_index][1]

    def _signed(self, value):
        if value >= 0:
            return "+" + str(value)
        return str(value)

    def _motion_text(self):
        return self._signed(self.move_dx) + "," + self._signed(self.move_dy)

    def _open_hid(self, retry_ms=0):
        if self.hid is None:
            self.hid = MouseController()

        self._log("open USB mouse")
        if self.hid.ensure_ready():
            self.usb_state = "ready"
            self.hid_detail = ""
            return True

        attempts = retry_ms // OPEN_RETRY_STEP_MS
        if attempts:
            self._log("retry USB mouse")
        for _ in range(attempts):
            sleep_ms(OPEN_RETRY_STEP_MS)
            if self.hid.ensure_ready():
                self.usb_state = "ready"
                self.hid_detail = ""
                self._log("USB mouse ready after retry")
                return True

        self.usb_state = "error"
        self.hid_detail = self.hid.error() if self.hid is not None else "mouse unavailable"
        return False

    def on_open(self, runtime):
        self.runtime = runtime
        self.hid = MouseController()
        self.usb_state = "boot"
        self.activity = "idle"
        self.hid_detail = ""
        self.move_dx = 0
        self.move_dy = 0
        self.mouse_buttons = 0
        self.speed_index = 0

        self._set_boot_status("open USB", "generic mouse", CYAN)
        if not self._open_hid(OPEN_RETRY_MS):
            self._log("USB mouse open failed: " + self.hid_detail)
            self._set_boot_status("USB error", self.hid_detail or "check serial", RED)
            return False

        self._log("USB mouse ready")
        self._set_boot_status("USB ready", "generic mouse", GREEN)
        return True

    def on_close(self, runtime):
        if self.hid is not None:
            self.hid.release_buttons()

    def _toggle_speed(self):
        self.speed_index = (self.speed_index + 1) % len(SPEEDS)
        self.activity = self._speed_name()
        self._log("speed: " + self._speed_name())

    def _update_mouse(self, buttons):
        step = self._speed_step()
        dx = 0
        dy = 0

        if buttons.down("LEFT"):
            dx -= step
        if buttons.down("RIGHT"):
            dx += step
        if buttons.down("UP"):
            dy -= step
        if buttons.down("DOWN"):
            dy += step

        mouse_buttons = 0
        if buttons.down("A"):
            mouse_buttons |= 1
        if buttons.down("B"):
            mouse_buttons |= 2

        self.move_dx = dx
        self.move_dy = dy
        self.mouse_buttons = mouse_buttons

        if self.hid is None:
            self.usb_state = "error"
            self.hid_detail = "mouse unavailable"
            self.activity = "hid off"
            return

        if self.hid.update_mouse(dx, dy, mouse_buttons):
            self.usb_state = "ready"
            self.hid_detail = ""
            if dx or dy:
                self.activity = "move"
            elif mouse_buttons == 1:
                self.activity = "left"
            elif mouse_buttons == 2:
                self.activity = "right"
            elif mouse_buttons == 3:
                self.activity = "both"
            elif self.activity not in ("slow", "fast"):
                self.activity = "idle"
            return

        self.usb_state = "error"
        self.hid_detail = self.hid.error()
        self.activity = "hid off"

    def _draw_tile(self, lcd, x, label, active, color, text_color=WHITE):
        fill = color if active else BLACK
        tile_text = BLACK if active else text_color
        lcd.fill_rect(x, TILE_Y, TILE_W, TILE_H, fill)
        lcd.rect(x, TILE_Y, TILE_W, TILE_H, color)
        lcd.text(label, x + 6, TILE_Y + 4, tile_text)

    def _draw_move_box(self, lcd):
        lcd.rect(MOVE_BOX_X, MOVE_BOX_Y, MOVE_BOX_W, MOVE_BOX_H, WHITE)
        lcd.text("Move", MOVE_BOX_X + 20, MOVE_BOX_Y + 2, GRAY)
        lcd.hline(MOVE_BOX_X + 6, MOVE_CENTER_Y, MOVE_BOX_W - 12, GRAY)
        lcd.vline(MOVE_CENTER_X, MOVE_BOX_Y + 12, MOVE_BOX_H - 16, GRAY)

        dot_x = MOVE_CENTER_X + max(-18, min(18, self.move_dx * 3))
        dot_y = MOVE_CENTER_Y + max(-12, min(12, self.move_dy * 2))
        lcd.fill_rect(dot_x - 1, dot_y - 1, 3, 3, YELLOW)

        lcd.text(self._motion_text(), MOVE_BOX_X + 8, MOVE_BOX_Y + 31, CYAN)

    def _draw_mouse(self, lcd):
        draw_header(lcd, "USB Mouse", self.usb_state, GREEN)
        self._draw_move_box(lcd)

        self._draw_tile(lcd, TILE_A_X, A_LABEL, bool(self.mouse_buttons & 1), GREEN)
        self._draw_tile(lcd, TILE_B_X, B_LABEL, bool(self.mouse_buttons & 2), RED)

        speed_label = "F" if self._speed_name() == "fast" else "S"
        speed_active = self._speed_name() == "fast"
        self._draw_tile(lcd, TILE_C_X, speed_label, speed_active, TEAL, TEAL)

        lcd.text("A left", 82, 38, WHITE)
        lcd.text("B right", 82, 48, WHITE)
        lcd.text("Stick spd", 82, 58, WHITE)

        footer = "Stick speed " + self._speed_name()
        draw_footer(lcd, footer, GRAY)

        self._report_lcd(
            "USB ready",
            "speed " + self._speed_name(),
            "move " + self._motion_text(),
        )

    def _draw_hid_unavailable(self, lcd):
        line1 = "USB mouse error"
        line2 = fit_text(self.hid_detail, 19) if self.hid_detail else ""
        line3 = ""
        footer = "check serial log"

        if self.hid_detail == "usb device unavailable":
            line2 = "Reset after deploy"
            line3 = "close REPL tools"
            footer = "then reconnect USB"
        elif self.hid_detail == "usb.device missing":
            line2 = "Flash MicroPython"
            line3 = "with USB device"
            footer = "support enabled"
        elif self.hid_detail == "usb mouse pkg missing":
            line2 = "copy vendor folder"
            line3 = "then reboot"
            footer = "then reboot"
        elif self.hid_detail.startswith("init failed:"):
            line2 = fit_text(self.hid_detail, 19)
            line3 = "reset and retry"
            footer = "reconnect USB"

        draw_header(lcd, "USB Mouse", "error", RED)
        lcd.text(line1, 4, 18, WHITE)
        if line2:
            lcd.text(line2, 4, 32, YELLOW)
        if line3:
            lcd.text(line3, 4, 46, GRAY)
        draw_footer(lcd, footer, GRAY)

        self._report_lcd("USB error", line2 or self.hid_detail, line3 or footer)

    def wants_debug_mode(self):
        return self.usb_state == "error"

    def debug_reason(self):
        return self.hid_detail or "USB mouse error"

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.pressed("CENTER"):
            self._toggle_speed()

        self._update_mouse(buttons)

        lcd.fill(BLACK)
        if self.usb_state == "error":
            self._draw_hid_unavailable(lcd)
        else:
            self._draw_mouse(lcd)
