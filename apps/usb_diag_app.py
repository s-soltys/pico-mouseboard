from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, GREEN, RED
from core import usb_boot
from core.hid import KeyboardController, MouseController
from core.ui import draw_header, draw_footer, fit_text

try:
    import machine
except ImportError:
    machine = None

try:
    import os
except ImportError:
    os = None

try:
    import sys
except ImportError:
    sys = None


def _bool_text(value):
    return "yes" if value else "no"


def _bool_flag(value):
    return "y" if value else "n"


class UsbDiagApp:
    def __init__(self):
        self.runtime = None
        self.lines = ()
        self.screen_color = RED
        self.footer = "CENTER rescan"

    def _log(self, message):
        if self.runtime is not None and hasattr(self.runtime, "log"):
            self.runtime.log(message)

    def _report_lcd(self, *lines):
        if self.runtime is not None and hasattr(self.runtime, "report_lcd"):
            self.runtime.report_lcd(*lines)

    def _single_screen_lines(
        self,
        *,
        boot_attempted,
        boot_ready,
        import_usb,
        import_mouse,
        import_keyboard,
        mouse_source,
        keyboard_source,
        claim_source,
        runtime_mouse_ready,
        runtime_keyboard_ready,
        runtime_mouse_error,
        runtime_keyboard_error,
    ):
        if boot_attempted:
            boot_text = "yes" if boot_ready else "no"
        else:
            boot_text = "skip"

        lines = [
            "boot ready " + boot_text,
            "usb.device " + import_usb,
            fit_text(
                "mouse src " + mouse_source if import_mouse == "ok" else "mouse pkg " + import_mouse,
                19,
            ),
            fit_text(
                "kbd src " + keyboard_source if import_keyboard == "ok" else "kbd pkg " + import_keyboard,
                19,
            ),
            fit_text("claim " + claim_source, 19),
        ]

        if not runtime_mouse_ready and runtime_mouse_error and runtime_mouse_error != "runtime ok":
            lines.append(fit_text("mouse " + runtime_mouse_error, 19))
        elif not runtime_keyboard_ready and runtime_keyboard_error and runtime_keyboard_error != "runtime ok":
            lines.append(fit_text("kbd " + runtime_keyboard_error, 19))
        else:
            lines.append("hid M/K " + _bool_flag(runtime_mouse_ready) + _bool_flag(runtime_keyboard_ready))

        return tuple(fit_text(line, 19) for line in lines[:6])

    def _probe(self):
        dev = usb_boot.device()
        dev_present = dev is not None
        dev_active = "n/a"
        if dev_present and hasattr(dev, "active"):
            try:
                dev_active = _bool_text(bool(dev.active()))
            except Exception as exc:
                dev_active = exc.__class__.__name__

        mouse_controller = MouseController(allow_runtime_claim=False)
        keyboard_controller = KeyboardController(allow_runtime_claim=False)
        runtime_mouse_ready = mouse_controller.ensure_ready()
        runtime_keyboard_ready = keyboard_controller.ensure_ready()
        mouse_report_ready = "n/a"
        keyboard_report_ready = "n/a"
        if runtime_mouse_ready:
            mouse_report_ready = _bool_text(mouse_controller.probe_report())
        if runtime_keyboard_ready:
            keyboard_report_ready = _bool_text(keyboard_controller.probe_report())
        runtime_mouse_error = mouse_controller.error() or "runtime ok"
        runtime_keyboard_error = keyboard_controller.error() or "runtime ok"
        claim_source = mouse_controller.claim_source()

        platform_name = getattr(sys, "platform", "?") if sys is not None else "?"
        release = ""
        machine_name = ""
        if os is not None and hasattr(os, "uname"):
            try:
                uname = os.uname()
                release = getattr(uname, "release", "") or ""
                machine_name = getattr(uname, "machine", "") or ""
            except Exception:
                pass

        import_usb = "ok" if usb_boot.usb is not None else (usb_boot.USB_IMPORT_ERROR or "missing")
        import_mouse = (
            "ok" if usb_boot.MouseInterface is not None else (usb_boot.MOUSE_IMPORT_ERROR or "missing")
        )
        import_keyboard = (
            "ok"
            if usb_boot.KeyboardInterface is not None
            else (usb_boot.KEYBOARD_IMPORT_ERROR or "missing")
        )
        mouse_source = usb_boot.MOUSE_SOURCE or "none"
        keyboard_source = usb_boot.KEYBOARD_SOURCE or "none"
        machine_usb = _bool_text(machine is not None and hasattr(machine, "USBDevice"))
        boot_error = usb_boot.boot_error() or ("boot ok" if usb_boot.boot_attempted() else "boot skipped")
        self.lines = self._single_screen_lines(
            boot_attempted=usb_boot.boot_attempted(),
            boot_ready=usb_boot.boot_ready(),
            import_usb=import_usb,
            import_mouse=import_mouse,
            import_keyboard=import_keyboard,
            mouse_source=mouse_source,
            keyboard_source=keyboard_source,
            claim_source=claim_source,
            runtime_mouse_ready=runtime_mouse_ready,
            runtime_keyboard_ready=runtime_keyboard_ready,
            runtime_mouse_error=runtime_mouse_error,
            runtime_keyboard_error=runtime_keyboard_error,
        )
        summary_ok = (
            usb_boot.boot_ready()
            and import_usb == "ok"
            and import_mouse == "ok"
            and import_keyboard == "ok"
            and runtime_mouse_ready
            and runtime_keyboard_ready
            and mouse_report_ready != "no"
            and keyboard_report_ready != "no"
        )
        self.screen_color = GREEN if summary_ok else RED
        self.footer = "CENTER rescan"

        self._log("USB diag scan")
        self._log("diag boot_ready=" + _bool_text(usb_boot.boot_ready()))
        self._log("diag boot_error=" + boot_error)
        self._log("diag usb.device=" + import_usb)
        self._log("diag mouse pkg=" + import_mouse)
        self._log("diag kbd pkg=" + import_keyboard)
        self._log("diag mouse source=" + mouse_source)
        self._log("diag kbd source=" + keyboard_source)
        self._log("diag claim=" + claim_source)
        self._log("diag machine.USBDevice=" + machine_usb)
        self._log("diag usb.device.get()=" + _bool_text(dev_present))
        self._log("diag dev.active=" + dev_active)
        self._log("diag mouse ready=" + _bool_text(runtime_mouse_ready))
        self._log("diag kbd ready=" + _bool_text(runtime_keyboard_ready))
        self._log("diag mouse report=" + mouse_report_ready)
        self._log("diag kbd report=" + keyboard_report_ready)
        self._log("diag mouse error=" + runtime_mouse_error)
        self._log("diag kbd error=" + runtime_keyboard_error)
        self._log("diag firmware=" + (release or "?") + " | " + (machine_name or platform_name))

    def on_open(self, runtime):
        self.runtime = runtime
        self._probe()
        return True

    def on_close(self, runtime):
        return None

    def _draw(self, lcd):
        draw_header(lcd, "USB Diag", "", self.screen_color)
        y = 12
        for line in self.lines:
            if line:
                color = WHITE if y == 12 else YELLOW if y == 21 else GRAY
                lcd.text(fit_text(line, 19), 4, y, color)
            y += 9
        draw_footer(lcd, self.footer, GRAY)
        self._report_lcd("USB diag", *self.lines)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd
        if buttons.pressed("CENTER"):
            self._probe()

        lcd.fill(BLACK)
        self._draw(lcd)
