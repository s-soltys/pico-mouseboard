from core.platform import sleep_ms
from core import usb_boot


usb = usb_boot.usb
MouseInterface = usb_boot.MouseInterface
KeyboardInterface = usb_boot.KeyboardInterface
USB_IMPORT_ERROR = usb_boot.USB_IMPORT_ERROR
MOUSE_IMPORT_ERROR = usb_boot.MOUSE_IMPORT_ERROR
KEYBOARD_IMPORT_ERROR = usb_boot.KEYBOARD_IMPORT_ERROR

INIT_SETTLE_MS = 250


class MouseController:
    def __init__(self, allow_runtime_claim=True):
        self._device = None
        self._allow_runtime_claim = allow_runtime_claim
        self.mouse = usb_boot.mouse()
        self._ready = False
        self._mouse_buttons = 0
        self._last_error = ""
        self._claim_source = usb_boot.claim_source()
        self._refresh_state()

    def error(self):
        return self._last_error

    def ready(self):
        return self._ready

    def claim_source(self):
        return self._claim_source

    def _set_error(self, message):
        self._last_error = message

    def _refresh_state(self):
        if usb is None:
            self._device = None
            self._ready = False
            self._mouse_buttons = 0
            self._claim_source = "firmware unsupported"
            self._set_error(USB_IMPORT_ERROR or "usb.device missing")
            return

        self._device = usb_boot.device()
        if self.mouse is None:
            self.mouse = usb_boot.mouse()

        if self._device is None:
            self._ready = False
            self._mouse_buttons = 0
            self._claim_source = usb_boot.claim_source()
            self._set_error("usb device unavailable")
        elif self.mouse is None:
            self._ready = False
            self._mouse_buttons = 0
            self._claim_source = "firmware unsupported"
            self._set_error(MOUSE_IMPORT_ERROR or "mouse unavailable")
        elif not self._last_error.startswith("mouse failed:"):
            self._claim_source = usb_boot.claim_source()
            self._set_error("")

    def ensure_ready(self):
        self._refresh_state()
        if self._ready:
            self._set_error("")
            return True
        if self._device is None:
            self._set_error(usb_boot.boot_error() or "usb device unavailable")
            return False
        if self.mouse is None:
            self._set_error(MOUSE_IMPORT_ERROR or "mouse unavailable")
            return False

        if usb_boot.boot_ready() and self.mouse is usb_boot.mouse():
            self._ready = True
            self._claim_source = usb_boot.claim_source()
            self._set_error("")
            return True

        if usb_boot.boot_attempted() or not self._allow_runtime_claim:
            self._ready = False
            self._mouse_buttons = 0
            self._claim_source = usb_boot.claim_source()
            self._set_error(usb_boot.boot_error() or "boot skipped")
            return False

        if not usb_boot.configure_hid("runtime"):
            self._refresh_state()
            self._ready = False
            self._mouse_buttons = 0
            self._claim_source = usb_boot.claim_source()
            self._set_error(usb_boot.boot_error() or "usb device unavailable")
            return False

        self._device = usb_boot.device()
        self._claim_source = usb_boot.claim_source()
        sleep_ms(INIT_SETTLE_MS)
        self._ready = True
        self._set_error("")
        return True

    def probe_report(self):
        if not self.ensure_ready():
            return False
        try:
            result = None
            if hasattr(self.mouse, "move_by"):
                result = self.mouse.move_by(0, 0)
            elif hasattr(self.mouse, "send_report"):
                result = self.mouse.send_report()
            if result is False:
                self._ready = False
                self._set_error("report send failed")
                return False
            self._set_error("")
            return True
        except Exception as exc:
            self._ready = False
            self._set_error(usb_boot.format_exception("report failed: ", exc))
            return False

    def update_mouse(self, dx, dy, buttons):
        if not self.ensure_ready():
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
            self._ready = False
            self._mouse_buttons = 0
            self._set_error(usb_boot.format_exception("mouse failed: ", exc))
            return False

    def release_buttons(self):
        if self._mouse_buttons == 0:
            return True
        return self.update_mouse(0, 0, 0)


class KeyboardController:
    def __init__(self, allow_runtime_claim=True):
        self._device = None
        self._allow_runtime_claim = allow_runtime_claim
        self.keyboard = usb_boot.keyboard()
        self._ready = False
        self._last_error = ""
        self._claim_source = usb_boot.claim_source()
        self._refresh_state()

    def error(self):
        return self._last_error

    def ready(self):
        return self._ready

    def claim_source(self):
        return self._claim_source

    def _set_error(self, message):
        self._last_error = message

    def _refresh_state(self):
        if usb is None:
            self._device = None
            self._ready = False
            self._claim_source = "firmware unsupported"
            self._set_error(USB_IMPORT_ERROR or "usb.device missing")
            return

        self._device = usb_boot.device()
        if self.keyboard is None:
            self.keyboard = usb_boot.keyboard()

        if self._device is None:
            self._ready = False
            self._claim_source = usb_boot.claim_source()
            self._set_error("usb device unavailable")
        elif self.keyboard is None:
            self._ready = False
            self._claim_source = "firmware unsupported"
            self._set_error(KEYBOARD_IMPORT_ERROR or "keyboard unavailable")
        elif not self._last_error.startswith("keyboard failed:"):
            self._claim_source = usb_boot.claim_source()
            self._set_error("")

    def ensure_ready(self):
        self._refresh_state()
        if self._ready:
            self._set_error("")
            return True
        if self._device is None:
            self._set_error(usb_boot.boot_error() or "usb device unavailable")
            return False
        if self.keyboard is None:
            self._set_error(KEYBOARD_IMPORT_ERROR or "keyboard unavailable")
            return False

        if usb_boot.boot_ready() and self.keyboard is usb_boot.keyboard():
            self._ready = True
            self._claim_source = usb_boot.claim_source()
            self._set_error("")
            return True

        if usb_boot.boot_attempted() or not self._allow_runtime_claim:
            self._ready = False
            self._claim_source = usb_boot.claim_source()
            self._set_error(usb_boot.boot_error() or "boot skipped")
            return False

        if not usb_boot.configure_hid("runtime"):
            self._refresh_state()
            self._ready = False
            self._claim_source = usb_boot.claim_source()
            self._set_error(usb_boot.boot_error() or "usb device unavailable")
            return False

        self._device = usb_boot.device()
        self._claim_source = usb_boot.claim_source()
        sleep_ms(INIT_SETTLE_MS)
        self._ready = True
        self._set_error("")
        return True

    def probe_report(self):
        if not self.ensure_ready():
            return False
        try:
            result = self.keyboard.release_all()
            if result is False:
                self._ready = False
                self._set_error("report send failed")
                return False
            self._set_error("")
            return True
        except Exception as exc:
            self._ready = False
            self._set_error(usb_boot.format_exception("report failed: ", exc))
            return False

    def tap_key(self, keycode, modifiers=0):
        if not self.ensure_ready():
            return False
        try:
            result = self.keyboard.tap_key(keycode, modifiers)
            if result is False:
                self._ready = False
                self._set_error("report send failed")
                return False
            self._set_error("")
            return True
        except Exception as exc:
            self._ready = False
            self._set_error(usb_boot.format_exception("keyboard failed: ", exc))
            return False

    def release_all(self):
        if not self.ensure_ready():
            return False
        try:
            result = self.keyboard.release_all()
            if result is False:
                self._ready = False
                self._set_error("report send failed")
                return False
            self._set_error("")
            return True
        except Exception as exc:
            self._ready = False
            self._set_error(usb_boot.format_exception("keyboard failed: ", exc))
            return False
