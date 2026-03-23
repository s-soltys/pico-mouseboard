# Vendored from micropython-lib's usb-device-keyboard package.

from micropython import const

import struct

from vendor.usb_hid import HIDInterface

_INTERFACE_PROTOCOL_KEYBOARD = const(0x01)


class KeyboardInterface(HIDInterface):
    MOD_LEFT_CTRL = const(0x01)
    MOD_LEFT_SHIFT = const(0x02)
    MOD_LEFT_ALT = const(0x04)
    MOD_LEFT_GUI = const(0x08)
    MOD_RIGHT_CTRL = const(0x10)
    MOD_RIGHT_SHIFT = const(0x20)
    MOD_RIGHT_ALT = const(0x40)
    MOD_RIGHT_GUI = const(0x80)

    def __init__(self, interface_str="MicroPython Keyboard"):
        super().__init__(
            _KEYBOARD_REPORT_DESC,
            protocol=_INTERFACE_PROTOCOL_KEYBOARD,
            interface_str=interface_str,
        )
        self._buf = bytearray(8)

    def send_report(self, modifiers=0, keycodes=()):
        if len(keycodes) > 6:
            raise ValueError("keycodes")

        struct.pack_into("BB", self._buf, 0, modifiers & 0xFF, 0)
        for index in range(6):
            self._buf[2 + index] = keycodes[index] if index < len(keycodes) else 0
        return super().send_report(self._buf)

    def release_all(self):
        return self.send_report()

    def tap_key(self, keycode, modifiers=0):
        if not self.send_report(modifiers, (keycode,)):
            return False
        return self.release_all()


_KEYBOARD_REPORT_DESC = (
    b"\x05\x01"
    b"\x09\x06"
    b"\xA1\x01"
    b"\x05\x07"
    b"\x19\xE0"
    b"\x29\xE7"
    b"\x15\x00"
    b"\x25\x01"
    b"\x75\x01"
    b"\x95\x08"
    b"\x81\x02"
    b"\x95\x01"
    b"\x75\x08"
    b"\x81\x01"
    b"\x95\x06"
    b"\x75\x08"
    b"\x15\x00"
    b"\x25\x65"
    b"\x05\x07"
    b"\x19\x00"
    b"\x29\x65"
    b"\x81\x00"
    b"\xC0"
)
