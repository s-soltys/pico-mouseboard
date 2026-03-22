import math

import framebuf

from core.platform import DigitalOutput, PWMBacklight, create_spi, sleep


# colors are BGR565 byte-swapped
RED = 0x00F8
GREEN = 0xE007
BLUE = 0x1F00
WHITE = 0xFFFF
BLACK = 0x0000
DKRED = 0x0090
PINK = 0x1FFC
DKGRN = 0x4004
YELLOW = 0xE0FF
CYAN = 0xFF07
GRAY = 0x1084
ORANGE = 0x20FD
PURPLE = 0x1660
TEAL = 0x6F04
RUST = 0x80C2
CRIMSON = 0x05B0
BROWN = 0x228A
GOLD = 0x40DD
SLATE = 0x8F52
INDIGO = 0x1E30
MARINE = 0xB903
AMBER = 0x00FE
OLIVE = 0xE063
MAROON = 0x0060
COPPER = 0xA0CA
SAND = 0x4BCD


class LCD_0inch96(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 160
        self.height = 80
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.cs = DigitalOutput(9, True)
        self.rst = DigitalOutput(12, True)
        self.dc = DigitalOutput(8, True)
        self._backlight = PWMBacklight(13)
        self.spi = create_spi(10, 11, baudrate=10_000_000)
        self._byte = bytearray(1)

        self.Init()
        self.SetWindows(0, 0, self.width - 1, self.height - 1)

    def _write(self, is_data, payload):
        self.dc.set(is_data)
        self.cs.off()
        self.spi.write(payload)
        self.cs.on()

    def write_cmd(self, cmd):
        self._byte[0] = cmd & 0xFF
        self._write(False, self._byte)

    def write_data(self, value):
        self._byte[0] = value & 0xFF
        self._write(True, self._byte)

    def reset(self):
        self.rst.on()
        sleep(0.2)
        self.rst.off()
        sleep(0.2)
        self.rst.on()
        sleep(0.2)

    def backlight(self, value):
        self._backlight.set_brightness(value)

    def Init(self):
        self.reset()
        self.backlight(1000)

        self.write_cmd(0x11)
        sleep(0.12)
        self.write_cmd(0x21)
        self.write_cmd(0x21)

        self.write_cmd(0xB1)
        self.write_data(0x05)
        self.write_data(0x3A)
        self.write_data(0x3A)

        self.write_cmd(0xB2)
        self.write_data(0x05)
        self.write_data(0x3A)
        self.write_data(0x3A)

        self.write_cmd(0xB3)
        self.write_data(0x05)
        self.write_data(0x3A)
        self.write_data(0x3A)
        self.write_data(0x05)
        self.write_data(0x3A)
        self.write_data(0x3A)

        self.write_cmd(0xB4)
        self.write_data(0x03)

        self.write_cmd(0xC0)
        self.write_data(0x62)
        self.write_data(0x02)
        self.write_data(0x04)

        self.write_cmd(0xC1)
        self.write_data(0xC0)

        self.write_cmd(0xC2)
        self.write_data(0x0D)
        self.write_data(0x00)

        self.write_cmd(0xC3)
        self.write_data(0x8D)
        self.write_data(0x6A)

        self.write_cmd(0xC4)
        self.write_data(0x8D)
        self.write_data(0xEE)

        self.write_cmd(0xC5)
        self.write_data(0x0E)

        self.write_cmd(0xE0)
        for value in (0x10, 0x0E, 0x02, 0x03, 0x0E, 0x07, 0x02, 0x07,
                      0x0A, 0x12, 0x27, 0x37, 0x00, 0x0D, 0x0E, 0x10):
            self.write_data(value)

        self.write_cmd(0xE1)
        for value in (0x10, 0x0E, 0x03, 0x03, 0x0F, 0x06, 0x02, 0x08,
                      0x0A, 0x13, 0x26, 0x36, 0x00, 0x0D, 0x0E, 0x10):
            self.write_data(value)

        self.write_cmd(0x3A)
        self.write_data(0x05)

        self.write_cmd(0x36)
        self.write_data(0xA8)

        self.write_cmd(0x29)

    def SetWindows(self, x_start, y_start, x_end, y_end):
        x_start += 1
        x_end += 1
        y_start += 26
        y_end += 26

        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(x_start)
        self.write_data(0x00)
        self.write_data(x_end)

        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(y_start)
        self.write_data(0x00)
        self.write_data(y_end)

        self.write_cmd(0x2C)

    def ellipse(self, cx, cy, rx, ry, color, fill=False):
        if rx < 0 or ry < 0:
            return
        if fill:
            for dy in range(-ry, ry + 1):
                py = cy + dy
                if py < 0 or py >= self.height:
                    continue
                if ry == 0:
                    span = rx
                else:
                    ratio = 1.0 - ((dy * dy) / float(ry * ry))
                    if ratio < 0:
                        continue
                    span = int(rx * math.sqrt(ratio))
                self.hline(cx - span, py, (span * 2) + 1, color)
            return

        for dx in range(-rx, rx + 1):
            if rx == 0:
                span = ry
            else:
                ratio = 1.0 - ((dx * dx) / float(rx * rx))
                if ratio < 0:
                    continue
                span = int(ry * math.sqrt(ratio))
            self.pixel(cx + dx, cy + span, color)
            self.pixel(cx + dx, cy - span, color)

        for dy in range(-ry, ry + 1):
            if ry == 0:
                span = rx
            else:
                ratio = 1.0 - ((dy * dy) / float(ry * ry))
                if ratio < 0:
                    continue
                span = int(rx * math.sqrt(ratio))
            self.pixel(cx + span, cy + dy, color)
            self.pixel(cx - span, cy + dy, color)

    def text(self, value, x, y, color):
        super().text(str(value), x, y, color)

    def display(self):
        self.SetWindows(0, 0, self.width - 1, self.height - 1)
        self._write(True, self.buffer)
