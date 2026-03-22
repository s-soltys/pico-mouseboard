from lcd import BLACK, CYAN, WHITE, YELLOW, GRAY, RED, GREEN
from core.buttons import ButtonManager
from core.display import get_lcd, show_fatal_error
from core.ui import center_x, fit_text
from core.platform import sleep
from apps.hid_tools_app import HIDToolsApp


class Launcher:
    LOG_HISTORY_LIMIT = 8

    def __init__(self):
        self.lcd = None
        self.buttons = None
        self.controller = None
        self.error_stage = "boot"
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
        self.lcd.text("keyboard + mouse", center_x("keyboard + mouse"), 36, YELLOW)
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
        self.set_boot_status("buttons ready", "init controller", CYAN, 0.15)

        self.controller = HIDToolsApp()
        self.set_boot_status("controller ready", "open HID", CYAN, 0.15)

    def draw_boot(self):
        status = self._boot_status or "starting"
        detail = self._boot_detail or "please wait"
        self._draw_boot(status, detail, YELLOW)
        sleep(0.35)

    def run(self):
        self.initialize()
        self.draw_boot()
        self.log("opening HID controller")
        self.controller.on_open(self)
        ready_color = RED if self.controller.status == "hid off" else GREEN
        ready_detail = self.controller.hid_detail or self.controller.status
        self.set_boot_status("ready", ready_detail, ready_color, 0.2)
        self.log("enter frame loop")
        self.error_stage = "runtime"
        while True:
            self.buttons.update()
            self.controller.step(self)
            self.lcd.display()
            sleep(0.03)


Mouseboard = Launcher
