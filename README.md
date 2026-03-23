# Pico Mouseboard

MicroPython USB mouse and keyboard controller for Raspberry Pi Pico 2 with the Waveshare Pico-LCD-0.96 display.

Hardware reference:
- https://www.waveshare.com/wiki/Pico-LCD-0.96

## Current Status

The board now boots as a composite USB mouse + keyboard device with:
- joystick directions mapped to cursor movement
- `A` mapped to left click
- `B` mapped to right click
- joystick press toggling two speed modes
- `A+B` toggling between mouse mode and keyboard mode
- keyboard mode using the joystick to move selection, `A` to send the selected key, and `B` to cycle pages

Keyboard pages:
- `abc`: lowercase letters plus `Space`, `Enter`, and `Backspace`
- `ABC`: uppercase letters plus `Space`, `Enter`, and `Backspace`
- `123`: numbers and symbols plus `Space`, `Enter`, and `Backspace`

Current speed steps:
- `slow`
- `fast`

## Boot Modes

There are three boot modes:
- normal reset: `mouse`
- hold `A` during reset or power-up: `usb_diag`
- hold `B` during reset or power-up: `self_test`

Mode summary:
- `mouse`: normal composite HID runtime with mouse and keyboard screens
- `usb_diag`: single-screen USB/HID diagnostics, `CENTER` rescans
- `self_test`: raw input test for all buttons and joystick directions

## Deploying

1. Flash a recent official Pico 2 MicroPython UF2 with `machine.USBDevice` support.
2. Copy these files and folders to the board:
   `boot.py`, `main.py`, `screentest.py`, `lcd.py`, `core/`, `apps/`, `usb/`, `vendor/`
3. Hard reset or unplug/replug the board.
4. Close any attached REPL/editor before testing mouse mode.

The `usb/` and `vendor/` folders are required. The project vendors the runtime USB support it needs, so no separate `mip install` step is expected.

## Bring-Up Checklist

Use this order after flashing or after USB/input changes:

1. Boot with `B` held and confirm `self_test` sees `UP`, `DOWN`, `LEFT`, `RIGHT`, `CENTER`, `A`, and `B`.
2. Boot with `A` held and confirm `usb_diag` shows:
   `boot ready yes`, `usb.device ok`, `mouse src ...`, `kbd src ...`, `hid M/K yy`
3. Boot normally and verify:
   the LCD shows the mouse screen, movement updates on-screen, the host sees a working USB mouse, and `A+B` opens the keyboard screen where `A` types the selected key.

If normal runtime fails to open HID, the app falls back to `usb_diag`.

## Diagnostics

`usb_diag` is intentionally one screen only. It shows the main USB/HID state in six short lines and avoids paging.

Useful readings:
- `usb.device missing`: the `usb/` package did not deploy, or import failed
- `mouse pkg missing`: the `vendor/` package did not deploy
- `kbd pkg missing`: the keyboard helper in `vendor/` did not deploy
- `boot ready skip`: expected if you intentionally forced `usb_diag`
- `usb device unavailable`: runtime USB device object could not be opened
- `claim boot failed`: `boot.py` tried to claim HID and failed
- `hid M/K yn`: one HID interface is not usable

## Notes

- Input pins are active-low. If the LCD does not react to controls, check `self_test` first.
- `boot.py` is the primary HID claim path. Normal mouse boots should claim USB there, not later in the app.
- An attached REPL can interfere with USB enumeration. If HID behaves inconsistently, disconnect the REPL and hard reset.

## Files

- `main.py`: runtime entrypoint
- `boot.py`: early USB HID setup
- `lcd.py`: display driver for the Waveshare Pico-LCD-0.96
- `apps/mouse_app.py`: mouse UI, keyboard UI, and input-to-HID behavior
- `apps/self_test_app.py`: raw input verification
- `apps/usb_diag_app.py`: single-screen USB diagnostics
- `core/`: platform, launcher, controls, buttons, display, HID, boot-mode glue
- `usb/`: vendored `usb.device` runtime package
- `vendor/`: vendored HID mouse and keyboard helpers
