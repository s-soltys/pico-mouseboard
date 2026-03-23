# Vendored from micropython-lib's usb-device-mouse package.

from micropython import const

import machine
import struct

from vendor.usb_hid import HIDInterface

_INTERFACE_PROTOCOL_MOUSE = const(0x02)


class MouseInterface(HIDInterface):
    def __init__(self, interface_str="MicroPython Mouse"):
        super().__init__(
            _MOUSE_REPORT_DESC,
            protocol=_INTERFACE_PROTOCOL_MOUSE,
            interface_str=interface_str,
        )
        self._l = False
        self._m = False
        self._r = False
        self._buf = bytearray(3)

    def send_report(self, dx=0, dy=0):
        buttons = 0
        if self._l:
            buttons |= 1 << 0
        if self._r:
            buttons |= 1 << 1
        if self._m:
            buttons |= 1 << 2

        while self.busy():
            machine.idle()

        struct.pack_into("Bbb", self._buf, 0, buttons, dx, dy)
        return super().send_report(self._buf)

    def click_left(self, down=True):
        self._l = down
        return self.send_report()

    def click_middle(self, down=True):
        self._m = down
        return self.send_report()

    def click_right(self, down=True):
        self._r = down
        return self.send_report()

    def move_by(self, dx, dy):
        if not -127 <= dx <= 127:
            raise ValueError("dx")
        if not -127 <= dy <= 127:
            raise ValueError("dy")
        return self.send_report(dx, dy)


_MOUSE_REPORT_DESC = (
    b"\x05\x01"
    b"\x09\x02"
    b"\xA1\x01"
    b"\x09\x01"
    b"\xA1\x00"
    b"\x05\x09"
    b"\x19\x01"
    b"\x29\x03"
    b"\x15\x00"
    b"\x25\x01"
    b"\x95\x03"
    b"\x75\x01"
    b"\x81\x02"
    b"\x95\x01"
    b"\x75\x05"
    b"\x81\x01"
    b"\x05\x01"
    b"\x09\x30"
    b"\x09\x31"
    b"\x15\x81"
    b"\x25\x7F"
    b"\x75\x08"
    b"\x95\x02"
    b"\x81\x06"
    b"\xC0"
    b"\xC0"
)
