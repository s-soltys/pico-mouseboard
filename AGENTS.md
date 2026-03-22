# Agent Notes

## Overview

This repo is a dedicated MicroPython mouse and keyboard controller for Raspberry Pi Pico 2 W plus the Waveshare Pico-LCD-0.96 screen.

The runtime is intentionally small:
- `main.py` boots the controller
- `core/` contains reusable platform, HID, and UI code
- `apps/hid_tools_app.py` contains the on-device keyboard and mouse screen

## Architecture Rules

- Keep `main.py` thin. Startup and frame-loop logic belongs in [core/launcher.py](/Users/szymon/Documents/pico-mouseboard/core/launcher.py).
- Keep GPIO button setup centralized in [core/buttons.py](/Users/szymon/Documents/pico-mouseboard/core/buttons.py). Do not create raw `Pin` readers inside UI modules.
- Preserve the physical naming convention in user-facing text: `Top (A)` and `Bottom (B)`.
- Reuse [core/ui.py](/Users/szymon/Documents/pico-mouseboard/core/ui.py) helpers for headers and footers instead of inventing one-off chrome.
- Keep memory use conservative. Prefer drawn icons and static in-memory data over large assets.

## Runtime Contract

`runtime` provides:
- `lcd`
- `buttons`
- no network helper; the controller should remain fully usable offline

The controller module is expected to:
- expose `on_open(runtime)`
- expose `step(runtime)`
- read button state
- draw one frame

## Input Conventions

- Use `buttons.pressed(name)` for one-shot actions.
- Use `buttons.repeat(name)` for cursor movement.
- Use `buttons.down(name)` for continuous panning or movement.

## Validation

When making changes:
- run a syntax-only check such as `env PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile main.py boot.py lcd.py core/*.py apps/*.py`
- prefer hardware-safe changes that keep the controller usable in the offline-only build
- document any new control or runtime convention in `README.md`
