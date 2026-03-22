from machine import Pin
import time

from core.controls import BUTTON_ORDER, BUTTON_PINS


class ButtonManager:
    HOME_WINDOW_MS = 180
    REPEAT_DELAY_MS = 260
    REPEAT_INTERVAL_MS = 110

    def __init__(self):
        self._pins = {}
        self._current = {}
        self._events = {}
        self._repeat_due = {}
        self._last_press_ms = {}
        self._now_ms = time.ticks_ms()
        self._home_triggered = False
        self._home_latched = False
        for name in BUTTON_ORDER:
            self._pins[name] = Pin(BUTTON_PINS[name], Pin.IN, Pin.PULL_UP)
            self._current[name] = False
            self._events[name] = False
            self._repeat_due[name] = None
            self._last_press_ms[name] = -100000

    def update(self, now_ms=None):
        if now_ms is None:
            now_ms = time.ticks_ms()
        self._now_ms = now_ms
        for name in self._events:
            self._events[name] = False

        next_state = {}
        for name, pin in self._pins.items():
            is_down = pin.value() == 0
            next_state[name] = is_down
            if is_down and not self._current[name]:
                self._events[name] = True
                self._last_press_ms[name] = now_ms
                self._repeat_due[name] = time.ticks_add(now_ms, self.REPEAT_DELAY_MS)
            elif not is_down:
                self._repeat_due[name] = None

        self._home_triggered = False
        if next_state["A"] and next_state["B"]:
            delta = abs(time.ticks_diff(self._last_press_ms["A"], self._last_press_ms["B"]))
            if delta <= self.HOME_WINDOW_MS and not self._home_latched:
                self._home_triggered = True
                self._home_latched = True
        else:
            self._home_latched = False

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

        first_due = time.ticks_add(self._last_press_ms[name], delay_ms)
        if time.ticks_diff(due, first_due) > 0:
            due = first_due
            self._repeat_due[name] = due

        if time.ticks_diff(self._now_ms, due) >= 0:
            self._repeat_due[name] = time.ticks_add(self._now_ms, interval_ms)
            return True
        return False

    def home_triggered(self):
        return self._home_triggered

    def any_down(self):
        for name in self._current:
            if self._current[name]:
                return True
        return False
