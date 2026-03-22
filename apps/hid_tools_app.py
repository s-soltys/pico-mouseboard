from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, GREEN, RED
from core.controls import A_LABEL, B_LABEL
from core.hid import (
    HIDController,
    KEY_BACKSPACE,
    KEY_ENTER,
    KEY_SPACE,
    KEY_TAB,
    char_to_keypress,
)
from core.platform import sleep_ms
from core.ui import draw_header, draw_footer, fit_text


KEYBOARD_GRID_X = 5
KEYBOARD_GRID_Y = 14
KEYBOARD_CELL_W = 15
KEYBOARD_CELL_H = 12

MOUSE_STEP = 4
OPEN_RETRY_MS = 1200
OPEN_RETRY_STEP_MS = 120

SPECIAL_KEYS = {
    "BK": ("Bksp", KEY_BACKSPACE, 0),
    "EN": ("Enter", KEY_ENTER, 0),
    "SP": ("Space", KEY_SPACE, 0),
    "TB": ("Tab", KEY_TAB, 0),
}

LAYERS = [
    (
        "abc",
        [
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", "BK"],
            ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
            ["TB", "SP", "EN", "-", "'", ";", "[", "]", "\\", "?"],
        ],
    ),
    (
        "ABC",
        [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", "BK"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
            ["TB", "SP", "EN", "_", '"', ":", "{", "}", "|", "!"],
        ],
    ),
    (
        "123",
        [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["-", "/", ":", ";", "(", ")", "$", "&", "@", '"'],
            [".", ",", "?", "!", "'", "[", "]", "{", "}", "#"],
            ["TB", "SP", "EN", "+", "=", "_", "*", "%", "\\", "|"],
        ],
    ),
    (
        "sym",
        [
            ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"],
            ["-", "_", "=", "+", "[", "]", "{", "}", "\\", "|"],
            [";", ":", "'", '"', ",", ".", "<", ">", "/", "?"],
            ["TB", "SP", "EN", "`", "~", "<", ">", "^", "_", "+"],
        ],
    ),
]


class HIDToolsApp:
    def __init__(self):
        self.mode = "keyboard"
        self.layer_index = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.hid = None
        self.runtime = None
        self.status = "ready"
        self.hid_detail = ""
        self.move_dx = 0
        self.move_dy = 0
        self.mouse_buttons = 0
        self._suppress_ab = False

    def _log(self, message):
        if self.runtime is not None and hasattr(self.runtime, "log"):
            self.runtime.log(message)

    def _report_lcd(self, *lines):
        if self.runtime is not None and hasattr(self.runtime, "report_lcd"):
            self.runtime.report_lcd(*lines)

    def _set_boot_status(self, status, detail="", color=YELLOW):
        if self.runtime is not None and hasattr(self.runtime, "set_boot_status"):
            self.runtime.set_boot_status(status, detail, color)

    def _mode_status(self, mode):
        if mode == "mouse":
            return "mouse"
        return "kbd on"

    def _open_hid(self, mode, retry_ms=0):
        if self.hid is None:
            self.hid = HIDController()

        self._log("open HID: " + mode)
        if self.hid.ensure_mode(mode):
            self.mode = mode
            self.status = self._mode_status(mode)
            self.hid_detail = ""
            return True

        attempts = retry_ms // OPEN_RETRY_STEP_MS
        if attempts:
            self._log("retry HID: " + mode)
        for _ in range(attempts):
            sleep_ms(OPEN_RETRY_STEP_MS)
            if self.hid.ensure_mode(mode):
                self.mode = mode
                self.status = self._mode_status(mode)
                self.hid_detail = ""
                self._log("HID ready after retry: " + mode)
                return True

        self.status = "hid off"
        self.hid_detail = self.hid.error() if self.hid is not None else "hid missing"
        return False

    def on_open(self, runtime):
        self.runtime = runtime
        self.mode = "keyboard"
        self.layer_index = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.move_dx = 0
        self.move_dy = 0
        self.mouse_buttons = 0
        self.status = "ready"
        self.hid_detail = ""
        self.hid = HIDController()
        self._suppress_ab = False
        self._set_boot_status("open HID", "keyboard mode", CYAN)
        if not self._open_hid("keyboard", OPEN_RETRY_MS):
            self._log("HID open failed: " + self.hid_detail)
            self._set_boot_status("HID unavailable", self.hid_detail or "check serial", RED)
        else:
            self._log("HID keyboard ready")
            self._set_boot_status("keyboard ready", "enter app", GREEN)

    def on_close(self, runtime):
        if self.hid is not None:
            self.hid.release_mouse()

    def _current_grid(self):
        return LAYERS[self.layer_index][1]

    def _selected_token(self):
        return self._current_grid()[self.cursor_y][self.cursor_x]

    def _move_cursor(self, dx, dy):
        self.cursor_x = (self.cursor_x + dx) % len(self._current_grid()[0])
        self.cursor_y = (self.cursor_y + dy) % len(self._current_grid())

    def _toggle_mode(self, source):
        current = self.mode
        if current == "mouse" and self.hid is not None:
            if not self.hid.release_mouse():
                self._log("mouse release failed: " + (self.hid.error() or "unknown"))
            self.mouse_buttons = 0
        self.move_dx = 0
        self.move_dy = 0
        target = "mouse" if self.mode == "keyboard" else "keyboard"
        self.status = "switch"
        self._log("switch mode: " + current + " -> " + target + " via " + source)
        if not self._open_hid(target):
            self._log("HID switch failed: " + target + " | " + self.hid_detail)
            return
        self._log("switched mode: " + target)

    def _update_combo_guard(self, buttons):
        if self._suppress_ab and not buttons.down("A") and not buttons.down("B"):
            self._suppress_ab = False

    def _switch_requested(self, buttons):
        if buttons.pressed("CENTER"):
            return "joystick press"
        if buttons.chord_pressed("A", "B"):
            self._suppress_ab = True
            return A_LABEL + " + " + B_LABEL
        return None

    def _send_selected_key(self):
        token = self._selected_token()
        if token in SPECIAL_KEYS:
            label, keycode, modifiers = SPECIAL_KEYS[token]
            success = self.hid.tap_key(keycode, modifiers) if self.hid is not None else False
            self.status = label.lower() if success else "hid off"
            if success:
                self.hid_detail = ""
                self._log("sent key: " + label)
            else:
                self.hid_detail = self.hid.error() if self.hid is not None else "hid missing"
                self._log("send failed: " + label + " | " + self.hid_detail)
            return

        mapped = char_to_keypress(token)
        if mapped is None:
            self.status = "unsupported"
            self._log("unsupported key: " + token)
            return

        keycode, modifiers = mapped
        success = self.hid.tap_key(keycode, modifiers) if self.hid is not None else False
        self.status = token if success else "hid off"
        if success:
            self.hid_detail = ""
            self._log("sent key: " + token)
        else:
            self.hid_detail = self.hid.error() if self.hid is not None else "hid missing"
            self._log("send failed: " + token + " | " + self.hid_detail)

    def _draw_key_cell(self, lcd, x, y, token, selected):
        border = YELLOW if selected else GRAY
        fill = WHITE if selected else BLACK
        text_color = BLACK if selected else WHITE
        lcd.fill_rect(x, y, KEYBOARD_CELL_W - 1, KEYBOARD_CELL_H - 1, fill)
        lcd.rect(x, y, KEYBOARD_CELL_W, KEYBOARD_CELL_H, border)

        if token in SPECIAL_KEYS:
            label = SPECIAL_KEYS[token][0][:2]
        else:
            label = token

        tx = x + max(1, (KEYBOARD_CELL_W - (len(label) * 8)) // 2)
        ty = y + 2
        lcd.text(label, tx, ty, text_color)

    def _draw_keyboard(self, lcd):
        if self.status == "hid off":
            self._draw_hid_unavailable(lcd, "Keyboard")
            return

        grid = self._current_grid()
        draw_header(lcd, "Keyboard", self.status[:6], CYAN)

        for row_index, row in enumerate(grid):
            for col_index, token in enumerate(row):
                cell_x = KEYBOARD_GRID_X + (col_index * KEYBOARD_CELL_W)
                cell_y = KEYBOARD_GRID_Y + (row_index * KEYBOARD_CELL_H)
                self._draw_key_cell(
                    lcd,
                    cell_x,
                    cell_y,
                    token,
                    row_index == self.cursor_y and col_index == self.cursor_x,
                )

        lcd.text(B_LABEL + ": layer", 4, 61, GRAY)
        draw_footer(lcd, A_LABEL + " send", GRAY)
        self._report_lcd("Keyboard", "status " + self.status, "layer " + LAYERS[self.layer_index][0])

    def _draw_hid_unavailable(self, lcd, title):
        line1 = "USB HID unavailable"
        line2 = fit_text(self.hid_detail, 19) if self.hid_detail else ""
        line3 = ""
        footer = ""

        if self.hid_detail == "usb device unavailable":
            line2 = "Reset after deploy"
            line3 = "close REPL tools"
            footer = "then reconnect USB"
        elif self.hid_detail == "usb.device missing":
            line2 = "Flash MicroPython"
            line3 = "with USB device"
            footer = "support enabled"
        elif self.hid_detail == "usb kb pkg missing":
            line2 = "Install package:"
            line3 = "usb-device-keyb."
            footer = "then reboot"
        elif self.hid_detail == "usb mouse pkg missing":
            line2 = "Install package:"
            line3 = "usb-device-mouse"
            footer = "then reboot"
        elif self.hid_detail.startswith("init failed:"):
            line2 = fit_text(self.hid_detail, 19)
            line3 = "reset and retry"
            footer = "reconnect USB"

        draw_header(lcd, title, "hidoff", RED)
        lcd.text(line1, 4, 18, WHITE)
        if line2:
            lcd.text(line2, 4, 32, YELLOW)
        if line3:
            lcd.text(line3, 4, 46, GRAY)
        draw_footer(lcd, footer or "check serial log", GRAY)
        self._report_lcd(title, line1, line2, line3 or footer or "check serial log")

    def _update_mouse(self, buttons):
        dx = 0
        dy = 0
        if buttons.down("LEFT"):
            dx -= MOUSE_STEP
        if buttons.down("RIGHT"):
            dx += MOUSE_STEP
        if buttons.down("UP"):
            dy -= MOUSE_STEP
        if buttons.down("DOWN"):
            dy += MOUSE_STEP

        mouse_buttons = 0
        if not self._suppress_ab and buttons.down("A"):
            mouse_buttons |= 1
        if not self._suppress_ab and buttons.down("B"):
            mouse_buttons |= 2

        self.move_dx = dx
        self.move_dy = dy
        self.mouse_buttons = mouse_buttons
        if self.hid is not None:
            if self.hid.update_mouse(dx, dy, mouse_buttons):
                if dx or dy:
                    self.status = "move"
                elif mouse_buttons == 1:
                    self.status = "left"
                elif mouse_buttons == 2:
                    self.status = "right"
                elif mouse_buttons == 3:
                    self.status = "both"
                else:
                    self.status = "idle"
                self.hid_detail = ""
            else:
                self.status = "hid off"
                self.hid_detail = self.hid.error()

    def _draw_mouse(self, lcd):
        if self.status == "hid off":
            self._draw_hid_unavailable(lcd, "Mouse")
            return

        draw_header(lcd, "Mouse", self.status[:6], CYAN)
        lcd.rect(12, 18, 50, 38, WHITE)
        lcd.vline(37, 22, 30, GRAY)
        lcd.hline(17, 37, 40, GRAY)
        lcd.ellipse(37 + (self.move_dx // 2), 37 + (self.move_dy // 2), 3, 3, YELLOW, True)

        lcd.text("dx " + str(self.move_dx), 76, 18, WHITE)
        lcd.text("dy " + str(self.move_dy), 76, 30, WHITE)
        lcd.text("L " + ("down" if self.mouse_buttons & 1 else "up"), 76, 42, GREEN)
        lcd.text("R " + ("down" if self.mouse_buttons & 2 else "up"), 76, 54, RED)

        lcd.text(B_LABEL + ": right", 4, 61, GRAY)
        draw_footer(lcd, A_LABEL + " left", GRAY)
        self._report_lcd("Mouse", "status " + self.status, "dx " + str(self.move_dx) + " dy " + str(self.move_dy))

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        self._update_combo_guard(buttons)
        switch_source = self._switch_requested(buttons)
        if switch_source:
            self._toggle_mode(switch_source)
            lcd.fill(BLACK)
            if self.mode == "keyboard":
                self._draw_keyboard(lcd)
            else:
                self._draw_mouse(lcd)
            return None

        lcd.fill(BLACK)
        if self.mode == "keyboard":
            if buttons.repeat("LEFT", 160, 110):
                self._move_cursor(-1, 0)
            if buttons.repeat("RIGHT", 160, 110):
                self._move_cursor(1, 0)
            if buttons.repeat("UP", 160, 110):
                self._move_cursor(0, -1)
            if buttons.repeat("DOWN", 160, 110):
                self._move_cursor(0, 1)
            if not self._suppress_ab and buttons.pressed("A"):
                self._send_selected_key()
            if not self._suppress_ab and buttons.pressed("B"):
                self.layer_index = (self.layer_index + 1) % len(LAYERS)
                self.status = LAYERS[self.layer_index][0]
                self._log("keyboard layer: " + self.status)
            self._draw_keyboard(lcd)
        else:
            self._update_mouse(buttons)
            self._draw_mouse(lcd)

        return None
