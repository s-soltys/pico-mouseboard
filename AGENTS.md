# Agent Notes

## Overview

This repo is a MicroPython launcher shell for Raspberry Pi Pico 2 W plus the Waveshare Pico-LCD-0.96 screen.

The runtime is intentionally small:
- `main.py` boots the launcher
- `core/` contains reusable platform and UI code
- `apps/` contains user-facing launcher apps
- `galaxy.py` remains the content engine for the Galaxy app

## Architecture Rules

- Keep `main.py` thin. Startup and frame-loop logic belongs in [core/launcher.py](/Users/szymon/Documents/pico-mouseboard/core/launcher.py).
- Keep GPIO button setup centralized in [core/buttons.py](/Users/szymon/Documents/pico-mouseboard/core/buttons.py). Do not create raw `Pin` readers inside individual apps.
- Preserve the physical naming convention in user-facing text: `Top (A)` and `Bottom (B)`.
- Preserve the global `Top + Bottom` home shortcut. App code must not block or rebind it.
- Reuse [core/ui.py](/Users/szymon/Documents/pico-mouseboard/core/ui.py) helpers for headers, footers, and tile styling instead of inventing per-app chrome.
- Keep memory use conservative. Prefer drawn icons and static in-memory data over large assets.
- Favor small in-code game state and drawn sprites over external assets for launcher mini-games.
- Launcher tiles and icons should remain black-and-white even if the app itself uses color internally.

## App Contract

Each app should expose:
- `app_id`
- `title`
- `accent`
- `draw_icon(lcd, cx, cy, selected)`
- `on_open(runtime)`
- `step(runtime)`

Apps are registered in [apps/__init__.py](/Users/szymon/Documents/pico-mouseboard/apps/__init__.py).

`runtime` provides:
- `lcd`
- `buttons`
- no network helper; apps should remain fully usable offline

`step(runtime)` is expected to:
- read button state
- draw one frame
- return `None` for normal operation or `"home"` if it wants to exit back to the launcher

## Input Conventions

- Use `buttons.pressed(name)` for one-shot actions.
- Use `buttons.repeat(name)` for menu/list movement.
- Use `buttons.down(name)` for continuous panning or movement.
- Let the launcher own the home gesture handling. App code should assume the launcher may interrupt any frame and return home.

## Validation

When making changes:
- run a syntax-only check such as `env PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile main.py galaxy.py lcd.py core/*.py apps/*.py`
- prefer hardware-safe changes that keep the app usable in the offline-only launcher build
- document any new app controls or runtime conventions in `README.md`
