from micropython import const

import machine
import struct


_STD_DESC_DEV_TYPE = const(0x01)
_STD_DESC_CONFIG_TYPE = const(0x02)
_STD_DESC_INTERFACE_TYPE = const(0x04)
_STD_DESC_ENDPOINT_TYPE = const(0x05)
_STD_DESC_INTERFACE_LEN = const(0x09)
_STD_DESC_ENDPOINT_LEN = const(0x07)

_REQ_RECIPIENT_DEVICE = const(0x00)
_REQ_RECIPIENT_INTERFACE = const(0x01)
_REQ_RECIPIENT_ENDPOINT = const(0x02)

_INTERFACE_CLASS_VENDOR = const(0xFF)
_INTERFACE_SUBCLASS_NONE = const(0x00)
_PROTOCOL_NONE = const(0x00)

_MP_EINVAL = const(22)

_DEV_DESC_LEN = const(18)
_CFG_DESC_LEN = const(9)

_DESC_OFFS_DEV_CLASS = const(4)
_DESC_OFFS_DEV_SUBCLASS = const(5)
_DESC_OFFS_DEV_PROTOCOL = const(6)
_DESC_OFFS_MAX_PACKET = const(7)
_DESC_OFFS_VENDOR = const(8)
_DESC_OFFS_PRODUCT = const(10)
_DESC_OFFS_BCD_DEVICE = const(12)
_DESC_OFFS_I_MANUFACTURER = const(14)
_DESC_OFFS_I_PRODUCT = const(15)
_DESC_OFFS_I_SERIAL = const(16)
_DESC_OFFS_NUM_CONFIGS = const(17)

_CFG_OFFS_TOTAL_LEN = const(2)
_CFG_OFFS_NUM_INTERFACES = const(4)
_CFG_OFFS_I_CONFIGURATION = const(6)
_CFG_OFFS_ATTRIBUTES = const(7)
_CFG_OFFS_MAX_POWER = const(8)

_EP_IN_FLAG = const(0x80)

_dev = None


def get():
    global _dev
    if _dev is None:
        _dev = _Device()
    return _dev


def split_bmRequestType(bm_request_type):
    return (
        bm_request_type & 0x1F,
        (bm_request_type >> 5) & 0x03,
        (bm_request_type >> 7) & 0x01,
    )


class Descriptor:
    def __init__(self, b):
        self.b = b
        self.o = 0

    def pack(self, fmt, *args):
        self.pack_into(fmt, self.o, *args)

    def pack_into(self, fmt, offs, *args):
        end = offs + struct.calcsize(fmt)
        if self.b is not None:
            struct.pack_into(fmt, self.b, offs, *args)
        self.o = max(self.o, end)

    def extend(self, data):
        if self.b is not None:
            self.b[self.o : self.o + len(data)] = data
        self.o += len(data)

    def interface(
        self,
        bInterfaceNumber,
        bNumEndpoints,
        bInterfaceClass=_INTERFACE_CLASS_VENDOR,
        bInterfaceSubClass=_INTERFACE_SUBCLASS_NONE,
        bInterfaceProtocol=_PROTOCOL_NONE,
        iInterface=0,
    ):
        self.pack(
            "BBBBBBBBB",
            _STD_DESC_INTERFACE_LEN,
            _STD_DESC_INTERFACE_TYPE,
            bInterfaceNumber,
            0,
            bNumEndpoints,
            bInterfaceClass,
            bInterfaceSubClass,
            bInterfaceProtocol,
            iInterface,
        )

    def endpoint(self, bEndpointAddress, bmAttributes, wMaxPacketSize, bInterval=1):
        if bmAttributes == "control":
            bmAttributes = 0
        elif bmAttributes == "bulk":
            bmAttributes = 2
        elif bmAttributes == "interrupt":
            bmAttributes = 3
        self.pack(
            "<BBBBHB",
            _STD_DESC_ENDPOINT_LEN,
            _STD_DESC_ENDPOINT_TYPE,
            bEndpointAddress,
            bmAttributes,
            wMaxPacketSize,
            bInterval,
        )


class Interface:
    def __init__(self):
        self._open = False
        self._eps = set()

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        raise NotImplementedError

    def num_itfs(self):
        return 1

    def num_eps(self):
        return 0

    def on_open(self):
        self._open = True

    def on_reset(self):
        self._open = False

    def is_open(self):
        return self._open

    def on_device_control_xfer(self, stage, request):
        return False

    def on_interface_control_xfer(self, stage, request):
        return False

    def on_endpoint_control_xfer(self, stage, request):
        return False

    def xfer_pending(self, ep_addr):
        return _dev is not None and _dev._xfer_pending(ep_addr)

    def submit_xfer(self, ep_addr, data, done_cb=None):
        if not self._open:
            raise RuntimeError("Not open")
        if not _dev._submit_xfer(ep_addr, data, done_cb):
            raise RuntimeError("DCD error")

    def stall(self, ep_addr, *args):
        if not self._open or ep_addr not in self._eps:
            raise RuntimeError("Not open")
        return _dev._usbd.stall(ep_addr, *args)


class _Device:
    def __init__(self):
        self._usbd = machine.USBDevice()
        self._interfaces = []
        self._itfs = {}
        self._eps = {}
        self._ep_cbs = {}

    def active(self, *args):
        return self._usbd.active(*args)

    def init(self, *itfs, **kwargs):
        self.active(False)
        self.config(*itfs, **kwargs)
        self.active(True)

    def config(
        self,
        *itfs,
        builtin_driver=False,
        manufacturer_str=None,
        product_str=None,
        serial_str=None,
        configuration_str=None,
        id_vendor=None,
        id_product=None,
        bcd_device=None,
        device_class=0,
        device_subclass=0,
        device_protocol=0,
        max_power_ma=100,
        remote_wakeup=False,
    ):
        if self.active():
            raise OSError(_MP_EINVAL)

        if isinstance(builtin_driver, bool):
            builtin_driver = self._usbd.BUILTIN_DEFAULT if builtin_driver else self._usbd.BUILTIN_NONE

        self._usbd.builtin_driver = builtin_driver

        base_dev = bytearray(getattr(builtin_driver, "desc_dev", b""))
        base_cfg = bytearray(getattr(builtin_driver, "desc_cfg", b""))
        base_itf = getattr(builtin_driver, "itf_max", 0)
        base_ep = max(1, getattr(builtin_driver, "ep_max", 0))
        base_str = max(4, getattr(builtin_driver, "str_max", 0))

        if not base_dev:
            base_dev = bytearray(_DEV_DESC_LEN)
            struct.pack_into(
                "<BBHBBBBHHHBBBB",
                base_dev,
                0,
                _DEV_DESC_LEN,
                _STD_DESC_DEV_TYPE,
                0x0200,
                device_class,
                device_subclass,
                device_protocol,
                64,
                id_vendor or 0x1209,
                id_product or 0x0001,
                bcd_device or 0x0100,
                1 if manufacturer_str else 0,
                2 if product_str else 0,
                3 if serial_str else 0,
                1,
            )

        if not base_cfg:
            base_cfg = bytearray(_CFG_DESC_LEN)
            struct.pack_into(
                "<BBHBBBBB",
                base_cfg,
                0,
                _CFG_DESC_LEN,
                _STD_DESC_CONFIG_TYPE,
                _CFG_DESC_LEN,
                0,
                1,
                0,
                0x80,
                max(1, min(250, max_power_ma // 2)),
            )

        strs = [None] * base_str
        if getattr(builtin_driver, "itf_max", 0) == 0:
            if manufacturer_str is None:
                manufacturer_str = "MicroPython"
            if product_str is None:
                product_str = "Pico Mouseboard"
            if serial_str is None:
                serial_str = "1"
            strs[1] = manufacturer_str
            strs[2] = product_str
            strs[3] = serial_str
            base_dev[_DESC_OFFS_I_MANUFACTURER] = 1 if manufacturer_str else 0
            base_dev[_DESC_OFFS_I_PRODUCT] = 2 if product_str else 0
            base_dev[_DESC_OFFS_I_SERIAL] = 3 if serial_str else 0

        if id_vendor is not None:
            struct.pack_into("<H", base_dev, _DESC_OFFS_VENDOR, id_vendor)
        if id_product is not None:
            struct.pack_into("<H", base_dev, _DESC_OFFS_PRODUCT, id_product)
        if bcd_device is not None:
            struct.pack_into("<H", base_dev, _DESC_OFFS_BCD_DEVICE, bcd_device)

        if getattr(builtin_driver, "itf_max", 0) == 0:
            base_dev[_DESC_OFFS_DEV_CLASS] = device_class
            base_dev[_DESC_OFFS_DEV_SUBCLASS] = device_subclass
            base_dev[_DESC_OFFS_DEV_PROTOCOL] = device_protocol
            base_dev[_DESC_OFFS_MAX_PACKET] = 64
            base_dev[_DESC_OFFS_NUM_CONFIGS] = 1

        temp_strs = list(strs)
        dummy = Descriptor(None)
        itf_num = base_itf
        ep_num = base_ep
        for itf in itfs:
            itf.desc_cfg(dummy, itf_num, ep_num, temp_strs)
            itf_num += itf.num_itfs()
            ep_num += itf.num_eps()

        cfg = bytearray(len(base_cfg) + dummy.o)
        cfg[: len(base_cfg)] = base_cfg
        desc = Descriptor(cfg)
        desc.o = len(base_cfg)

        self._interfaces = list(itfs)
        self._itfs = {}
        self._eps = {}
        self._ep_cbs = {}

        itf_num = base_itf
        ep_num = base_ep
        for itf in self._interfaces:
            itf._open = False
            itf._eps = set()
            itf.desc_cfg(desc, itf_num, ep_num, strs)
            for offset in range(itf.num_itfs()):
                self._itfs[itf_num + offset] = itf
            itf_num += itf.num_itfs()
            ep_num += itf.num_eps()

        total_interfaces = getattr(builtin_driver, "itf_max", 0) + sum(itf.num_itfs() for itf in self._interfaces)
        struct.pack_into("<H", cfg, _CFG_OFFS_TOTAL_LEN, len(cfg))
        cfg[_CFG_OFFS_NUM_INTERFACES] = total_interfaces
        cfg[_CFG_OFFS_ATTRIBUTES] = 0x80 | (0x20 if remote_wakeup else 0)
        cfg[_CFG_OFFS_MAX_POWER] = max(1, min(250, max_power_ma // 2))

        if configuration_str:
            cfg[_CFG_OFFS_I_CONFIGURATION] = len(strs)
            strs.append(configuration_str)
        elif len(cfg) > _CFG_OFFS_I_CONFIGURATION:
            cfg[_CFG_OFFS_I_CONFIGURATION] = 0

        self._usbd.config(
            bytes(base_dev),
            bytes(cfg),
            desc_strs=strs,
            open_itf_cb=self._open_itf_cb,
            reset_cb=self._reset_cb,
            control_xfer_cb=self._control_xfer_cb,
            xfer_cb=self._xfer_cb,
        )

    def _open_itf_cb(self, desc):
        itf = None
        offset = 0
        while offset + 2 <= len(desc):
            length = desc[offset]
            if length <= 0 or offset + length > len(desc):
                break
            dtype = desc[offset + 1]
            if dtype == _STD_DESC_INTERFACE_TYPE:
                itf = self._itfs.get(desc[offset + 2])
                if itf is not None:
                    itf.on_open()
            elif dtype == _STD_DESC_ENDPOINT_TYPE and itf is not None:
                ep_addr = desc[offset + 2]
                self._eps[ep_addr] = itf
                itf._eps.add(ep_addr)
            offset += length

    def _reset_cb(self):
        self._eps = {}
        self._ep_cbs = {}
        for itf in self._interfaces:
            itf.on_reset()

    def _control_xfer_cb(self, stage, request):
        recipient, _, _ = split_bmRequestType(request[0])
        w_index = request[4] | (request[5] << 8)

        if recipient == _REQ_RECIPIENT_INTERFACE:
            itf = self._itfs.get(w_index & 0xFF)
            if itf is not None:
                return itf.on_interface_control_xfer(stage, request)
            return False

        if recipient == _REQ_RECIPIENT_ENDPOINT:
            itf = self._eps.get(w_index & 0xFF)
            if itf is not None:
                return itf.on_endpoint_control_xfer(stage, request)
            return False

        if recipient == _REQ_RECIPIENT_DEVICE:
            for itf in self._interfaces:
                result = itf.on_device_control_xfer(stage, request)
                if result is not False:
                    return result
        return False

    def _xfer_pending(self, ep_addr):
        return ep_addr in self._ep_cbs

    def _submit_xfer(self, ep_addr, data, done_cb=None):
        if ep_addr in self._ep_cbs:
            return False
        self._ep_cbs[ep_addr] = done_cb
        try:
            ok = self._usbd.submit_xfer(ep_addr, data)
        except Exception:
            self._ep_cbs.pop(ep_addr, None)
            raise
        if not ok:
            self._ep_cbs.pop(ep_addr, None)
        return ok

    def _xfer_cb(self, ep_addr, result, xferred_bytes):
        done_cb = self._ep_cbs.pop(ep_addr, None)
        if done_cb is not None:
            done_cb(ep_addr, result, xferred_bytes)
