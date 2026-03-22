import random

from lcd import BLACK, WHITE, GRAY, YELLOW, BLUE, RED, CYAN, GREEN, ORANGE
from core.ui import draw_header, draw_footer


PAC_MAP = [
    "##############",
    "#....#.......#",
    "#.##.#.###.#.#",
    "#o..P....G...#",
    "#.#.###.#.##.#",
    "#....H....o..#",
    "##############",
]

CELL = 8
MAP_X = 24
MAP_Y = 12
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class PacmanApp:
    app_id = "pacman"
    title = "Pac-Man"
    accent = YELLOW

    def __init__(self):
        self.walls = set()
        self.dots = {}
        self.player_x = 1
        self.player_y = 1
        self.player_dir = (1, 0)
        self.want_dir = (1, 0)
        self.ghosts = []
        self.score = 0
        self.state = "playing"
        self.paused = False
        self.power_timer = 0
        self.frame = 0

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        ink = BLACK if monochrome and selected else (WHITE if monochrome else YELLOW)
        eye = BLACK if monochrome and selected else WHITE
        lcd.ellipse(cx, cy, 8, 8, ink, True)
        lcd.pixel(cx + 4, cy - 2, eye)
        lcd.pixel(cx + 5, cy, eye)
        lcd.pixel(cx + 4, cy + 2, eye)
        lcd.fill_rect(cx + 1, cy - 3, 7, 6, BLACK if monochrome and selected else BLACK)

    def on_open(self, runtime):
        self.reset_game()

    def reset_game(self):
        self.walls = set()
        self.dots = {}
        self.ghosts = []
        self.score = 0
        self.state = "playing"
        self.paused = False
        self.power_timer = 0
        self.frame = 0
        for y in range(len(PAC_MAP)):
            row = PAC_MAP[y]
            for x in range(len(row)):
                cell = row[x]
                if cell == "#":
                    self.walls.add((x, y))
                elif cell == ".":
                    self.dots[(x, y)] = "dot"
                elif cell == "o":
                    self.dots[(x, y)] = "power"
                elif cell == "P":
                    self.player_x = x
                    self.player_y = y
                elif cell == "G":
                    self.ghosts.append({
                        "start": (x, y),
                        "x": x,
                        "y": y,
                        "dir": (-1, 0),
                        "color": RED,
                    })
                elif cell == "H":
                    self.ghosts.append({
                        "start": (x, y),
                        "x": x,
                        "y": y,
                        "dir": (1, 0),
                        "color": CYAN,
                    })
        self.player_dir = (1, 0)
        self.want_dir = (1, 0)

    def _passable(self, x, y):
        if x < 0 or y < 0 or y >= len(PAC_MAP) or x >= len(PAC_MAP[0]):
            return False
        return (x, y) not in self.walls

    def _update_player(self):
        wx, wy = self.want_dir
        if self._passable(self.player_x + wx, self.player_y + wy):
            self.player_dir = self.want_dir

        dx, dy = self.player_dir
        if self._passable(self.player_x + dx, self.player_y + dy):
            self.player_x += dx
            self.player_y += dy

        pos = (self.player_x, self.player_y)
        if pos in self.dots:
            dot = self.dots[pos]
            del self.dots[pos]
            self.score += 1
            if dot == "power":
                self.power_timer = 40
                self.score += 3
        if not self.dots:
            self.state = "won"

    def _move_ghost(self, ghost):
        reverse = (-ghost["dir"][0], -ghost["dir"][1])
        best_dirs = []
        best_score = None
        for direction in DIRS:
            nx = ghost["x"] + direction[0]
            ny = ghost["y"] + direction[1]
            if not self._passable(nx, ny):
                continue
            if direction == reverse and len(best_dirs) > 0:
                continue
            score = abs(nx - self.player_x) + abs(ny - self.player_y)
            if self.power_timer > 0:
                score = -score
            if best_score is None or score < best_score:
                best_score = score
                best_dirs = [direction]
            elif score == best_score:
                best_dirs.append(direction)

        if not best_dirs:
            if self._passable(ghost["x"] + reverse[0], ghost["y"] + reverse[1]):
                best_dirs = [reverse]
            else:
                return

        choice = best_dirs[random.randint(0, len(best_dirs) - 1)]
        ghost["dir"] = choice
        ghost["x"] += choice[0]
        ghost["y"] += choice[1]

    def _check_collisions(self):
        for ghost in self.ghosts:
            if ghost["x"] == self.player_x and ghost["y"] == self.player_y:
                if self.power_timer > 0:
                    ghost["x"], ghost["y"] = ghost["start"]
                    ghost["dir"] = (0, 0)
                    self.score += 5
                else:
                    self.state = "lost"

    def draw_scene(self, lcd):
        lcd.fill(BLACK)
        draw_header(lcd, "Pac-Man", "S" + str(self.score), YELLOW)

        for y in range(len(PAC_MAP)):
            for x in range(len(PAC_MAP[0])):
                px = MAP_X + (x * CELL)
                py = MAP_Y + (y * CELL)
                if (x, y) in self.walls:
                    lcd.rect(px, py, CELL, CELL, BLUE)
                    lcd.fill_rect(px + 1, py + 1, CELL - 2, CELL - 2, BLACK)
                elif (x, y) in self.dots:
                    if self.dots[(x, y)] == "power":
                        lcd.ellipse(px + 4, py + 4, 2, 2, ORANGE, True)
                    else:
                        lcd.pixel(px + 4, py + 4, WHITE)

        px = MAP_X + (self.player_x * CELL) + 4
        py = MAP_Y + (self.player_y * CELL) + 4
        lcd.ellipse(px, py, 3, 3, YELLOW, True)
        if self.player_dir == (1, 0):
            lcd.fill_rect(px + 1, py - 2, 3, 4, BLACK)
        elif self.player_dir == (-1, 0):
            lcd.fill_rect(px - 4, py - 2, 3, 4, BLACK)
        elif self.player_dir == (0, -1):
            lcd.fill_rect(px - 2, py - 4, 4, 3, BLACK)
        else:
            lcd.fill_rect(px - 2, py + 1, 4, 3, BLACK)

        for ghost in self.ghosts:
            gx = MAP_X + (ghost["x"] * CELL) + 4
            gy = MAP_Y + (ghost["y"] * CELL) + 4
            color = GREEN if self.power_timer > 0 else ghost["color"]
            lcd.fill_rect(gx - 3, gy - 2, 6, 5, color)
            lcd.ellipse(gx, gy - 2, 3, 3, color, True)
            lcd.pixel(gx - 1, gy - 1, WHITE)
            lcd.pixel(gx + 1, gy - 1, WHITE)

        if self.state == "playing" and not self.paused:
            draw_footer(lcd, "B pause", GRAY)
        elif self.paused:
            draw_footer(lcd, "Paused", CYAN)
            lcd.text("B resume", 60, 71, CYAN)
        elif self.state == "won":
            draw_footer(lcd, "Maze clear", GREEN)
            lcd.text("A restart", 72, 71, GREEN)
        else:
            draw_footer(lcd, "Caught", RED)
            lcd.text("A restart", 72, 71, RED)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.pressed("A"):
            self.reset_game()

        if buttons.down("LEFT"):
            self.want_dir = (-1, 0)
        elif buttons.down("RIGHT"):
            self.want_dir = (1, 0)
        elif buttons.down("UP"):
            self.want_dir = (0, -1)
        elif buttons.down("DOWN"):
            self.want_dir = (0, 1)

        if self.state == "playing":
            if buttons.pressed("B"):
                self.paused = not self.paused
            if not self.paused:
                self.frame += 1
                if self.frame % 4 == 0:
                    self._update_player()
                    self._check_collisions()
                if self.frame % 5 == 0:
                    for ghost in self.ghosts:
                        self._move_ghost(ghost)
                    self._check_collisions()
                if self.power_timer > 0 and self.frame % 2 == 0:
                    self.power_timer -= 1
        elif buttons.pressed("B"):
            self.reset_game()

        self.draw_scene(lcd)
        return None
