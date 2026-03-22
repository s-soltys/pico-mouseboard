from lcd import LCD_0inch96, BLACK, CYAN, WHITE, YELLOW, GRAY, RED
from core.ui import center_x, fit_text


_SHARED_LCD = None
_LCD_INIT_ERROR = None


def get_lcd():
    global _SHARED_LCD, _LCD_INIT_ERROR
    if _SHARED_LCD is not None:
        return _SHARED_LCD
    if _LCD_INIT_ERROR is not None:
        raise _LCD_INIT_ERROR

    try:
        _SHARED_LCD = LCD_0inch96()
    except Exception as exc:
        _LCD_INIT_ERROR = exc
        raise
    return _SHARED_LCD


def _screen_lines(lines, max_lines=3):
    normalized = []
    for line in lines:
        if line is None:
            continue
        text = str(line)
        if not text:
            continue
        normalized.append(fit_text(text, 19))
    if len(normalized) > max_lines:
        normalized = normalized[-max_lines:]
    return normalized


def draw_text_screen(title, lines, *, title_color=RED, line_colors=(YELLOW, WHITE, GRAY), lcd=None):
    if lcd is None:
        lcd = get_lcd()

    lines = _screen_lines(lines)
    title = fit_text(title, 19)

    lcd.fill(BLACK)
    lcd.text("PICO", center_x("PICO"), 8, CYAN)
    lcd.text("MOUSEBOARD", center_x("MOUSEBOARD"), 22, WHITE)
    lcd.text(title, center_x(title), 36, title_color)

    y = 52
    for index, line in enumerate(lines):
        color = line_colors[index] if index < len(line_colors) else GRAY
        lcd.text(line, 4, y, color)
        y += 10

    lcd.display()
    return lcd


def show_fatal_error(exc, *, stage="runtime", detail="", log_lines=(), lcd=None):
    title = "boot error" if stage == "boot" else "runtime error"
    lines = []

    if detail:
        lines.append(detail)

    name = exc.__class__.__name__
    lines.append(name)

    message = str(exc)
    if message and message != name:
        lines.append(message)

    remaining = 3 - len(lines)
    if remaining > 0:
        for line in _screen_lines(log_lines, remaining):
            if line not in lines:
                lines.append(line)

    return draw_text_screen(title, lines[:3], title_color=RED, lcd=lcd)
