try:
    from machine import Pin
except ImportError:
    Pin = None

from core.controls import BUTTON_PINS


DEFAULT_BOOT_MODE = "mouse"
FORCE_USB_DIAG_BUTTON = "A"
FORCE_SELF_TEST_BUTTON = "B"


def _button_down(name):
    if Pin is None:
        return False
    try:
        pin = Pin(BUTTON_PINS[name], Pin.IN, Pin.PULL_UP)
    except Exception:
        return False
    return pin.value() == 0


def detect_boot_mode(default=DEFAULT_BOOT_MODE):
    if _button_down(FORCE_USB_DIAG_BUTTON):
        return "usb_diag"
    if _button_down(FORCE_SELF_TEST_BUTTON):
        return "self_test"
    return default
