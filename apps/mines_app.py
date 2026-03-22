import random
import time

from lcd import BLACK, WHITE, GRAY, YELLOW, GREEN, RED, CYAN, BLUE, ORANGE, SLATE, DKGRN
from core.ui import draw_header, draw_footer


GRID_W = 8
GRID_H = 5
CELL_W = 16
CELL_H = 12
GRID_X = 16
GRID_Y = 10
MINE_COUNT = 7

COUNT_COLORS = {
    1: CYAN,
    2: GREEN,
    3: ORANGE,
    4: BLUE,
    5: RED,
}


class MinesApp:
    app_id = "mines"
    title = "Mines"
    accent = GREEN

    def __init__(self):
        self.board = []
        self.revealed = []
        self.flagged = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.state = "playing"
        self.revealed_count = 0
        self.exploded = None

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        ink = BLACK if monochrome and selected else (WHITE if monochrome else GREEN)
        mark = BLACK if monochrome and selected else (WHITE if monochrome else RED)
        lcd.ellipse(cx, cy, 7, 7, ink, False)
        lcd.hline(cx - 8, cy, 17, ink)
        lcd.vline(cx, cy - 8, 17, ink)
        lcd.pixel(cx - 5, cy - 5, mark)
        lcd.pixel(cx + 5, cy + 5, mark)

    def on_open(self, runtime):
        self.reset_board()

    def reset_board(self):
        self.board = []
        self.revealed = []
        self.flagged = []
        for _ in range(GRID_H):
            self.board.append([0] * GRID_W)
            self.revealed.append([False] * GRID_W)
            self.flagged.append([False] * GRID_W)

        random.seed(time.ticks_ms())
        placed = 0
        while placed < MINE_COUNT:
            idx = random.randint(0, (GRID_W * GRID_H) - 1)
            x = idx % GRID_W
            y = idx // GRID_W
            if self.board[y][x] == -1:
                continue
            self.board[y][x] = -1
            placed += 1

        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.board[y][x] == -1:
                    continue
                count = 0
                for ny in range(max(0, y - 1), min(GRID_H, y + 2)):
                    for nx in range(max(0, x - 1), min(GRID_W, x + 2)):
                        if self.board[ny][nx] == -1:
                            count += 1
                self.board[y][x] = count

        self.cursor_x = 0
        self.cursor_y = 0
        self.state = "playing"
        self.revealed_count = 0
        self.exploded = None

    def count_flags(self):
        total = 0
        for row in self.flagged:
            for cell in row:
                if cell:
                    total += 1
        return total

    def reveal_cell(self, start_x, start_y):
        if self.flagged[start_y][start_x] or self.revealed[start_y][start_x]:
            return

        if self.board[start_y][start_x] == -1:
            self.state = "lost"
            self.exploded = (start_x, start_y)
            for y in range(GRID_H):
                for x in range(GRID_W):
                    if self.board[y][x] == -1:
                        self.revealed[y][x] = True
            return

        stack = [(start_x, start_y)]
        while stack:
            x, y = stack.pop()
            if self.revealed[y][x] or self.flagged[y][x]:
                continue

            self.revealed[y][x] = True
            self.revealed_count += 1

            if self.board[y][x] != 0:
                continue

            for ny in range(max(0, y - 1), min(GRID_H, y + 2)):
                for nx in range(max(0, x - 1), min(GRID_W, x + 2)):
                    if not self.revealed[ny][nx] and self.board[ny][nx] != -1:
                        stack.append((nx, ny))

        if self.revealed_count >= (GRID_W * GRID_H) - MINE_COUNT:
            self.state = "won"
            for y in range(GRID_H):
                for x in range(GRID_W):
                    if self.board[y][x] == -1:
                        self.flagged[y][x] = True

    def toggle_flag(self, x, y):
        if self.revealed[y][x]:
            return
        self.flagged[y][x] = not self.flagged[y][x]

    def draw_grid(self, lcd):
        for y in range(GRID_H):
            for x in range(GRID_W):
                px = GRID_X + (x * CELL_W)
                py = GRID_Y + (y * CELL_H)
                revealed = self.revealed[y][x]
                selected = (x == self.cursor_x and y == self.cursor_y)
                fill = SLATE if not revealed else BLACK
                border = YELLOW if selected else GRAY
                if revealed and self.board[y][x] == -1:
                    fill = RED if self.exploded == (x, y) else DKGRN
                lcd.fill_rect(px + 1, py + 1, CELL_W - 2, CELL_H - 2, fill)
                lcd.rect(px, py, CELL_W, CELL_H, border)

                if self.flagged[y][x] and not revealed:
                    lcd.vline(px + 5, py + 3, 6, WHITE)
                    lcd.fill_rect(px + 6, py + 3, 4, 3, RED)
                    lcd.hline(px + 3, py + 9, 7, WHITE)
                    continue

                if not revealed:
                    continue

                value = self.board[y][x]
                if value == -1:
                    lcd.ellipse(px + 8, py + 6, 3, 3, BLACK, True)
                    lcd.hline(px + 3, py + 6, 10, WHITE)
                    lcd.vline(px + 8, py + 1, 10, WHITE)
                elif value > 0:
                    lcd.text(str(value), px + 4, py + 2, COUNT_COLORS.get(value, WHITE))

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.repeat("LEFT"):
            self.cursor_x = max(0, self.cursor_x - 1)
        if buttons.repeat("RIGHT"):
            self.cursor_x = min(GRID_W - 1, self.cursor_x + 1)
        if buttons.repeat("UP"):
            self.cursor_y = max(0, self.cursor_y - 1)
        if buttons.repeat("DOWN"):
            self.cursor_y = min(GRID_H - 1, self.cursor_y + 1)

        if self.state == "playing":
            if buttons.pressed("A"):
                self.toggle_flag(self.cursor_x, self.cursor_y)
            if buttons.pressed("B"):
                self.reveal_cell(self.cursor_x, self.cursor_y)
        elif buttons.pressed("A"):
            self.reset_board()

        lcd.fill(BLACK)
        mines_left = MINE_COUNT - self.count_flags()
        draw_header(lcd, "Mines", "M" + str(mines_left), GREEN)
        self.draw_grid(lcd)

        if self.state == "won":
            draw_footer(lcd, "Cleared! A new", CYAN)
        elif self.state == "lost":
            draw_footer(lcd, "Boom. A retry", RED)
        else:
            draw_footer(lcd, "B dig", GRAY)
            lcd.text("A flag", 80, 71, GRAY)
        return None
