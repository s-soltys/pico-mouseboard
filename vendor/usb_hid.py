# Vendored from micropython-lib's usb-device-hid package.

from micropython import const

import machine
import struct
import time

from usb.device.core import Descriptor, Interface, split_bmRequestType

_EP_IN_FLAG = const(1 << 7)

# Control transfer stages
_STAGE_IDLE = const(0)
_STAGE_SETUP = const(1)
_STAGE_DATA = const(2)
_STAGE_ACK = const(3)

# Request types
_REQ_TYPE_STANDARD = const(0x0)
_REQ_TYPE_CLASS = const(0x1)
_REQ_TYPE_VENDOR = const(0x2)
_REQ_TYPE_RESERVED = const(0x3)

# Descriptor types
_DESC_HID_TYPE = const(0x21)
_DESC_REPORT_TYPE = const(0x22)
_DESC_PHYSICAL_TYPE = const(0x23)

# Interface and protocol identifiers
_INTERFACE_CLASS = const(0x03)
_INTERFACE_SUBCLASS_NONE = const(0x00)
_INTERFACE_SUBCLASS_BOOT = const(0x01)

_INTERFACE_PROTOCOL_NONE = const(0x00)
_INTERFACE_PROTOCOL_KEYBOARD = const(0x01)
_INTERFACE_PROTOCOL_MOUSE = const(0x02)

# bRequest values for HID control requests
_REQ_CONTROL_GET_REPORT = const(0x01)
_REQ_CONTROL_GET_IDLE = const(0x02)
_REQ_CONTROL_GET_PROTOCOL = const(0x03)
_REQ_CONTROL_GET_DESCRIPTOR = const(0x06)
_REQ_CONTROL_SET_REPORT = const(0x09)
_REQ_CONTROL_SET_IDLE = const(0x0A)
_REQ_CONTROL_SET_PROTOCOL = const(0x0B)


class HIDInterface(Interface):
    def __init__(
        self,
        report_descriptor,
        extra_descriptors=[],
        set_report_buf=None,
        protocol=_INTERFACE_PROTOCOL_NONE,
        interface_str=None,
    ):
        super().__init__()
        self.report_descriptor = report_descriptor
        self.extra_descriptors = extra_descriptors
        self._set_report_buf = set_report_buf
        self.protocol = protocol
        self.interface_str = interface_str
        self._int_ep = None

    def get_report(self):
        return False

    def on_set_report(self, report_data, report_id, report_type):
        return True

    def busy(self):
        return self.is_open() and self.xfer_pending(self._int_ep)

    def send_report(self, report_data, timeout_ms=100):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self.busy():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False
            machine.idle()
        if not self.is_open():
            return False
        self.submit_xfer(self._int_ep, report_data)
        return True

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        desc.interface(
            itf_num,
            1,
            _INTERFACE_CLASS,
            _INTERFACE_SUBCLASS_NONE
            if self.protocol == _INTERFACE_PROTOCOL_NONE
            else _INTERFACE_SUBCLASS_BOOT,
            self.protocol,
            len(strs) if self.interface_str else 0,
        )
        if self.interface_str:
            strs.append(self.interface_str)

        self.get_hid_descriptor(desc)

        self._int_ep = ep_num | _EP_IN_FLAG
        desc.endpoint(self._int_ep, "interrupt", 8, 8)

        self.idle_rate = 0
        self.protocol = 1

    def num_eps(self):
        return 1

    def get_hid_descriptor(self, desc=None):
        length = 9 + 3 * len(self.extra_descriptors)
        if desc is None:
            desc = Descriptor(bytearray(length))

        desc.pack(
            "<BBHBBBH",
            length,
            _DESC_HID_TYPE,
            0x111,
            0,
            len(self.extra_descriptors) + 1,
            _DESC_REPORT_TYPE,
            len(self.report_descriptor),
        )

        for desc_type, desc_data in self.extra_descriptors:
            desc.pack("<BH", desc_type, len(desc_data))
        return desc.b

    def on_interface_control_xfer(self, stage, request):
        bmRequestType, bRequest, wValue, _, wLength = struct.unpack("BBHHH", request)
        _, req_type, _ = split_bmRequestType(bmRequestType)

        if stage == _STAGE_SETUP:
            if req_type == _REQ_TYPE_STANDARD:
                if bRequest == _REQ_CONTROL_GET_DESCRIPTOR:
                    desc_type = wValue >> 8
                    if desc_type == _DESC_HID_TYPE:
                        return self.get_hid_descriptor()
                    if desc_type == _DESC_REPORT_TYPE:
                        self.protocol = 1
                        return self.report_descriptor
            elif req_type == _REQ_TYPE_CLASS:
                if bRequest == _REQ_CONTROL_GET_REPORT:
                    return False
                if bRequest == _REQ_CONTROL_GET_IDLE:
                    return bytes([self.idle_rate])
                if bRequest == _REQ_CONTROL_GET_PROTOCOL:
                    return bytes([self.protocol])
                if bRequest in (_REQ_CONTROL_SET_IDLE, _REQ_CONTROL_SET_PROTOCOL):
                    return True
                if bRequest == _REQ_CONTROL_SET_REPORT:
                    return self._set_report_buf
                return False

        if stage == _STAGE_ACK and req_type == _REQ_TYPE_CLASS:
            if bRequest == _REQ_CONTROL_SET_IDLE:
                self.idle_rate = wValue >> 8
            elif bRequest == _REQ_CONTROL_SET_PROTOCOL:
                self.protocol = wValue
            elif bRequest == _REQ_CONTROL_SET_REPORT:
                report_id = wValue & 0xFF
                report_type = wValue >> 8
                report_data = self._set_report_buf
                if report_data is not None and wLength < len(report_data):
                    report_data = memoryview(self._set_report_buf)[:wLength]
                self.on_set_report(report_data, report_id, report_type)

        return True
