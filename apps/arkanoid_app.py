from lcd import BLACK, WHITE, GRAY, YELLOW, CYAN, RED, ORANGE, GREEN, BLUE
from core.ui import draw_header, draw_footer


BRICK_ROWS = 4
BRICK_COLS = 5
BRICK_W = 28
BRICK_H = 6
BRICK_X = 6
BRICK_Y = 14


class ArkanoidApp:
    app_id = "arkanoid"
    title = "Arkanoid"
    accent = CYAN

    def __init__(self):
        self.paddle_x = 68
        self.ball_x = 80
        self.ball_y = 56
        self.ball_vx = 2
        self.ball_vy = -2
        self.launched = False
        self.lives = 3
        self.state = "playing"
        self.bricks = []
        self.score = 0

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        ink = BLACK if monochrome and selected else (WHITE if monochrome else CYAN)
        brick = BLACK if monochrome and selected else (WHITE if monochrome else ORANGE)
        lcd.fill_rect(cx - 8, cy + 5, 16, 3, ink)
        lcd.ellipse(cx, cy + 1, 2, 2, WHITE if monochrome else YELLOW, True)
        lcd.rect(cx - 10, cy - 8, 7, 4, brick)
        lcd.rect(cx - 1, cy - 8, 7, 4, brick)
        lcd.rect(cx - 5, cy - 2, 7, 4, brick)

    def on_open(self, runtime):
        self.reset_game()

    def reset_game(self):
        self.paddle_x = 68
        self.ball_x = 80
        self.ball_y = 56
        self.ball_vx = 2
        self.ball_vy = -2
        self.launched = False
        self.lives = 3
        self.state = "playing"
        self.score = 0
        self.bricks = []
        row_colors = [RED, ORANGE, GREEN, BLUE]
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                self.bricks.append({
                    "x": BRICK_X + (col * (BRICK_W + 3)),
                    "y": BRICK_Y + (row * (BRICK_H + 3)),
                    "alive": True,
                    "color": row_colors[row],
                })

    def _reset_ball(self):
        self.ball_x = self.paddle_x + 12
        self.ball_y = 56
        self.ball_vx = 2
        self.ball_vy = -2
        self.launched = False

    def _update_ball(self):
        if not self.launched:
            self.ball_x = self.paddle_x + 12
            return

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_x <= 2 or self.ball_x >= 158:
            self.ball_vx *= -1
            self.ball_x += self.ball_vx
        if self.ball_y <= 12:
            self.ball_vy *= -1
            self.ball_y += self.ball_vy

        if self.ball_y >= 58 and self.paddle_x - 2 <= self.ball_x <= self.paddle_x + 26:
            self.ball_vy = -abs(self.ball_vy)
            hit = self.ball_x - (self.paddle_x + 12)
            if hit < -4:
                self.ball_vx = -3
            elif hit > 4:
                self.ball_vx = 3
            elif hit < 0:
                self.ball_vx = -2
            elif hit > 0:
                self.ball_vx = 2

        for brick in self.bricks:
            if not brick["alive"]:
                continue
            if brick["x"] <= self.ball_x <= brick["x"] + BRICK_W and brick["y"] <= self.ball_y <= brick["y"] + BRICK_H:
                brick["alive"] = False
                self.ball_vy *= -1
                self.score += 1
                break

        alive = False
        for brick in self.bricks:
            if brick["alive"]:
                alive = True
                break
        if not alive:
            self.state = "won"

        if self.ball_y > 69:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "lost"
            else:
                self._reset_ball()

    def draw_scene(self, lcd):
        lcd.fill(BLACK)
        draw_header(lcd, "Arkanoid", "L" + str(self.lives), CYAN)

        for brick in self.bricks:
            if brick["alive"]:
                lcd.fill_rect(brick["x"], brick["y"], BRICK_W, BRICK_H, brick["color"])
                lcd.rect(brick["x"], brick["y"], BRICK_W, BRICK_H, WHITE)

        lcd.fill_rect(self.paddle_x, 60, 24, 3, WHITE)
        lcd.ellipse(self.ball_x, self.ball_y, 2, 2, YELLOW, True)
        lcd.text("S" + str(self.score), 120, 12, WHITE)

        if self.state == "playing":
            if self.launched:
                draw_footer(lcd, "A reset", GRAY)
            else:
                draw_footer(lcd, "B launch", GRAY)
                lcd.text("A reset", 80, 71, GRAY)
        elif self.state == "won":
            draw_footer(lcd, "Wall clear", GREEN)
            lcd.text("A restart", 72, 71, GREEN)
        else:
            draw_footer(lcd, "No lives", RED)
            lcd.text("A restart", 72, 71, RED)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.pressed("A"):
            self.reset_game()

        if self.state == "playing":
            if buttons.down("LEFT"):
                self.paddle_x = max(4, self.paddle_x - 4)
            if buttons.down("RIGHT"):
                self.paddle_x = min(132, self.paddle_x + 4)
            if buttons.pressed("B") and not self.launched:
                self.launched = True
            self._update_ball()

        self.draw_scene(lcd)
        return None
