from lcd import BLACK, WHITE, GRAY, CYAN, YELLOW, DKGRN, TEAL, SLATE
from core.controls import HOME_HINT


SCREEN_W = 160
SCREEN_H = 80
HEADER_H = 10
FOOTER_H = 10


def fit_text(text, max_chars):
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    return text[:max_chars - 1] + "."


def center_x(text, width=SCREEN_W):
    return max(0, (width - len(text) * 8) // 2)


def draw_header(lcd, title, detail="", color=CYAN):
    lcd.fill_rect(0, 0, SCREEN_W, HEADER_H, BLACK)
    lcd.hline(0, HEADER_H - 1, SCREEN_W, color)
    lcd.text(fit_text(title, 12), 2, 1, color)
    if detail:
        detail = fit_text(detail, 6)
        lcd.text(detail, SCREEN_W - (len(detail) * 8) - 2, 1, WHITE)


def draw_footer(lcd, text, color=GRAY):
    lcd.fill_rect(0, SCREEN_H - FOOTER_H, SCREEN_W, FOOTER_H, BLACK)
    lcd.hline(0, SCREEN_H - FOOTER_H, SCREEN_W, color)
    lcd.text(fit_text(text, 19), 2, SCREEN_H - FOOTER_H + 1, color)


def draw_tile(lcd, x, y, w, h, title, selected, accent, icon_fn, monochrome=False):
    if monochrome:
        border = WHITE
        fill = WHITE if selected else BLACK
        text_color = BLACK if selected else WHITE
    else:
        border = YELLOW if selected else GRAY
        fill = SLATE if selected else DKGRN
        text_color = accent if selected else WHITE
    lcd.fill_rect(x, y, w, h, fill)
    lcd.rect(x, y, w, h, border)
    icon_fn(lcd, x + w // 2, y + 9, selected, monochrome)
    lcd.text(fit_text(title, max(4, (w // 8) - 1)), x + 3, y + h - 10, text_color)


def draw_empty_state(lcd, title, lines, accent=TEAL, footer=HOME_HINT):
    lcd.fill(BLACK)
    draw_header(lcd, title, color=accent)
    y = 18
    for line in lines:
        lcd.text(fit_text(line, 19), 4, y, WHITE)
        y += 12
    draw_footer(lcd, footer)
