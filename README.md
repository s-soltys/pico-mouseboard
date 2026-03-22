# Pico Mouseboard

Dedicated MicroPython keyboard and mouse controller for Raspberry Pi Pico 2 W with the Waveshare Pico-LCD-0.96 display.

Hardware reference:
- https://www.waveshare.com/wiki/Pico-LCD-0.96

## What It Does

This build now does one thing only: it shows a boot/status screen first, then enters a dedicated mouse/keyboard control screen.

Startup diagnostics are shown in two places:
- the LCD shows a boot splash with the current startup stage
- the USB serial console prints startup and runtime log lines prefixed with `[boot]`, `[main]`, or `[mouseboard]`
- HID open/switch failures are reported on the LCD and logged to serial so you can debug startup without network access
- fatal startup and runtime exceptions also try to initialize the LCD directly and show the latest log context on-screen

USB startup note:
- the app initializes HID from `main.py` and no longer depends on `boot.py` for normal startup
- the app retries HID bring-up briefly during startup in case the USB device handle appears a moment later
- if the board was started from a live REPL or editor "Run" action, the USB device handle can still be unavailable until you reset or reconnect the board

Because current RP2040 MicroPython HID support does not expose a clean composite keyboard+mouse device from Python, the firmware switches the USB HID interface when you change modes:
- keyboard mode exposes a USB keyboard
- mouse mode exposes a USB mouse

Expect a short host-side reconnect when switching modes with the joystick press or the `Top (A) + Bottom (B)` chord.

## Controls

- D-pad: move the keyboard cursor or move the mouse pointer
- Boot default: keyboard mode
- `Top (A)`: send the selected key in keyboard mode, or left click in mouse mode
- `Bottom (B)`: change keyboard layer in keyboard mode, or right click in mouse mode
- Joystick press: switch between keyboard mode and mouse mode
- `Top (A) + Bottom (B)`: also switch between keyboard mode and mouse mode
- In mouse mode, the `Top (A) + Bottom (B)` chord is reserved for mode switching and does not send a simultaneous left+right click

Board note:
- This build assumes the joystick press switch is wired to `GP3`, which matches the common Pico-LCD-0.96 mapping. If your board revision differs, update `CENTER` in [core/controls.py](/Users/szymon/Documents/pico-mouseboard/core/controls.py).

## Active Files

- [main.py](/Users/szymon/Documents/pico-mouseboard/main.py): MicroPython entrypoint
- [boot.py](/Users/szymon/Documents/pico-mouseboard/boot.py): optional MicroPython boot hook; normal startup now lives in [main.py](/Users/szymon/Documents/pico-mouseboard/main.py)
- [lcd.py](/Users/szymon/Documents/pico-mouseboard/lcd.py): MicroPython LCD driver
- [core/display.py](/Users/szymon/Documents/pico-mouseboard/core/display.py): shared LCD bootstrap and fatal error screen helpers
- [core/platform.py](/Users/szymon/Documents/pico-mouseboard/core/platform.py): MicroPython GPIO, SPI, PWM, and timing helpers
- [core/hid.py](/Users/szymon/Documents/pico-mouseboard/core/hid.py): MicroPython USB keyboard/mouse mode switching helpers
- [core/buttons.py](/Users/szymon/Documents/pico-mouseboard/core/buttons.py): shared button manager
- [core/launcher.py](/Users/szymon/Documents/pico-mouseboard/core/launcher.py): startup and frame loop for the dedicated controller
- [core/ui.py](/Users/szymon/Documents/pico-mouseboard/core/ui.py): shared screen header/footer helpers
- [apps/hid_tools_app.py](/Users/szymon/Documents/pico-mouseboard/apps/hid_tools_app.py): keyboard and mouse control screen

## Deploying

1. Flash a recent MicroPython build for Pico 2 W with USB device support.
2. Install the HID helper packages once:

```sh
mpremote connect /dev/ttyACM0 mip install usb-device-keyboard
mpremote connect /dev/ttyACM0 mip install usb-device-mouse
```

3. Copy [main.py](/Users/szymon/Documents/pico-mouseboard/main.py), [lcd.py](/Users/szymon/Documents/pico-mouseboard/lcd.py), [core/](/Users/szymon/Documents/pico-mouseboard/core), and [apps/](/Users/szymon/Documents/pico-mouseboard/apps) to the board. Copy [boot.py](/Users/szymon/Documents/pico-mouseboard/boot.py) only if you want the optional boot log stub.
4. Reboot the board.

If the screen reports `USB HID unavailable` with `usb device unavailable`, close any attached REPL/editor session and do a real board reset or reconnect. Starting it from an attached REPL session can leave the board in a non-HID USB state.

If the HID packages are missing, the controller still opens but will show a `hid off` status instead of sending keyboard or mouse events.
