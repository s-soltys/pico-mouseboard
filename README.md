# Pico Mouseboard

MicroPython USB mouse controller for Raspberry Pi Pico 2 with the Waveshare Pico-LCD-0.96 display.

Hardware reference:
- https://www.waveshare.com/wiki/Pico-LCD-0.96

## Boot Modes

This build now supports three explicit modes:
- `mouse`: normal USB HID mouse mode
- `usb_diag`: inspect firmware and USB state without claiming HID at runtime
- `self_test`: verify every board input without touching USB HID

Boot selection:
- normal reset: `mouse`
- hold `A` during reset or power-up: `usb_diag`
- hold `B` during reset or power-up: `self_test`

## Mouse Controls

In `mouse` mode:
- joystick directions move the host cursor
- `A` sends left mouse button
- `B` sends right mouse button
- joystick press toggles slow and fast cursor speed

The LCD shows:
- startup progress and USB mouse status
- operating instructions
- live movement and button state visualization
- HID or runtime errors

## USB Support

The Pico is intended to enumerate as a generic USB mouse on macOS, Windows, and Linux by using MicroPython's `usb.device.mouse` interface.

`boot.py` is the primary HID claim path. On a normal mouse boot it claims the USB interface as early as possible. If you force `usb_diag` or `self_test`, `boot.py` skips HID claim so those modes can inspect the system without also changing USB state.

The app runtime only attempts a fallback HID claim when `boot.py` did not already run the mouse setup path.

Required firmware support:
- a recent MicroPython build for Pico 2 with `usb.device`
- `machine.USBDevice` support enabled in firmware

The repo vendors the mouse and HID helper modules, so a separate `mip install usb-device-mouse` step is not required as long as the firmware already provides `usb.device`.

If the LCD reports `usb.device missing`, the board firmware setup is incomplete. If it reports `usb mouse pkg missing`, then either the vendored files were not copied to the board or the base `usb.device` support is unavailable.

## Bring-Up Workflow

Use this order after flashing or after major USB changes:

1. Flash a recent Pico 2 MicroPython firmware with USB device support.
2. Copy `boot.py`, `main.py`, `screentest.py`, `lcd.py`, `core/`, `apps/`, and `vendor/` to the board.
3. Reset while holding `B` and confirm `self_test` sees every input: `UP`, `DOWN`, `LEFT`, `RIGHT`, `CENTER`, `A`, `B`.
4. Reset while holding `A` and confirm `usb_diag` sees the expected firmware and USB capabilities.
5. Reset normally into `mouse` mode and test host enumeration.

If USB mouse startup fails, the device automatically falls back to `usb_diag`.

## USB Diagnostics

Controls:
- pages auto-rotate every 2.5s
- `LEFT` / `RIGHT` or `A` / `B`: change page
- `CENTER`: rescan USB state

The pages show:
- whether boot-time HID setup was attempted and whether it succeeded
- whether `usb.device`, `usb.device.mouse`, and `machine.USBDevice` are present
- whether `usb.device.get()` returns a device object
- whether HID is already claimed and from which path
- whether a zero-motion report can be queued
- firmware/platform info

Interpret the results like this:
- `usb.device missing`: wrong or too old MicroPython firmware
- `mouse pkg missing`: vendored USB helper files did not deploy, or `usb.device` support is incomplete
- `boot skipped`: expected when you forced `usb_diag` or `self_test`
- `usb dev no` on a cold boot with no REPL attached: firmware or board USB support problem, not app logic
- `claim boot failed`: `boot.py` ran but HID setup failed before the app started
- `claim runtime claimed`: boot-time HID was skipped and the app manually claimed USB later
- `report send failed`: the HID interface exists but no report could be queued
- `init failed: ...`: capture the exact exception text from the LCD or serial log and debug that next

## Files

- `main.py`: MicroPython entrypoint for the mouse runtime
- `boot.py`: early USB mouse initialization for cold boots
- `screentest.py`: convenience wrapper that launches the same runtime manually
- `lcd.py`: Waveshare Pico-LCD-0.96 driver
- `core/`: shared platform, display, buttons, HID, boot mode, and runtime glue
- `apps/mouse_app.py`: mouse input handling and LCD UI
- `apps/self_test_app.py`: raw input verification
- `apps/usb_diag_app.py`: on-device USB diagnostics mode
- `vendor/`: vendored USB HID/mouse helper modules

## Deploying

1. Flash a recent Pico 2 MicroPython firmware with USB device support.
2. Copy `boot.py`, `main.py`, `screentest.py`, `lcd.py`, `core/`, `apps/`, and `vendor/` to the board.
3. Reboot the Pico.

After the first deploy, do a real reset or unplug/replug once so `boot.py` can claim USB during startup. If the board is started from an attached REPL or editor session and the LCD still shows `usb device unavailable`, close the REPL tool and reset again so MicroPython can reopen USB as a mouse.
