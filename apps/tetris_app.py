import random

from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, ORANGE, GREEN, RED, BLUE, PURPLE
from core.ui import draw_header, draw_footer


BOARD_W = 10
BOARD_H = 12
CELL = 5
BOARD_X = 22
BOARD_Y = 10

SHAPES = [
    [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
]

COLORS = [CYAN, YELLOW, PURPLE, BLUE, ORANGE, GREEN, RED]


class TetrisApp:
    app_id = "tetris"
    title = "Tetris"
    accent = PURPLE

    def __init__(self):
        self.board = []
        self.current = None
        self.next_index = 0
        self.drop_tick = 0
        self.lines = 0
        self.state = "playing"

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        ink = BLACK if monochrome and selected else (WHITE if monochrome else PURPLE)
        lcd.fill_rect(cx - 10, cy - 7, 6, 6, ink)
        lcd.fill_rect(cx - 4, cy - 7, 6, 6, ink)
        lcd.fill_rect(cx + 2, cy - 7, 6, 6, ink)
        lcd.fill_rect(cx - 4, cy - 1, 6, 6, ink)

    def on_open(self, runtime):
        self.reset_game()

    def reset_game(self):
        self.board = []
        for _ in range(BOARD_H):
            self.board.append([0] * BOARD_W)
        self.lines = 0
        self.state = "playing"
        self.drop_tick = 0
        self.next_index = random.randint(0, len(SHAPES) - 1)
        self._spawn_piece()

    def _spawn_piece(self):
        self.current = {
            "shape": self.next_index,
            "rot": 0,
            "x": 3,
            "y": 0,
        }
        self.drop_tick = 0
        self.next_index = random.randint(0, len(SHAPES) - 1)
        if not self._can_place(self.current["x"], self.current["y"], self.current["shape"], self.current["rot"]):
            self.state = "lost"

    def _cells(self, shape_index, rot):
        rotations = SHAPES[shape_index]
        return rotations[rot % len(rotations)]

    def _can_place(self, px, py, shape_index, rot):
        for ox, oy in self._cells(shape_index, rot):
            x = px + ox
            y = py + oy
            if x < 0 or x >= BOARD_W or y < 0 or y >= BOARD_H:
                return False
            if self.board[y][x]:
                return False
        return True

    def _try_move(self, dx, dy, new_rot=None):
        if self.state != "playing" or self.current is None:
            return False
        rot = self.current["rot"] if new_rot is None else new_rot
        nx = self.current["x"] + dx
        ny = self.current["y"] + dy
        if self._can_place(nx, ny, self.current["shape"], rot):
            self.current["x"] = nx
            self.current["y"] = ny
            self.current["rot"] = rot
            return True
        return False

    def _rotate(self):
        if self.state != "playing":
            return
        new_rot = (self.current["rot"] + 1) % len(SHAPES[self.current["shape"]])
        if self._try_move(0, 0, new_rot):
            return
        if self._try_move(-1, 0, new_rot):
            return
        self._try_move(1, 0, new_rot)

    def _lock_piece(self):
        color = COLORS[self.current["shape"]]
        for ox, oy in self._cells(self.current["shape"], self.current["rot"]):
            x = self.current["x"] + ox
            y = self.current["y"] + oy
            if 0 <= y < BOARD_H and 0 <= x < BOARD_W:
                self.board[y][x] = color

        new_rows = []
        cleared = 0
        for row in self.board:
            full = True
            for cell in row:
                if not cell:
                    full = False
                    break
            if full:
                cleared += 1
            else:
                new_rows.append(row)

        while len(new_rows) < BOARD_H:
            new_rows.insert(0, [0] * BOARD_W)
        self.board = new_rows
        self.lines += cleared
        self._spawn_piece()

    def _hard_drop(self):
        if self.state != "playing":
            return
        while self._try_move(0, 1):
            pass
        self._lock_piece()

    def draw_scene(self, lcd):
        lcd.fill(BLACK)
        draw_header(lcd, "Tetris", "L" + str(self.lines), PURPLE)

        lcd.rect(BOARD_X - 1, BOARD_Y, BOARD_W * CELL + 2, BOARD_H * CELL, WHITE)
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                px = BOARD_X + (x * CELL)
                py = BOARD_Y + (y * CELL)
                color = self.board[y][x] if self.board[y][x] else BLACK
                lcd.fill_rect(px, py, CELL - 1, CELL - 1, color)
                if not color:
                    lcd.rect(px, py, CELL, CELL, GRAY)

        if self.current is not None:
            color = COLORS[self.current["shape"]]
            for ox, oy in self._cells(self.current["shape"], self.current["rot"]):
                x = self.current["x"] + ox
                y = self.current["y"] + oy
                px = BOARD_X + (x * CELL)
                py = BOARD_Y + (y * CELL)
                lcd.fill_rect(px, py, CELL - 1, CELL - 1, color)

        lcd.text("Next", 92, 18, WHITE)
        preview = SHAPES[self.next_index][0]
        for ox, oy in preview:
            px = 98 + (ox * 5)
            py = 30 + (oy * 5)
            lcd.fill_rect(px, py, 4, 4, COLORS[self.next_index])

        if self.state == "lost":
            lcd.text("LOCKED", 92, 48, RED)

        if self.state == "playing":
            draw_footer(lcd, "A rotate", GRAY)
            lcd.text("B drop", 64, 71, GRAY)
        else:
            draw_footer(lcd, "A restart", RED)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.pressed("A"):
            if self.state == "playing":
                self._rotate()
            else:
                self.reset_game()

        if self.state == "playing":
            if buttons.repeat("LEFT", 200, 100):
                self._try_move(-1, 0)
            if buttons.repeat("RIGHT", 200, 100):
                self._try_move(1, 0)
            if buttons.repeat("DOWN", 80, 60):
                if not self._try_move(0, 1):
                    self._lock_piece()
            if buttons.pressed("B"):
                self._hard_drop()

            self.drop_tick += 1
            if self.drop_tick >= 15:
                self.drop_tick = 0
                if not self._try_move(0, 1):
                    self._lock_piece()

        self.draw_scene(lcd)
        return None
