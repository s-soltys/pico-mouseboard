import random

from lcd import BLACK, WHITE, GRAY, YELLOW, GREEN, RED, CYAN
from core.ui import draw_header, draw_footer


class SpaceInvadersApp:
    app_id = "invaders"
    title = "Invaders"
    accent = GREEN

    def __init__(self):
        self.player_x = 78
        self.player_lives = 3
        self.aliens = []
        self.alien_dir = 1
        self.frame = 0
        self.player_bullet = None
        self.enemy_bullet = None
        self.score = 0
        self.state = "playing"

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        ink = BLACK if monochrome and selected else (WHITE if monochrome else GREEN)
        eye = BLACK if monochrome and selected else (WHITE if monochrome else RED)
        lcd.rect(cx - 8, cy - 5, 16, 9, ink)
        lcd.fill_rect(cx - 5, cy - 8, 10, 3, ink)
        lcd.pixel(cx - 4, cy - 2, eye)
        lcd.pixel(cx + 3, cy - 2, eye)
        lcd.vline(cx - 6, cy + 4, 4, ink)
        lcd.vline(cx + 5, cy + 4, 4, ink)

    def on_open(self, runtime):
        self.reset_game()

    def reset_game(self):
        self.player_x = 78
        self.player_lives = 3
        self.aliens = []
        for row in range(3):
            for col in range(5):
                self.aliens.append({
                    "x": 24 + (col * 22),
                    "y": 16 + (row * 10),
                    "alive": True,
                    "color": GREEN if row < 2 else CYAN,
                })
        self.alien_dir = 1
        self.frame = 0
        self.player_bullet = None
        self.enemy_bullet = None
        self.score = 0
        self.state = "playing"

    def _alive_aliens(self):
        alive = []
        for alien in self.aliens:
            if alien["alive"]:
                alive.append(alien)
        return alive

    def _move_aliens(self):
        alive = self._alive_aliens()
        if not alive:
            self.state = "won"
            return

        edge_hit = False
        for alien in alive:
            next_x = alien["x"] + (self.alien_dir * 5)
            if next_x < 10 or next_x > 146:
                edge_hit = True
                break

        if edge_hit:
            self.alien_dir *= -1
            for alien in alive:
                alien["y"] += 5
                if alien["y"] >= 56:
                    self.state = "lost"
        else:
            for alien in alive:
                alien["x"] += self.alien_dir * 5

    def _spawn_enemy_bullet(self):
        if self.enemy_bullet is not None:
            return
        alive = self._alive_aliens()
        if not alive:
            return
        shooter = alive[random.randint(0, len(alive) - 1)]
        self.enemy_bullet = {"x": shooter["x"], "y": shooter["y"] + 4}

    def _check_player_bullet(self):
        if self.player_bullet is None:
            return
        self.player_bullet["y"] -= 5
        if self.player_bullet["y"] < 11:
            self.player_bullet = None
            return

        for alien in self.aliens:
            if not alien["alive"]:
                continue
            if abs(self.player_bullet["x"] - alien["x"]) <= 7 and abs(self.player_bullet["y"] - alien["y"]) <= 5:
                alien["alive"] = False
                self.player_bullet = None
                self.score += 1
                return

    def _check_enemy_bullet(self):
        if self.enemy_bullet is None:
            return
        self.enemy_bullet["y"] += 4
        if self.enemy_bullet["y"] > 69:
            self.enemy_bullet = None
            return

        if abs(self.enemy_bullet["x"] - self.player_x) <= 9 and self.enemy_bullet["y"] >= 60:
            self.enemy_bullet = None
            self.player_lives -= 1
            if self.player_lives <= 0:
                self.state = "lost"

    def draw_scene(self, lcd):
        lcd.fill(BLACK)
        draw_header(lcd, "Invaders", "L" + str(self.player_lives), GREEN)

        for alien in self.aliens:
            if not alien["alive"]:
                continue
            x = alien["x"]
            y = alien["y"]
            lcd.rect(x - 6, y - 3, 12, 7, alien["color"])
            lcd.fill_rect(x - 3, y - 5, 6, 2, alien["color"])
            lcd.pixel(x - 3, y - 1, WHITE)
            lcd.pixel(x + 2, y - 1, WHITE)
            lcd.vline(x - 4, y + 4, 3, alien["color"])
            lcd.vline(x + 3, y + 4, 3, alien["color"])

        lcd.fill_rect(self.player_x - 9, 62, 18, 4, WHITE)
        lcd.fill_rect(self.player_x - 4, 58, 8, 4, CYAN)

        if self.player_bullet:
            lcd.vline(self.player_bullet["x"], self.player_bullet["y"], 4, YELLOW)
        if self.enemy_bullet:
            lcd.vline(self.enemy_bullet["x"], self.enemy_bullet["y"], 4, RED)

        lcd.text("S" + str(self.score), 120, 12, WHITE)

        if self.state == "playing":
            draw_footer(lcd, "B fire", GRAY)
            lcd.text("A reset", 80, 71, GRAY)
        elif self.state == "won":
            draw_footer(lcd, "Wave clear", CYAN)
            lcd.text("A restart", 72, 71, CYAN)
        else:
            draw_footer(lcd, "Invaded", RED)
            lcd.text("A restart", 72, 71, RED)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if buttons.pressed("A"):
            self.reset_game()

        if self.state == "playing":
            if buttons.down("LEFT"):
                self.player_x = max(16, self.player_x - 3)
            if buttons.down("RIGHT"):
                self.player_x = min(144, self.player_x + 3)
            if buttons.pressed("B") and self.player_bullet is None:
                self.player_bullet = {"x": self.player_x, "y": 56}

            self.frame += 1
            if self.frame % 8 == 0:
                self._move_aliens()
            if self.frame % 20 == 0:
                self._spawn_enemy_bullet()
            self._check_player_bullet()
            self._check_enemy_bullet()

        self.draw_scene(lcd)
        return None
