from core.controls import BUTTON_ORDER, BUTTON_PINS
from core.platform import DigitalInput, ticks_add, ticks_diff, ticks_ms


class ButtonManager:
    REPEAT_DELAY_MS = 260
    REPEAT_INTERVAL_MS = 110

    def __init__(self):
        self._pins = {}
        self._current = {}
        self._events = {}
        self._repeat_due = {}
        self._last_press_ms = {}
        self._now_ms = ticks_ms()
        for name in BUTTON_ORDER:
            self._pins[name] = DigitalInput(BUTTON_PINS[name])
            self._current[name] = False
            self._events[name] = False
            self._repeat_due[name] = None
            self._last_press_ms[name] = -100000

    def update(self, now_ms=None):
        if now_ms is None:
            now_ms = ticks_ms()
        self._now_ms = now_ms
        for name in self._events:
            self._events[name] = False

        next_state = {}
        for name, pin in self._pins.items():
            is_down = pin.value() is False
            next_state[name] = is_down
            if is_down and not self._current[name]:
                self._events[name] = True
                self._last_press_ms[name] = now_ms
                self._repeat_due[name] = ticks_add(now_ms, self.REPEAT_DELAY_MS)
            elif not is_down:
                self._repeat_due[name] = None

        self._current = next_state

    def down(self, name):
        return self._current.get(name, False)

    def pressed(self, name):
        return self._events.get(name, False)

    def repeat(self, name, delay_ms=None, interval_ms=None):
        if self.pressed(name):
            return True
        if not self.down(name):
            return False

        if delay_ms is None:
            delay_ms = self.REPEAT_DELAY_MS
        if interval_ms is None:
            interval_ms = self.REPEAT_INTERVAL_MS

        due = self._repeat_due.get(name)
        if due is None:
            return False

        first_due = ticks_add(self._last_press_ms[name], delay_ms)
        if ticks_diff(due, first_due) > 0:
            due = first_due
            self._repeat_due[name] = due

        if ticks_diff(self._now_ms, due) >= 0:
            self._repeat_due[name] = ticks_add(self._now_ms, interval_ms)
            return True
        return False
