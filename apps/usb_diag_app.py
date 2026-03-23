from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, GREEN, RED
from core import usb_boot
from core.hid import MouseController
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
        mouse_source,
        claim_source,
        runtime_ready,
        runtime_error,
        dev_present,
        report_ready,
    ):
        if boot_attempted:
            boot_text = "yes" if boot_ready else "no"
        else:
            boot_text = "skip"

        lines = [
            "boot ready " + boot_text,
            "usb.device " + import_usb,
            "mouse pkg " + import_mouse,
            fit_text("claim " + claim_source, 19),
            "hid ready " + _bool_text(runtime_ready),
        ]

        if not runtime_ready and runtime_error and runtime_error != "runtime ok":
            lines.append(runtime_error)
        elif report_ready != "n/a":
            lines.append("report ok " + report_ready)
        else:
            lines.append("usb dev " + _bool_text(dev_present))

        if import_mouse == "ok":
            lines[2] = fit_text("mouse src " + mouse_source, 19)

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

        controller = MouseController(allow_runtime_claim=False)
        runtime_ready = controller.ensure_ready()
        report_ready = "n/a"
        if runtime_ready:
            report_ready = _bool_text(controller.probe_report())
        runtime_error = controller.error() or "runtime ok"
        claim_source = controller.claim_source()

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
        mouse_source = usb_boot.MOUSE_SOURCE or "none"
        machine_usb = _bool_text(machine is not None and hasattr(machine, "USBDevice"))
        boot_error = usb_boot.boot_error() or ("boot ok" if usb_boot.boot_attempted() else "boot skipped")
        self.lines = self._single_screen_lines(
            boot_attempted=usb_boot.boot_attempted(),
            boot_ready=usb_boot.boot_ready(),
            import_usb=import_usb,
            import_mouse=import_mouse,
            mouse_source=mouse_source,
            claim_source=claim_source,
            runtime_ready=runtime_ready,
            runtime_error=runtime_error,
            dev_present=dev_present,
            report_ready=report_ready,
        )
        summary_ok = (
            usb_boot.boot_ready()
            and import_usb == "ok"
            and import_mouse == "ok"
            and runtime_ready
            and report_ready != "no"
        )
        self.screen_color = GREEN if summary_ok else RED
        self.footer = "CENTER rescan"

        self._log("USB diag scan")
        self._log("diag boot_ready=" + _bool_text(usb_boot.boot_ready()))
        self._log("diag boot_error=" + boot_error)
        self._log("diag usb.device=" + import_usb)
        self._log("diag mouse pkg=" + import_mouse)
        self._log("diag mouse source=" + mouse_source)
        self._log("diag claim=" + claim_source)
        self._log("diag machine.USBDevice=" + machine_usb)
        self._log("diag usb.device.get()=" + _bool_text(dev_present))
        self._log("diag dev.active=" + dev_active)
        self._log("diag hid ready=" + _bool_text(runtime_ready))
        self._log("diag report ready=" + report_ready)
        self._log("diag hid error=" + runtime_error)
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
