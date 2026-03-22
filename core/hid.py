from core.platform import sleep_ms


USB_IMPORT_ERROR = None
KEYBOARD_IMPORT_ERROR = None
MOUSE_IMPORT_ERROR = None

try:
    import usb.device
except ImportError:
    usb = None
    USB_IMPORT_ERROR = "usb.device missing"
else:
    try:
        from usb.device.keyboard import KeyboardInterface
    except ImportError:
        KeyboardInterface = None
        KEYBOARD_IMPORT_ERROR = "usb kb pkg missing"
    try:
        from usb.device.mouse import MouseInterface
    except ImportError:
        MouseInterface = None
        MOUSE_IMPORT_ERROR = "usb mouse pkg missing"

if usb is None:
    KeyboardInterface = None
    MouseInterface = None

MOD_LEFT_SHIFT = 0x02

KEY_A = 0x04
KEY_1 = 0x1E
KEY_0 = 0x27
KEY_ENTER = 0x28
KEY_BACKSPACE = 0x2A
KEY_TAB = 0x2B
KEY_SPACE = 0x2C
KEY_MINUS = 0x2D
KEY_EQUALS = 0x2E
KEY_LEFT_BRACKET = 0x2F
KEY_RIGHT_BRACKET = 0x30
KEY_BACKSLASH = 0x31
KEY_SEMICOLON = 0x33
KEY_QUOTE = 0x34
KEY_GRAVE = 0x35
KEY_COMMA = 0x36
KEY_PERIOD = 0x37
KEY_SLASH = 0x38

MODE_KEYBOARD = "keyboard"
MODE_MOUSE = "mouse"
SWITCH_SETTLE_MS = 250


class HIDController:
    def __init__(self):
        self._device = None
        self.keyboard = KeyboardInterface() if KeyboardInterface is not None else None
        self.mouse = MouseInterface() if MouseInterface is not None else None
        self._mode = None
        self._mouse_buttons = 0
        self._last_error = ""
        self._refresh_state()

    def error(self):
        return self._last_error

    def _set_error(self, message):
        self._last_error = message

    def _refresh_state(self):
        if usb is None:
            self._device = None
            self._set_error(USB_IMPORT_ERROR or "usb.device missing")
            return

        try:
            self._device = usb.device.get()
        except Exception:
            self._device = None

        if self._device is None:
            self._mode = None
            self._mouse_buttons = 0
            self._set_error("usb device unavailable")
        elif self.keyboard is None:
            self._set_error(KEYBOARD_IMPORT_ERROR or "keyboard unavailable")
        elif self.mouse is None:
            self._set_error(MOUSE_IMPORT_ERROR or "mouse unavailable")
        else:
            self._set_error("")

    def available(self):
        self._refresh_state()
        return self.keyboard_ready() and self.mouse_ready()

    def keyboard_ready(self):
        self._refresh_state()
        return self._device is not None and self.keyboard is not None

    def mouse_ready(self):
        self._refresh_state()
        return self._device is not None and self.mouse is not None

    def mode(self):
        return self._mode

    def ensure_mode(self, mode):
        self._refresh_state()
        if mode == MODE_KEYBOARD:
            interface = self.keyboard
        elif mode == MODE_MOUSE:
            interface = self.mouse
        else:
            self._set_error("invalid HID mode")
            return False

        if self._device is None:
            self._set_error("usb device unavailable")
            return False
        if interface is None:
            if mode == MODE_KEYBOARD:
                self._set_error(KEYBOARD_IMPORT_ERROR or "keyboard unavailable")
            else:
                self._set_error(MOUSE_IMPORT_ERROR or "mouse unavailable")
            return False
        if self._mode == mode:
            self._set_error("")
            return True

        try:
            self._device.init(interface, builtin_driver=True)
            sleep_ms(SWITCH_SETTLE_MS)
        except Exception as exc:
            self._mode = None
            self._mouse_buttons = 0
            self._set_error("init failed: " + exc.__class__.__name__)
            return False

        self._mode = mode
        if mode != MODE_MOUSE:
            self._mouse_buttons = 0
        self._set_error("")
        return True

    def tap_key(self, keycode, modifiers=0):
        if not self.ensure_mode(MODE_KEYBOARD):
            return False

        keys = [keycode]
        if modifiers:
            keys.insert(0, -modifiers)

        try:
            self.keyboard.send_keys(keys)
            self.keyboard.send_keys([])
            self._set_error("")
            return True
        except Exception as exc:
            self._mode = None
            self._set_error("send failed: " + exc.__class__.__name__)
            return False

    def update_mouse(self, dx, dy, buttons):
        if not self.ensure_mode(MODE_MOUSE):
            return False
        if dx == 0 and dy == 0 and buttons == self._mouse_buttons:
            self._set_error("")
            return True

        try:
            if buttons != self._mouse_buttons:
                self.mouse.click_left(bool(buttons & 1))
                self.mouse.click_right(bool(buttons & 2))
                self._mouse_buttons = buttons
            if dx or dy:
                self.mouse.move_by(dx, dy)
            self._set_error("")
            return True
        except Exception as exc:
            self._mode = None
            self._mouse_buttons = 0
            self._set_error("mouse failed: " + exc.__class__.__name__)
            return False

    def release_mouse(self):
        if not self.mouse_ready():
            self._set_error(MOUSE_IMPORT_ERROR or "mouse unavailable")
            return False
        if self._mode != MODE_MOUSE:
            self._mouse_buttons = 0
            self._set_error("")
            return True
        return self.update_mouse(0, 0, 0)


def configure_default_usb_mode(mode=MODE_KEYBOARD):
    return HIDController().ensure_mode(mode)


def char_to_keypress(char):
    if len(char) != 1:
        return None

    code = ord(char)
    if 97 <= code <= 122:
        return KEY_A + (code - 97), 0
    if 65 <= code <= 90:
        return KEY_A + (code - 65), MOD_LEFT_SHIFT
    if 49 <= code <= 57:
        return KEY_1 + (code - 49), 0
    if code == 48:
        return KEY_0, 0

    mapping = {
        " ": (KEY_SPACE, 0),
        "-": (KEY_MINUS, 0),
        "_": (KEY_MINUS, MOD_LEFT_SHIFT),
        "=": (KEY_EQUALS, 0),
        "+": (KEY_EQUALS, MOD_LEFT_SHIFT),
        "[": (KEY_LEFT_BRACKET, 0),
        "{": (KEY_LEFT_BRACKET, MOD_LEFT_SHIFT),
        "]": (KEY_RIGHT_BRACKET, 0),
        "}": (KEY_RIGHT_BRACKET, MOD_LEFT_SHIFT),
        "\\": (KEY_BACKSLASH, 0),
        "|": (KEY_BACKSLASH, MOD_LEFT_SHIFT),
        ";": (KEY_SEMICOLON, 0),
        ":": (KEY_SEMICOLON, MOD_LEFT_SHIFT),
        "'": (KEY_QUOTE, 0),
        '"': (KEY_QUOTE, MOD_LEFT_SHIFT),
        "`": (KEY_GRAVE, 0),
        "~": (KEY_GRAVE, MOD_LEFT_SHIFT),
        ",": (KEY_COMMA, 0),
        "<": (KEY_COMMA, MOD_LEFT_SHIFT),
        ".": (KEY_PERIOD, 0),
        ">": (KEY_PERIOD, MOD_LEFT_SHIFT),
        "/": (KEY_SLASH, 0),
        "?": (KEY_SLASH, MOD_LEFT_SHIFT),
        "!": (KEY_1, MOD_LEFT_SHIFT),
        "@": (KEY_1 + 1, MOD_LEFT_SHIFT),
        "#": (KEY_1 + 2, MOD_LEFT_SHIFT),
        "$": (KEY_1 + 3, MOD_LEFT_SHIFT),
        "%": (KEY_1 + 4, MOD_LEFT_SHIFT),
        "^": (KEY_1 + 5, MOD_LEFT_SHIFT),
        "&": (KEY_1 + 6, MOD_LEFT_SHIFT),
        "*": (KEY_1 + 7, MOD_LEFT_SHIFT),
        "(": (KEY_1 + 8, MOD_LEFT_SHIFT),
        ")": (KEY_0, MOD_LEFT_SHIFT),
    }
    return mapping.get(char)
