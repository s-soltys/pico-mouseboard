try:
    from core.boot_mode import detect_boot_mode
    from core.usb_boot import configure_mouse
except Exception:
    detect_boot_mode = None
    configure_mouse = None

if configure_mouse is not None:
    try:
        if detect_boot_mode is None or detect_boot_mode() == "mouse":
            configure_mouse("boot")
    except Exception:
        pass
