from lcd import BLACK, CYAN, WHITE, YELLOW, GRAY, RED
from apps.self_test_app import SelfTestApp
from apps.mouse_app import MouseApp
from apps.usb_diag_app import UsbDiagApp
from core.buttons import ButtonManager
from core.boot_mode import DEFAULT_BOOT_MODE, detect_boot_mode
from core.display import get_lcd, show_fatal_error
from core.ui import center_x, fit_text
from core.platform import sleep, sleep_ms, ticks_add, ticks_diff, ticks_ms


# Poll inputs and send HID reports more often than the LCD can be flushed.
INPUT_POLL_MS = 5
LCD_FLUSH_MS = 40


class Mouseboard:
    LOG_HISTORY_LIMIT = 8

    def __init__(self):
        self.lcd = None
        self.buttons = None
        self.controller = None
        self.boot_mode = DEFAULT_BOOT_MODE
        self.error_stage = "boot"
        self.now_ms = ticks_ms()
        self._boot_status = ""
        self._boot_detail = ""
        self._last_lcd_report = None
        self._log_history = []

    def log(self, message):
        text = str(message)
        self._log_history.append(text)
        if len(self._log_history) > self.LOG_HISTORY_LIMIT:
            self._log_history.pop(0)
        try:
            print("[mouseboard]", text)
        except Exception:
            pass

    def report_lcd(self, *lines):
        report = tuple(line for line in lines if line)
        if report == self._last_lcd_report:
            return
        self._last_lcd_report = report
        if report:
            self.log("LCD: " + " | ".join(report))

    def _draw_boot(self, status="", detail="", color=YELLOW):
        if self.lcd is None:
            return

        status = fit_text(status, 19)
        detail = fit_text(detail, 19)

        self.lcd.fill(BLACK)
        self.lcd.text("PICO", center_x("PICO"), 8, CYAN)
        self.lcd.text("MOUSEBOARD", center_x("MOUSEBOARD"), 22, WHITE)
        self.lcd.text("usb mouse", center_x("usb mouse"), 36, YELLOW)
        if status:
            self.lcd.text(status, center_x(status), 52, color)
        if detail:
            self.lcd.text(detail, center_x(detail), 64, GRAY)
        self.report_lcd("BOOT", status, detail)
        self.lcd.display()

    def set_boot_status(self, status, detail="", color=YELLOW, delay=0):
        self._boot_status = status
        self._boot_detail = detail
        if detail:
            self.log("boot stage: " + status + " | " + detail)
        else:
            self.log("boot stage: " + status)
        self._draw_boot(status, detail, color)
        if delay:
            sleep(delay)

    def show_error(self, exc, stage="runtime"):
        message = str(exc) or exc.__class__.__name__
        self.log(stage + " error: " + exc.__class__.__name__ + ": " + message)
        detail = ""
        if stage == "boot":
            detail = self._boot_detail or self._boot_status or "startup"

        try:
            if self.lcd is None:
                self.lcd = get_lcd()
            show_fatal_error(
                exc,
                stage=stage,
                detail=detail,
                log_lines=self._log_history,
                lcd=self.lcd,
            )
            title = "boot error" if stage == "boot" else "runtime error"
            line1 = fit_text(detail or exc.__class__.__name__, 19)
            line2 = fit_text(message, 19)
            self.report_lcd(title, line1, line2)
        except Exception as screen_exc:
            self.log("error screen failed: " + repr(screen_exc))

    def initialize(self):
        self.error_stage = "boot"
        self.log("boot start")
        self.log("init lcd")
        self.lcd = get_lcd()
        self.set_boot_status("lcd ready", "init buttons", CYAN, 0.15)

        self.buttons = ButtonManager()
        self.buttons.update()
        self.boot_mode = detect_boot_mode(DEFAULT_BOOT_MODE)
        self.log("boot mode: " + self.boot_mode)

        if self.boot_mode == "self_test":
            self.set_boot_status("buttons ready", "init self test", CYAN, 0.15)
            self.controller = SelfTestApp()
            self.set_boot_status("self test", "press all inputs", CYAN, 0.15)
            return

        if self.boot_mode == "usb_diag":
            self.set_boot_status("buttons ready", "init USB diag", CYAN, 0.15)
            self.controller = UsbDiagApp()
            self.set_boot_status("diag ready", "probe USB", CYAN, 0.15)
            return

        self.set_boot_status("buttons ready", "init mouse app", CYAN, 0.15)
        self.controller = MouseApp()
        self.set_boot_status("app ready", "open USB mouse", CYAN, 0.15)

    def _open_usb_diag(self, reason=""):
        previous = self.controller
        if reason:
            self.log("open USB diag: " + reason)
        if previous is not None and hasattr(previous, "on_close"):
            try:
                previous.on_close(self)
            except Exception as exc:
                self.log("close before diag failed: " + repr(exc))
        self.controller = UsbDiagApp()
        self.controller.on_open(self)

    def run(self):
        self.initialize()
        opened = self.controller.on_open(self)
        if not opened and isinstance(self.controller, MouseApp):
            self._open_usb_diag(getattr(self.controller, "hid_detail", "") or "mouse open failed")
        sleep(0.25)
        self.error_stage = "runtime"
        self.log("enter frame loop")
        next_lcd_flush_ms = ticks_ms()
        while True:
            self.now_ms = ticks_ms()
            self.buttons.update(self.now_ms)
            self.controller.step(self)
            if isinstance(self.controller, MouseApp) and self.controller.wants_debug_mode():
                self._open_usb_diag(self.controller.debug_reason())
                next_lcd_flush_ms = self.now_ms
                continue
            if ticks_diff(self.now_ms, next_lcd_flush_ms) >= 0:
                self.lcd.display()
                next_lcd_flush_ms = ticks_add(self.now_ms, LCD_FLUSH_MS)
            sleep_ms(INPUT_POLL_MS)
