from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, GREEN, RED, TEAL
from core.controls import A_LABEL, B_LABEL
from core.hid import KeyboardController, MouseController
from core.platform import sleep_ms, ticks_diff, ticks_ms
from core.ui import draw_footer, draw_header, fit_text


# Motion speeds are accumulated over elapsed time so cursor velocity stays stable
# even when the input loop runs faster than the LCD refresh. Each profile is
# (label, base_pixels_per_second, max_pixels_per_second).
SPEEDS = (
    ("slow", 260, 520),
    ("fast", 840, 1720),
)

OPEN_RETRY_MS = 1200
OPEN_RETRY_STEP_MS = 120
MAX_MOTION_ELAPSED_MS = 40
MAX_REPORT_DELTA = 10
ACCEL_START_MS = 120
ACCEL_RAMP_MS = 420

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

KEYBOARD_GRID_X = 10
KEYBOARD_GRID_Y = 14
KEYBOARD_COL_W = 28
KEYBOARD_ROW_H = 9

MODE_MOUSE = "mouse"
MODE_KEYBOARD = "keyboard"
KEYBOARD_SHIFT = 0x02

KEYCODE_A = 4
KEYCODE_1 = 30
KEYCODE_ENTER = 40
KEYCODE_BACKSPACE = 42
KEYCODE_SPACE = 44
KEYCODE_MINUS = 45
KEYCODE_EQUAL = 46
KEYCODE_LEFT_BRACKET = 47
KEYCODE_RIGHT_BRACKET = 48
KEYCODE_BACKSLASH = 49
KEYCODE_SEMICOLON = 51
KEYCODE_APOSTROPHE = 52
KEYCODE_COMMA = 54
KEYCODE_PERIOD = 55
KEYCODE_SLASH = 56


def _key(display, keycode, modifiers=0, name=None, special=False):
    return {
        "display": display,
        "keycode": keycode,
        "modifiers": modifiers,
        "name": name or display,
        "special": special,
    }


def _alpha_key(letter, modifiers=0):
    return _key(letter, KEYCODE_A + (ord(letter.lower()) - ord("a")), modifiers, letter)


def _special_key(display, keycode, name):
    return _key(display, keycode, 0, name, True)


LOWERCASE_PAGE = (
    tuple(_alpha_key(letter) for letter in "abcde"),
    tuple(_alpha_key(letter) for letter in "fghij"),
    tuple(_alpha_key(letter) for letter in "klmno"),
    tuple(_alpha_key(letter) for letter in "pqrst"),
    tuple(_alpha_key(letter) for letter in "uvwxy"),
    (
        _alpha_key("z"),
        _special_key("SP", KEYCODE_SPACE, "Space"),
        _special_key("ENT", KEYCODE_ENTER, "Enter"),
        _special_key("BK", KEYCODE_BACKSPACE, "Backspace"),
    ),
)

UPPERCASE_PAGE = (
    tuple(_alpha_key(letter, KEYBOARD_SHIFT) for letter in "ABCDE"),
    tuple(_alpha_key(letter, KEYBOARD_SHIFT) for letter in "FGHIJ"),
    tuple(_alpha_key(letter, KEYBOARD_SHIFT) for letter in "KLMNO"),
    tuple(_alpha_key(letter, KEYBOARD_SHIFT) for letter in "PQRST"),
    tuple(_alpha_key(letter, KEYBOARD_SHIFT) for letter in "UVWXY"),
    (
        _alpha_key("Z", KEYBOARD_SHIFT),
        _special_key("SP", KEYCODE_SPACE, "Space"),
        _special_key("ENT", KEYCODE_ENTER, "Enter"),
        _special_key("BK", KEYCODE_BACKSPACE, "Backspace"),
    ),
)

SYMBOL_PAGE = (
    (
        _key("1", KEYCODE_1 + 0),
        _key("2", KEYCODE_1 + 1),
        _key("3", KEYCODE_1 + 2),
        _key("4", KEYCODE_1 + 3),
        _key("5", KEYCODE_1 + 4),
    ),
    (
        _key("6", KEYCODE_1 + 5),
        _key("7", KEYCODE_1 + 6),
        _key("8", KEYCODE_1 + 7),
        _key("9", KEYCODE_1 + 8),
        _key("0", KEYCODE_1 + 9),
    ),
    (
        _key("-", KEYCODE_MINUS),
        _key("=", KEYCODE_EQUAL),
        _key("[", KEYCODE_LEFT_BRACKET),
        _key("]", KEYCODE_RIGHT_BRACKET),
        _key(";", KEYCODE_SEMICOLON),
    ),
    (
        _key("'", KEYCODE_APOSTROPHE),
        _key(",", KEYCODE_COMMA),
        _key(".", KEYCODE_PERIOD),
        _key("/", KEYCODE_SLASH),
        _key("\\", KEYCODE_BACKSLASH),
    ),
    (
        _key("!", KEYCODE_1 + 0, KEYBOARD_SHIFT),
        _key("?", KEYCODE_SLASH, KEYBOARD_SHIFT),
        _key("@", KEYCODE_1 + 1, KEYBOARD_SHIFT),
        _key("#", KEYCODE_1 + 2, KEYBOARD_SHIFT),
        _key("$", KEYCODE_1 + 3, KEYBOARD_SHIFT),
    ),
    (
        _key("%", KEYCODE_1 + 4, KEYBOARD_SHIFT),
        _key("+", KEYCODE_EQUAL, KEYBOARD_SHIFT),
        _special_key("SP", KEYCODE_SPACE, "Space"),
        _special_key("ENT", KEYCODE_ENTER, "Enter"),
        _special_key("BK", KEYCODE_BACKSPACE, "Backspace"),
    ),
)

KEYBOARD_PAGES = (
    ("abc", LOWERCASE_PAGE),
    ("ABC", UPPERCASE_PAGE),
    ("123", SYMBOL_PAGE),
)


class MouseApp:
    def __init__(self):
        self.mouse_hid = None
        self.keyboard_hid = None
        self.runtime = None
        self.usb_state = "boot"
        self.activity = "idle"
        self.hid_detail = ""
        self.move_dx = 0
        self.move_dy = 0
        self.mouse_buttons = 0
        self.speed_index = 0
        self.input_mode = MODE_MOUSE
        self.keyboard_page_index = 0
        self.keyboard_row = 0
        self.keyboard_col = 0
        self._last_motion_ms = None
        self._move_error_x = 0.0
        self._move_error_y = 0.0
        self._move_dir_x = 0
        self._move_dir_y = 0
        self._move_hold_x_ms = 0
        self._move_hold_y_ms = 0
        self._mode_switch_latch = False
        self._mode_switch_release = False

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

    def _speed_base(self):
        return SPEEDS[self.speed_index][1]

    def _speed_max(self):
        return SPEEDS[self.speed_index][2]

    def _keyboard_page_name(self):
        return KEYBOARD_PAGES[self.keyboard_page_index][0]

    def _keyboard_rows(self):
        return KEYBOARD_PAGES[self.keyboard_page_index][1]

    def _selected_key(self):
        self._clamp_keyboard_selection()
        return self._keyboard_rows()[self.keyboard_row][self.keyboard_col]

    def _selected_key_name(self):
        return self._selected_key()["name"]

    def _reset_motion_state(self, now_ms=None):
        self.move_dx = 0
        self.move_dy = 0
        self._last_motion_ms = now_ms
        self._move_error_x = 0.0
        self._move_error_y = 0.0
        self._move_dir_x = 0
        self._move_dir_y = 0
        self._move_hold_x_ms = 0
        self._move_hold_y_ms = 0

    def _movement_elapsed_ms(self, runtime):
        now_ms = getattr(runtime, "now_ms", ticks_ms())
        if self._last_motion_ms is None:
            self._last_motion_ms = now_ms
            return 0

        elapsed_ms = ticks_diff(now_ms, self._last_motion_ms)
        self._last_motion_ms = now_ms
        if elapsed_ms <= 0:
            return 0
        if elapsed_ms > MAX_MOTION_ELAPSED_MS:
            return MAX_MOTION_ELAPSED_MS
        return elapsed_ms

    def _axis_dir(self, buttons, negative, positive):
        direction = 0
        if buttons.down(negative):
            direction -= 1
        if buttons.down(positive):
            direction += 1
        return direction

    def _axis_speed(self, hold_ms):
        base_speed = self._speed_base()
        max_speed = self._speed_max()
        if hold_ms <= ACCEL_START_MS:
            return base_speed
        ramp_ms = hold_ms - ACCEL_START_MS
        if ramp_ms >= ACCEL_RAMP_MS:
            return max_speed
        return base_speed + ((max_speed - base_speed) * ramp_ms / ACCEL_RAMP_MS)

    def _axis_delta(self, direction, elapsed_ms, residual, last_direction, hold_ms):
        if direction == 0:
            return 0, 0.0, 0, 0

        if direction != last_direction:
            residual = 0.0
            hold_ms = 0

        hold_ms += elapsed_ms
        residual += direction * (self._axis_speed(hold_ms) * elapsed_ms / 1000.0)
        delta = int(residual)
        if delta > MAX_REPORT_DELTA:
            delta = MAX_REPORT_DELTA
        elif delta < -MAX_REPORT_DELTA:
            delta = -MAX_REPORT_DELTA
        residual -= delta
        return delta, residual, direction, hold_ms

    def _signed(self, value):
        if value >= 0:
            return "+" + str(value)
        return str(value)

    def _motion_text(self):
        return self._signed(self.move_dx) + "," + self._signed(self.move_dy)

    def _open_hid_once(self):
        mouse_ready = self.mouse_hid.ensure_ready()
        keyboard_ready = self.keyboard_hid.ensure_ready()
        if mouse_ready and keyboard_ready:
            self.usb_state = "ready"
            self.hid_detail = ""
            return True
        self.usb_state = "error"
        if not mouse_ready:
            self.hid_detail = self.mouse_hid.error() or "mouse unavailable"
        else:
            self.hid_detail = self.keyboard_hid.error() or "keyboard unavailable"
        return False

    def _open_hid(self, retry_ms=0):
        if self.mouse_hid is None:
            self.mouse_hid = MouseController()
        if self.keyboard_hid is None:
            self.keyboard_hid = KeyboardController()

        self._log("open USB HID")
        if self._open_hid_once():
            return True

        attempts = retry_ms // OPEN_RETRY_STEP_MS
        if attempts:
            self._log("retry USB HID")
        for _ in range(attempts):
            sleep_ms(OPEN_RETRY_STEP_MS)
            if self._open_hid_once():
                self._log("USB HID ready after retry")
                return True

        return False

    def _set_mode(self, mode):
        self.input_mode = mode
        self.mouse_buttons = 0
        self._reset_motion_state(getattr(self.runtime, "now_ms", ticks_ms()))
        if mode == MODE_KEYBOARD:
            self.activity = "keyboard"
            if self.mouse_hid is not None:
                try:
                    self.mouse_hid.release_buttons()
                except Exception:
                    pass
        else:
            self.activity = "mouse"
        self._log("mode: " + mode)

    def _toggle_input_mode(self):
        if self.input_mode == MODE_MOUSE:
            self._set_mode(MODE_KEYBOARD)
        else:
            self._set_mode(MODE_MOUSE)

    def _cycle_keyboard_page(self):
        self.keyboard_page_index = (self.keyboard_page_index + 1) % len(KEYBOARD_PAGES)
        self._clamp_keyboard_selection()
        self.activity = "page " + self._keyboard_page_name()
        self._log("keyboard page: " + self._keyboard_page_name())

    def _clamp_keyboard_selection(self):
        rows = self._keyboard_rows()
        if self.keyboard_row >= len(rows):
            self.keyboard_row = len(rows) - 1
        if self.keyboard_row < 0:
            self.keyboard_row = 0

        row = rows[self.keyboard_row]
        if self.keyboard_col >= len(row):
            self.keyboard_col = len(row) - 1
        if self.keyboard_col < 0:
            self.keyboard_col = 0

    def _move_keyboard_selection(self, row_delta=0, col_delta=0):
        rows = self._keyboard_rows()
        next_row = self.keyboard_row + row_delta
        if next_row < 0:
            next_row = 0
        elif next_row >= len(rows):
            next_row = len(rows) - 1

        next_col = self.keyboard_col + col_delta
        row = rows[next_row]
        if next_col < 0:
            next_col = 0
        elif next_col >= len(row):
            next_col = len(row) - 1

        if next_row != self.keyboard_row:
            next_col = min(next_col, len(rows[next_row]) - 1)

        self.keyboard_row = next_row
        self.keyboard_col = next_col

    def _handle_mode_toggle(self, buttons):
        if self._mode_switch_release:
            if not buttons.down("A") and not buttons.down("B"):
                self._mode_switch_release = False
                self._mode_switch_latch = False
            return True

        chord_down = buttons.down("A") and buttons.down("B")
        if chord_down and not self._mode_switch_latch:
            self._mode_switch_latch = True
            self._mode_switch_release = True
            self._toggle_input_mode()
            return True
        if not chord_down:
            self._mode_switch_latch = False
        return chord_down

    def on_open(self, runtime):
        self.runtime = runtime
        self.mouse_hid = MouseController()
        self.keyboard_hid = KeyboardController()
        self.usb_state = "boot"
        self.activity = "idle"
        self.hid_detail = ""
        self.mouse_buttons = 0
        self.speed_index = 0
        self.input_mode = MODE_MOUSE
        self.keyboard_page_index = 0
        self.keyboard_row = 0
        self.keyboard_col = 0
        self._mode_switch_latch = False
        self._mode_switch_release = False
        self._reset_motion_state(getattr(runtime, "now_ms", ticks_ms()))

        self._set_boot_status("open USB", "mouse+kbd", CYAN)
        if not self._open_hid(OPEN_RETRY_MS):
            self._log("USB HID open failed: " + self.hid_detail)
            self._set_boot_status("USB error", self.hid_detail or "check serial", RED)
            return False

        self._log("USB HID ready")
        self._set_boot_status("USB ready", "mouse+kbd", GREEN)
        return True

    def on_close(self, runtime):
        if self.mouse_hid is not None:
            self.mouse_hid.release_buttons()
        if self.keyboard_hid is not None:
            self.keyboard_hid.release_all()

    def _toggle_speed(self):
        self.speed_index = (self.speed_index + 1) % len(SPEEDS)
        self._reset_motion_state(getattr(self.runtime, "now_ms", ticks_ms()))
        self.activity = self._speed_name()
        self._log("speed: " + self._speed_name())

    def _update_mouse(self, buttons, elapsed_ms):
        dir_x = self._axis_dir(buttons, "LEFT", "RIGHT")
        dir_y = self._axis_dir(buttons, "UP", "DOWN")
        dx, self._move_error_x, self._move_dir_x, self._move_hold_x_ms = self._axis_delta(
            dir_x,
            elapsed_ms,
            self._move_error_x,
            self._move_dir_x,
            self._move_hold_x_ms,
        )
        dy, self._move_error_y, self._move_dir_y, self._move_hold_y_ms = self._axis_delta(
            dir_y,
            elapsed_ms,
            self._move_error_y,
            self._move_dir_y,
            self._move_hold_y_ms,
        )

        mouse_buttons = 0
        if buttons.down("A"):
            mouse_buttons |= 1
        if buttons.down("B"):
            mouse_buttons |= 2

        self.move_dx = dx
        self.move_dy = dy
        self.mouse_buttons = mouse_buttons

        if self.mouse_hid is None:
            self.usb_state = "error"
            self.hid_detail = "mouse unavailable"
            self.activity = "hid off"
            return

        if self.mouse_hid.update_mouse(dx, dy, mouse_buttons):
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
        self.hid_detail = self.mouse_hid.error()
        self.activity = "hid off"

    def _update_keyboard(self, buttons):
        if buttons.repeat("UP"):
            self._move_keyboard_selection(row_delta=-1)
        if buttons.repeat("DOWN"):
            self._move_keyboard_selection(row_delta=1)
        if buttons.repeat("LEFT"):
            self._move_keyboard_selection(col_delta=-1)
        if buttons.repeat("RIGHT"):
            self._move_keyboard_selection(col_delta=1)

        if buttons.pressed("B"):
            self._cycle_keyboard_page()

        if not buttons.pressed("A"):
            return

        entry = self._selected_key()
        if self.keyboard_hid is None:
            self.usb_state = "error"
            self.hid_detail = "keyboard unavailable"
            self.activity = "hid off"
            return

        if self.keyboard_hid.tap_key(entry["keycode"], entry["modifiers"]):
            self.usb_state = "ready"
            self.hid_detail = ""
            self.activity = "send " + entry["name"]
            self._log("key send: " + entry["name"])
            return

        self.usb_state = "error"
        self.hid_detail = self.keyboard_hid.error()
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
        lcd.text("A+B keys", 82, 58, WHITE)

        footer = "Stick speed " + self._speed_name()
        draw_footer(lcd, footer, GRAY)

        self._report_lcd(
            "USB ready",
            "mouse " + self._speed_name(),
            "move " + self._motion_text(),
        )

    def _draw_keyboard_cell(self, lcd, x, y, entry, selected):
        width = KEYBOARD_COL_W - 2
        height = KEYBOARD_ROW_H - 1
        border = YELLOW if entry["special"] else WHITE
        if selected:
            lcd.fill_rect(x, y, width, height, CYAN)
            lcd.rect(x, y, width, height, CYAN)
            text_color = BLACK
        else:
            lcd.fill_rect(x, y, width, height, BLACK)
            lcd.rect(x, y, width, height, border)
            text_color = border

        label = entry["display"]
        text_x = x + max(1, (width - (len(label) * 8)) // 2)
        lcd.text(label, text_x, y + 1, text_color)

    def _draw_keyboard(self, lcd):
        draw_header(lcd, "Keyboard", self._keyboard_page_name(), GREEN)
        for row_index, row in enumerate(self._keyboard_rows()):
            y = KEYBOARD_GRID_Y + (row_index * KEYBOARD_ROW_H)
            row_x = KEYBOARD_GRID_X + ((5 - len(row)) * (KEYBOARD_COL_W // 2))
            for col_index, entry in enumerate(row):
                x = row_x + (col_index * KEYBOARD_COL_W)
                selected = row_index == self.keyboard_row and col_index == self.keyboard_col
                self._draw_keyboard_cell(lcd, x, y, entry, selected)

        draw_footer(lcd, "A key B page", GRAY)
        self._report_lcd(
            "USB ready",
            "kbd " + self._keyboard_page_name(),
            "sel " + self._selected_key_name(),
        )

    def _draw_hid_unavailable(self, lcd):
        line1 = "USB HID error"
        line2 = fit_text(self.hid_detail, 19) if self.hid_detail else ""
        line3 = ""
        footer = "check serial log"

        if self.hid_detail == "usb device unavailable":
            line2 = "Reset after deploy"
            line3 = "close REPL tools"
            footer = "then reconnect USB"
        elif self.hid_detail == "usb.device missing":
            line2 = "copy usb folder"
            line3 = "or check firmware"
            footer = "then reboot"
        elif self.hid_detail in ("usb mouse pkg missing", "usb keyboard pkg missing"):
            line2 = "copy vendor folder"
            line3 = "plus usb folder"
            footer = "then reboot"
        elif self.hid_detail.startswith("init failed:"):
            line2 = fit_text(self.hid_detail, 19)
            line3 = "reset and retry"
            footer = "reconnect USB"

        draw_header(lcd, "USB HID", "error", RED)
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
        return self.hid_detail or "USB HID error"

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd
        suppress_actions = self._handle_mode_toggle(buttons)

        if self.input_mode == MODE_MOUSE:
            if not suppress_actions and buttons.pressed("CENTER"):
                self._toggle_speed()
            if suppress_actions:
                self.mouse_buttons = 0
                if self.mouse_hid is not None:
                    self.mouse_hid.release_buttons()
                self._reset_motion_state(getattr(runtime, "now_ms", ticks_ms()))
            else:
                self._update_mouse(buttons, self._movement_elapsed_ms(runtime))
        elif suppress_actions:
            pass
        else:
            self._update_keyboard(buttons)

        lcd.fill(BLACK)
        if self.usb_state == "error":
            self._draw_hid_unavailable(lcd)
        elif self.input_mode == MODE_KEYBOARD:
            self._draw_keyboard(lcd)
        else:
            self._draw_mouse(lcd)
