# Pico Launcher

Mini smartphone-style offline launcher for Raspberry Pi Pico 2 W with the Waveshare Pico-LCD-0.96 display.

Hardware reference:
- https://www.waveshare.com/wiki/Pico-LCD-0.96
- https://docs.micropython.org/en/latest/rp2/quickref.html

## What It Does

The device boots into a compact offline launcher instead of jumping straight into the galaxy explorer. Wireless support and network-backed apps have been removed in this repo version.

Included apps:
- `Galaxy`: the original galaxy/system/planet explorer
- `Mines`: compact minesweeper
- `Invaders`: arcade shooter
- `Pac-Man`: maze chase
- `Arkanoid`: brick breaker
- `Tetris`: falling-block puzzle

## Controls

Shared controls:
- D-pad: move selection / scroll / pan
- `A`: secondary action, back, cycle, or restart depending on the app
- `B`: primary action, open, select, or confirm depending on the app
- `A + B`: global home shortcut, returns to the launcher from any app

App-specific notes:
- `Galaxy`: `A` jumps to the next galaxy on the overview, `B` enters the current target, and `A` backs out of deeper views
- `Mines`: `A` toggles a flag while playing and restarts after a win/loss, `B` reveals a tile
- `Invaders`: D-pad moves, `B` fires, `A` restarts
- `Pac-Man`: D-pad steers, `B` pauses/resumes, `A` restarts
- `Arkanoid`: D-pad moves, `B` launches, `A` resets
- `Tetris`: D-pad moves, `A` rotates, `B` hard-drops

## Project Layout

- [main.py](/Users/szymon/Documents/pico-mouseboard/main.py): launcher entrypoint
- [lcd.py](/Users/szymon/Documents/pico-mouseboard/lcd.py): LCD driver
- [galaxy.py](/Users/szymon/Documents/pico-mouseboard/galaxy.py): galaxy generation and rendering engine
- [core/controls.py](/Users/szymon/Documents/pico-mouseboard/core/controls.py): canonical pin map and shared control labels
- [core/launcher.py](/Users/szymon/Documents/pico-mouseboard/core/launcher.py): shared runtime and home screen
- [core/buttons.py](/Users/szymon/Documents/pico-mouseboard/core/buttons.py): GPIO input handling and `A + B` home-chord detection
- [core/ui.py](/Users/szymon/Documents/pico-mouseboard/core/ui.py): shared drawing helpers
- [apps/](/Users/szymon/Documents/pico-mouseboard/apps): launcher apps

## Adding Apps

1. Create a new app class under `apps/`.
2. Give it `app_id`, `title`, `accent`, `draw_icon()`, `on_open()`, and `step()` methods.
3. Register it in [apps/__init__.py](/Users/szymon/Documents/pico-mouseboard/apps/__init__.py).
4. Keep navigation on the shared button model and do not bypass the global `A + B` home gesture.

`step(runtime)` is called once per frame. Use:
- `runtime.lcd` for drawing
- `runtime.buttons` for button state

## Deploying

This project is written for MicroPython on Pico 2 W and runs as an offline launcher on the Waveshare Pico-LCD-0.96.

Typical flow:
1. Flash MicroPython to the board if needed.
2. Copy the project files and folders to the device.
3. Ensure `main.py` is present at the device root.
4. Reboot the board.

If you use the VS Code MicroPico workflow, upload the full repo so `core/` and `apps/` are copied alongside `main.py`.
