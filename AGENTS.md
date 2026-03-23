# AGENTS

This repo targets a Raspberry Pi Pico 2 running MicroPython with the Waveshare Pico-LCD-0.96 board. Treat it as a hardware-facing firmware project, not a generic Python app.

## What Matters

- USB mouse support depends on `machine.USBDevice` plus the vendored `usb/` and `vendor/` folders in this repo.
- `boot.py` is the intended place to claim the HID interface for normal mouse boots.
- `usb_diag` and `self_test` deliberately avoid the normal mouse boot path so failures can be isolated.
- Inputs are active-low. For this board, `Pin.value()` should be interpreted as pressed when it returns `0`.

## Working Assumptions

- Default boot mode is `mouse`.
- Hold `A` at boot for `usb_diag`.
- Hold `B` at boot for `self_test`.
- Current mouse speed steps are defined in `apps/mouse_app.py` and are intentionally higher than the original values.

## Safe Change Strategy

- If USB stops enumerating, debug in this order:
  1. confirm `usb/` and `vendor/` were deployed
  2. verify `self_test` still sees all inputs
  3. check `usb_diag`
  4. only then change HID logic
- Prefer small changes to `core/usb_boot.py`, `core/hid.py`, and `apps/usb_diag_app.py`; these files are tightly coupled.
- When changing button handling, verify behavior in both `self_test` and `mouse` mode.
- When changing boot behavior, keep `boot.py` and `core/boot_mode.py` aligned.

## File Map

- `apps/mouse_app.py`: main end-user behavior
- `apps/self_test_app.py`: quickest way to verify hardware input
- `apps/usb_diag_app.py`: quickest way to verify USB stack state
- `core/buttons.py`: raw active-low input handling
- `core/controls.py`: button names and GPIO map
- `core/usb_boot.py`: boot-time USB/HID setup and status tracking
- `core/hid.py`: runtime HID wrapper
- `usb/device/`: vendored runtime USB support
- `vendor/`: vendored HID interface implementations

## Practical Guidance

- Keep diagnostics concise enough to fit the LCD without paging unless there is a strong reason otherwise.
- If documentation changes, keep the README focused on deployment and use, and keep this file focused on engineering pitfalls.
- Assume changes need on-device verification; desktop-only checks are useful for syntax, not for final confidence.
