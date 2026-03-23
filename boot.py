try:
    from core.boot_mode import detect_boot_mode
    from core.usb_boot import configure_hid
except Exception:
    detect_boot_mode = None
    configure_hid = None

if configure_hid is not None:
    try:
        if detect_boot_mode is None or detect_boot_mode() == "mouse":
            configure_hid("boot")
    except Exception:
        pass
