import galaxy
import time

from lcd import CYAN, WHITE, YELLOW, BLACK, GRAY, GOLD


class GalaxyApp:
    app_id = "galaxy"
    title = "Galaxy"
    accent = CYAN

    def __init__(self):
        self.state = galaxy.STATE_GALAXYSEL
        self.galaxies = None
        self.sel_gal = 0
        self.systems = None
        self.cur_shape = 0
        self.uvx = 0
        self.uvy = 0
        self.vx = 0
        self.vy = 0
        self.sel_idx = 0
        self.planets = None
        self.sel_planet = 0
        self.regions = None
        self.sel_region = 0
        self.scroll_speed = 4
        self.show_splash = False
        self.splash_until = 0
        self.splash_phase = 0

    def draw_icon(self, lcd, cx, cy, selected, monochrome=False):
        if monochrome:
            ink = BLACK if selected else WHITE
            lcd.ellipse(cx, cy, 10, 6, ink, False)
            lcd.ellipse(cx, cy, 2, 2, ink, True)
            lcd.pixel(cx - 7, cy, ink)
            lcd.pixel(cx + 8, cy - 1, ink)
            return
        lcd.ellipse(cx, cy, 10, 6, CYAN, False)
        lcd.ellipse(cx, cy, 2, 2, YELLOW, True)
        lcd.pixel(cx - 7, cy, WHITE)
        lcd.pixel(cx + 8, cy - 1, WHITE)
        if selected:
            lcd.ellipse(cx, cy, 13, 9, YELLOW, False)

    def on_open(self, runtime):
        self.show_splash = True
        self.splash_phase = time.ticks_ms()
        self.splash_until = time.ticks_add(self.splash_phase, 1100)
        self._init_world()

    def _init_world(self):
        self.galaxies = galaxy.gen_galaxy_list(8)
        self.sel_gal = 0
        self.state = galaxy.STATE_GALAXYSEL
        self.systems = None
        self.cur_shape = 0
        self.vx = 0
        self.vy = 0
        self.sel_idx = 0
        self.planets = None
        self.sel_planet = 0
        self.regions = None
        self.sel_region = 0
        g = self.galaxies[0]
        self.uvx = max(0, min(galaxy.UNIV_W - 160, g[4] - 80))
        self.uvy = max(0, min(galaxy.UNIV_H - 80, g[5] - 40))

    def _draw_splash(self, lcd):
        tick = time.ticks_ms()
        lcd.fill(BLACK)
        galaxy.draw_bg_stars(lcd, (tick // 7) % 400, (tick // 11) % 300)
        galaxy._draw_mini_galaxy(lcd, 36, 38, 0, CYAN, False)
        galaxy._draw_mini_galaxy(lcd, 82, 28, 1, GOLD, False)
        galaxy._draw_mini_galaxy(lcd, 126, 42, 4, YELLOW, False)
        lcd.text("GALAXY", 40, 10, CYAN)
        lcd.text("EXPLORER", 32, 22, WHITE)
        lcd.text("Charting stars", 28, 54, GRAY)
        lcd.text("A/B skip", 20, 66, YELLOW)

    def step(self, runtime):
        buttons = runtime.buttons
        lcd = runtime.lcd

        if self.show_splash:
            self._draw_splash(lcd)
            if (buttons.pressed("A") or buttons.pressed("B")
                    or time.ticks_diff(time.ticks_ms(), self.splash_until) >= 0):
                self.show_splash = False
            return None

        if self.state == galaxy.STATE_GALAXYSEL:
            if buttons.down("UP"):
                self.uvy = max(0, self.uvy - self.scroll_speed)
            if buttons.down("DOWN"):
                self.uvy = min(galaxy.UNIV_H - 80, self.uvy + self.scroll_speed)
            if buttons.down("LEFT"):
                self.uvx = max(0, self.uvx - self.scroll_speed)
            if buttons.down("RIGHT"):
                self.uvx = min(galaxy.UNIV_W - 160, self.uvx + self.scroll_speed)
            if buttons.pressed("A"):
                self.sel_gal = (self.sel_gal + 1) % len(self.galaxies)
                entry = self.galaxies[self.sel_gal]
                self.uvx = max(0, min(galaxy.UNIV_W - 160, entry[4] - 80))
                self.uvy = max(0, min(galaxy.UNIV_H - 80, entry[5] - 40))
            if buttons.pressed("B"):
                self.sel_gal = galaxy.find_nearest_gal(self.galaxies, self.uvx, self.uvy)
                if self.sel_gal >= 0:
                    entry = self.galaxies[self.sel_gal]
                    self.cur_shape = entry[2]
                    self.systems = galaxy.gen_galaxy(entry[0], self.cur_shape)
                    self.vx = max(0, min(galaxy.WORLD_W - 160, self.systems[0][0] - 80))
                    self.vy = max(0, min(galaxy.WORLD_H - 80, self.systems[0][1] - 40))
                    self.sel_idx = 0
                    self.state = galaxy.STATE_GALAXY
            self.sel_gal = galaxy.find_nearest_gal(self.galaxies, self.uvx, self.uvy)
            galaxy.draw_galaxy_sel(lcd, self.galaxies, self.uvx, self.uvy, self.sel_gal)
            return None

        if self.state == galaxy.STATE_GALAXY:
            if buttons.down("UP"):
                self.vy = max(0, self.vy - self.scroll_speed)
            if buttons.down("DOWN"):
                self.vy = min(galaxy.WORLD_H - 80, self.vy + self.scroll_speed)
            if buttons.down("LEFT"):
                self.vx = max(0, self.vx - self.scroll_speed)
            if buttons.down("RIGHT"):
                self.vx = min(galaxy.WORLD_W - 160, self.vx + self.scroll_speed)
            if buttons.pressed("B"):
                self.sel_idx = galaxy.find_nearest(self.systems, self.vx, self.vy)
                if self.sel_idx >= 0:
                    self.planets = galaxy.gen_planets(self.systems[self.sel_idx])
                    self.sel_planet = 0
                    self.state = galaxy.STATE_SYSTEM
            if buttons.pressed("A"):
                self.state = galaxy.STATE_GALAXYSEL
            self.sel_idx = galaxy.find_nearest(self.systems, self.vx, self.vy)
            galaxy.draw_galaxy(lcd, self.systems, self.vx, self.vy, self.sel_idx)
            return None

        if self.state == galaxy.STATE_SYSTEM:
            if buttons.repeat("LEFT", 180, 120):
                self.sel_planet = (self.sel_planet - 1) % len(self.planets)
            if buttons.repeat("RIGHT", 180, 120):
                self.sel_planet = (self.sel_planet + 1) % len(self.planets)
            if buttons.pressed("B"):
                self.regions = galaxy.gen_regions(self.planets[self.sel_planet])
                self.sel_region = 0
                self.state = galaxy.STATE_PLANET
            if buttons.pressed("A"):
                self.state = galaxy.STATE_GALAXY

            for planet in self.planets:
                planet[5] += planet[6]
                if planet[5] > 6.283:
                    planet[5] -= 6.283

            galaxy.draw_system(lcd, self.systems[self.sel_idx], self.planets, self.sel_planet)
            return None

        if buttons.repeat("LEFT", 180, 120):
            self.sel_region = (self.sel_region - 1) % len(self.regions)
        if buttons.repeat("RIGHT", 180, 120):
            self.sel_region = (self.sel_region + 1) % len(self.regions)
        if buttons.pressed("A"):
            self.state = galaxy.STATE_SYSTEM

        galaxy.draw_planet(lcd, self.planets[self.sel_planet], self.regions, self.sel_region)
        return None
