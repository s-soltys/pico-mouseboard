USB_IMPORT_ERROR = None
MOUSE_IMPORT_ERROR = None
KEYBOARD_IMPORT_ERROR = None
MOUSE_SOURCE = ""
KEYBOARD_SOURCE = ""

try:
    import usb.device
except ImportError:
    usb = None
    USB_IMPORT_ERROR = "usb.device missing"
else:
    try:
        from usb.device.mouse import MouseInterface
        MOUSE_SOURCE = "usb.device.mouse"
    except ImportError:
        try:
            from vendor.usb_mouse import MouseInterface
            MOUSE_SOURCE = "vendor.usb_mouse"
        except ImportError:
            MouseInterface = None
            MOUSE_IMPORT_ERROR = "usb mouse pkg missing"
    try:
        from usb.device.keyboard import KeyboardInterface
        KEYBOARD_SOURCE = "usb.device.keyboard"
    except ImportError:
        try:
            from vendor.usb_keyboard import KeyboardInterface
            KEYBOARD_SOURCE = "vendor.usb_keyboard"
        except ImportError:
            KeyboardInterface = None
            KEYBOARD_IMPORT_ERROR = "usb keyboard pkg missing"

if usb is None:
    MouseInterface = None
    KeyboardInterface = None

_boot_mouse = None
_boot_keyboard = None
_boot_attempted = False
_boot_ready = False
_boot_error = ""
_claim_source = ""


def format_exception(prefix, exc):
    name = exc.__class__.__name__
    message = str(exc)
    if message and message != name:
        return prefix + name + ": " + message
    return prefix + name


def device():
    if usb is None:
        return None
    try:
        return usb.device.get()
    except Exception:
        return None


def mouse():
    global _boot_mouse
    if MouseInterface is None:
        return None
    if _boot_mouse is None:
        _boot_mouse = MouseInterface()
    return _boot_mouse


def keyboard():
    global _boot_keyboard
    if KeyboardInterface is None:
        return None
    if _boot_keyboard is None:
        _boot_keyboard = KeyboardInterface()
    return _boot_keyboard


def boot_ready():
    return _boot_ready


def boot_attempted():
    return _boot_attempted


def boot_error():
    return _boot_error


def claim_source():
    if _claim_source:
        return _claim_source
    if _boot_attempted:
        return "boot failed"
    return "not claimed"


def configure_hid(source="boot"):
    global _boot_attempted, _boot_ready, _boot_error, _claim_source

    _boot_attempted = True

    if usb is None:
        _boot_ready = False
        _boot_error = USB_IMPORT_ERROR or "usb.device missing"
        _claim_source = "firmware unsupported"
        return False

    dev = device()
    if dev is None:
        _boot_ready = False
        _boot_error = "usb device unavailable"
        _claim_source = source + " failed"
        return False

    mouse_iface = mouse()
    if mouse_iface is None:
        _boot_ready = False
        _boot_error = MOUSE_IMPORT_ERROR or "mouse unavailable"
        _claim_source = "firmware unsupported"
        return False

    keyboard_iface = keyboard()
    if keyboard_iface is None:
        _boot_ready = False
        _boot_error = KEYBOARD_IMPORT_ERROR or "keyboard unavailable"
        _claim_source = "firmware unsupported"
        return False

    if _boot_ready and _boot_mouse is mouse_iface and _boot_keyboard is keyboard_iface:
        if not _claim_source:
            _claim_source = source + " claimed"
        return True

    try:
        dev.init(mouse_iface, keyboard_iface, builtin_driver=True)
    except Exception as exc:
        _boot_ready = False
        _boot_error = format_exception("init failed: ", exc)
        _claim_source = source + " failed"
        return False

    _boot_ready = True
    _boot_error = ""
    _claim_source = source + " claimed"
    return True


def configure_mouse(source="boot"):
    return configure_hid(source)
