import time

from machine import PWM, SPI, Pin


try:
    ticks_ms = time.ticks_ms
    ticks_add = time.ticks_add
    ticks_diff = time.ticks_diff
except AttributeError:
    def ticks_ms():
        return int(time.monotonic() * 1000)

    def ticks_add(value, delta):
        return value + delta

    def ticks_diff(left, right):
        return left - right


def sleep(seconds):
    time.sleep(seconds)


try:
    sleep_ms = time.sleep_ms
except AttributeError:
    def sleep_ms(milliseconds):
        time.sleep(milliseconds / 1000.0)


def resolve_pin(pin_id):
    if isinstance(pin_id, str) and pin_id.startswith("GP"):
        return int(pin_id[2:])
    return pin_id


def _pin(pin_id, mode=None, pull=None, value=None):
    kwargs = {}
    if pull is not None:
        kwargs["pull"] = pull
    if value is not None:
        kwargs["value"] = value
    if mode is None:
        return Pin(resolve_pin(pin_id), **kwargs)
    return Pin(resolve_pin(pin_id), mode, **kwargs)


def _spi_id_for(clock_pin):
    clock_pin = resolve_pin(clock_pin)
    if isinstance(clock_pin, int) and clock_pin >= 8:
        return 1
    return 0


class DigitalInput:
    def __init__(self, pin_id):
        self.io = _pin(pin_id, Pin.IN, Pin.PULL_UP)

    def value(self):
        return self.io.value()


class DigitalOutput:
    def __init__(self, pin_id, initial=False):
        self.io = _pin(pin_id, Pin.OUT, value=1 if initial else 0)

    def set(self, value):
        self.io.value(1 if value else 0)

    def on(self):
        self.set(True)

    def off(self):
        self.set(False)


class PWMBacklight:
    def __init__(self, pin_id, frequency=1000):
        self._pwm = PWM(_pin(pin_id))
        self._pwm.freq(frequency)
        self._pwm.duty_u16(0)

    def set_brightness(self, value, scale=1000):
        value = max(0, min(scale, value))
        self._pwm.duty_u16(int((value / scale) * 65535))


def create_spi(clock_pin, mosi_pin, *, baudrate=10_000_000):
    return SPI(
        _spi_id_for(clock_pin),
        baudrate=baudrate,
        polarity=0,
        phase=0,
        sck=_pin(clock_pin),
        mosi=_pin(mosi_pin),
    )
