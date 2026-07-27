"""Pixel-art intro boards and per-game score layouts for Stern templates."""

from __future__ import annotations

from typing import Any, Callable

# Vestaboard color codes (63–70)
COLOR_RED = 63
COLOR_ORANGE = 64
COLOR_YELLOW = 65
COLOR_GREEN = 66
COLOR_BLUE = 67
COLOR_VIOLET = 68
COLOR_WHITE = 69
COLOR_BLACK = 70

BOARD_ROWS = 6
BOARD_COLS = 22
BOARD_CELLS = BOARD_ROWS * BOARD_COLS
MIN_COLORED_CELLS = int(BOARD_CELLS * 0.8)  # 105 of 132


def _blank() -> list[list[int]]:
    return [[0] * BOARD_COLS for _ in range(BOARD_ROWS)]


def _set(board: list[list[int]], x: int, y: int, color: int) -> None:
    if 0 <= y < BOARD_ROWS and 0 <= x < BOARD_COLS:
        board[y][x] = color


def _fill_rect(
    board: list[list[int]], x0: int, y0: int, w: int, h: int, color: int
) -> None:
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            _set(board, x, y, color)


def _fill_row(board: list[list[int]], y: int, color: int, x0: int = 0, x1: int = BOARD_COLS) -> None:
    for x in range(x0, x1):
        _set(board, x, y, color)


def _token(color: int) -> str:
    return "{" + str(color) + "}"


def _bar(accent: int, width: int = BOARD_COLS) -> str:
    return _token(accent) * width


def _count_colored(board: list[list[int]]) -> int:
    return sum(1 for row in board for cell in row if cell != 0)


def _intro_vbml(raw: list[list[int]]) -> dict[str, Any]:
    """Wrap a finished board; reveal frames are built at send time."""
    return {
        "props": {},
        "raw": raw,
        "strategy": "column",
        "components": [
            {
                "style": {
                    "height": BOARD_ROWS,
                    "width": BOARD_COLS,
                    "absolutePosition": {"x": 0, "y": 0},
                },
                "rawCharacters": raw,
            }
        ],
    }


def build_reveal_frames(
    final: list[list[int]], frame_count: int = 18
) -> list[list[list[int]]]:
    """Build TL→BR scan-order reveal frames (top-left flips first)."""
    cells = [(y, x, final[y][x]) for y in range(BOARD_ROWS) for x in range(BOARD_COLS)]
    frames: list[list[list[int]]] = []
    board = _blank()
    chunk = max(1, len(cells) // frame_count)
    for index, (y, x, color) in enumerate(cells):
        board[y][x] = color
        if (index + 1) % chunk == 0 or index == len(cells) - 1:
            frames.append([row[:] for row in board])
    return frames


# ---------------------------------------------------------------------------
# Intro art — dense, 2+ colors, recognizable (≥80% filled)
# ---------------------------------------------------------------------------


def icon_sword() -> list[list[int]]:
    """D&D — glowing sword on gold cave wall."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, BOARD_ROWS, COLOR_ORANGE)
    # stone texture stripes
    for y in range(BOARD_ROWS):
        for x in range(0, BOARD_COLS, 3):
            if (x + y) % 2 == 0:
                _set(b, x, y, COLOR_YELLOW)
    # large vertical blade (white + yellow edge)
    for y in range(BOARD_ROWS):
        _set(b, 10, y, COLOR_WHITE)
        _set(b, 11, y, COLOR_WHITE)
        _set(b, 9, y, COLOR_YELLOW)
        _set(b, 12, y, COLOR_YELLOW)
    # crossguard
    _fill_row(b, 4, COLOR_YELLOW, 6, 16)
    _fill_row(b, 5, COLOR_YELLOW, 8, 14)
    return b


def icon_bat() -> list[list[int]]:
    """Elvira — bat on blood-red sky."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, BOARD_ROWS, COLOR_RED)
    # moon
    _fill_rect(b, 16, 0, 5, 2, COLOR_WHITE)
    # bat wings (black on red)
    for y in range(1, 5):
        for x in range(1, 10):
            if abs((x - 5) + (y - 2)) < 4:
                _set(b, x, y, COLOR_BLACK)
        for x in range(12, 21):
            if abs((x - 16) + (y - 2)) < 4:
                _set(b, x, y, COLOR_BLACK)
    # body
    _fill_rect(b, 9, 1, 4, 3, COLOR_BLACK)
    _fill_rect(b, 10, 0, 2, 1, COLOR_BLACK)
    # eyes
    _set(b, 10, 2, COLOR_WHITE)
    _set(b, 11, 2, COLOR_WHITE)
    return b


def icon_claws() -> list[list[int]]:
    """Godzilla — city skyline + claw slashes."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, 3, COLOR_BLUE)
    _fill_rect(b, 0, 3, BOARD_COLS, 3, COLOR_GREEN)
    # buildings
    for x in range(0, BOARD_COLS, 4):
        h = 2 + (x % 3)
        _fill_rect(b, x, 3 - h, 3, h, COLOR_BLACK)
    # three claw marks (orange on green)
    for offset in (3, 10, 17):
        for y in range(BOARD_ROWS):
            _set(b, offset + y // 2, y, COLOR_ORANGE)
            _set(b, offset + y // 2 + 1, y, COLOR_ORANGE)
            _set(b, offset + y // 2 + 2, y, COLOR_YELLOW)
    return b


def icon_shark_fin() -> list[list[int]]:
    """Jaws — ocean with large fin and teeth row."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, BOARD_ROWS, COLOR_BLUE)
    # lighter wave bands
    for y in (1, 3, 5):
        _fill_row(b, y, COLOR_WHITE, 0, BOARD_COLS)
        for x in range(0, BOARD_COLS, 2):
            _set(b, x, y, COLOR_BLUE)
    # fin
    for x in range(8, 15):
        _set(b, x, 0, COLOR_WHITE)
    for x in range(7, 16):
        _set(b, x, 1, COLOR_WHITE)
    for x in range(6, 17):
        _set(b, x, 2, COLOR_WHITE)
    # teeth at waterline
    for x in range(2, BOARD_COLS - 2, 2):
        _set(b, x, 4, COLOR_WHITE)
    return b


def icon_pistol() -> list[list[int]]:
    """John Wick — bold pistol silhouette on white target rings."""
    b = _blank()
    # concentric target (red/white)
    for y in range(BOARD_ROWS):
        for x in range(BOARD_COLS):
            dist = abs(x - 11) + abs(y - 3)
            b[y][x] = COLOR_RED if dist % 3 == 0 else COLOR_WHITE
    # pistol black
    _fill_rect(b, 4, 2, 12, 2, COLOR_BLACK)
    _fill_rect(b, 6, 4, 4, 2, COLOR_BLACK)
    _fill_rect(b, 5, 3, 2, 1, COLOR_BLACK)
    _set(b, 16, 2, COLOR_BLACK)
    _set(b, 16, 3, COLOR_BLACK)
    return b


def icon_footprint() -> list[list[int]]:
    """Jurassic Park — amber field + large raptor footprint."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, BOARD_ROWS, COLOR_ORANGE)
    for y in range(BOARD_ROWS):
        for x in range(BOARD_COLS):
            if (x + y) % 4 == 0:
                _set(b, x, y, COLOR_YELLOW)
    # footprint (black)
    _fill_rect(b, 8, 3, 6, 3, COLOR_BLACK)
    for x in (5, 6, 7):
        _set(b, x, 1, COLOR_BLACK)
        _set(b, x, 2, COLOR_BLACK)
    for x in (10, 11, 12):
        _set(b, x, 0, COLOR_BLACK)
        _set(b, x, 1, COLOR_BLACK)
    for x in (14, 15, 16):
        _set(b, x, 1, COLOR_BLACK)
        _set(b, x, 2, COLOR_BLACK)
    return b


def icon_bolt() -> list[list[int]]:
    """Pokemon — electric bolt on dark sky."""
    b = _blank()
    _fill_rect(b, 0, 0, BOARD_COLS, BOARD_ROWS, COLOR_VIOLET)
    for y in range(BOARD_ROWS):
        for x in range(0, BOARD_COLS, 5):
            _set(b, x, y, COLOR_BLUE)
    # large lightning bolt (yellow + white core)
    bolt = [
        (13, 0), (14, 0), (12, 1), (13, 1), (11, 2), (12, 2),
        (10, 3), (11, 3), (12, 3), (13, 3), (9, 4), (10, 4),
        (11, 4), (12, 4), (8, 5), (9, 5), (10, 5), (11, 5),
        (7, 0), (8, 1), (9, 2), (8, 3), (7, 4),
    ]
    for x, y in bolt:
        _set(b, x, y, COLOR_YELLOW)
        _set(b, x + 1, y, COLOR_WHITE)
    return b


def icon_x() -> list[list[int]]:
    """X-Men — bold X on yellow danger stripes."""
    b = _blank()
    for y in range(BOARD_ROWS):
        for x in range(BOARD_COLS):
            b[y][x] = COLOR_YELLOW if (x // 3) % 2 == 0 else COLOR_BLACK
    # large X (violet + white)
    for i in range(BOARD_ROWS):
        _set(b, 3 + i, i, COLOR_VIOLET)
        _set(b, 4 + i, i, COLOR_WHITE)
        _set(b, 17 - i, i, COLOR_VIOLET)
        _set(b, 18 - i, i, COLOR_WHITE)
    return b


# ---------------------------------------------------------------------------
# Score layouts — game name, player, score only (no TOP SCORE labels)
# ---------------------------------------------------------------------------


def _comp(
    template: str,
    *,
    x: int,
    y: int,
    width: int,
    height: int = 1,
    justify: str = "center",
    align: str = "top",
) -> dict[str, Any]:
    return {
        "style": {
            "justify": justify,
            "align": align,
            "height": height,
            "width": width,
            "absolutePosition": {"x": x, "y": y},
        },
        "template": template,
    }


def _accent_line(accent: int, y: int, x: int = 0, width: int = BOARD_COLS) -> dict[str, Any]:
    return _comp(_bar(accent, width), x=x, y=y, width=width, justify="left")


def layout_dnd(title: str, accent: int) -> list[dict[str, Any]]:
    """Centered title stack, gold corner dots, player then score."""
    return [
        _comp(_token(COLOR_BLACK), x=0, y=0, width=1, height=1, justify="left"),
        _comp(_token(accent), x=21, y=0, width=1, height=1, justify="left"),
        _comp(title, x=0, y=1, width=BOARD_COLS, height=2),
        _accent_line(accent, 3),
        _comp("{{player}}", x=0, y=3, width=BOARD_COLS),
        _comp("{{score}}", x=1, y=4, width=20),
        _comp(_token(accent), x=0, y=5, width=1, height=1, justify="left"),
        _comp(_token(COLOR_BLACK), x=21, y=5, width=1, height=1, justify="left"),
    ]


def layout_elvira(title: str, accent: int) -> list[dict[str, Any]]:
    """Title left column; player and score on the right."""
    return [
        _accent_line(accent, 0),
        _comp(title, x=0, y=1, width=11, height=4, justify="left", align="center"),
        _comp(_token(accent), x=11, y=1, width=1, height=4, justify="left"),
        _comp("{{player}}", x=12, y=1, width=10, justify="right"),
        _accent_line(COLOR_BLACK, 3, x=12, width=10),
        _comp("{{score}}", x=12, y=4, width=10, justify="right"),
        _accent_line(accent, 5),
    ]


def layout_godzilla(title: str, accent: int) -> list[dict[str, Any]]:
    """GODZILLA / player / score — three centered rows."""
    return [
        _accent_line(accent, 0),
        _comp(title.replace("\n", " "), x=0, y=1, width=BOARD_COLS),
        _comp("{{player}}", x=0, y=3, width=BOARD_COLS),
        _accent_line(COLOR_GREEN, 4),
        _comp("{{score}}", x=0, y=5, width=BOARD_COLS),
    ]


def layout_jaws(title: str, accent: int) -> list[dict[str, Any]]:
    """Title top; player center; score lower-right."""
    return [
        _comp(title.replace("\n", " "), x=0, y=0, width=BOARD_COLS),
        _accent_line(accent, 1),
        _accent_line(COLOR_WHITE, 2),
        _comp("{{player}}", x=0, y=3, width=BOARD_COLS),
        _comp("{{score}}", x=10, y=5, width=12, justify="right"),
    ]


def layout_john_wick(title: str, accent: int) -> list[dict[str, Any]]:
    """Title + underline; player centered; score bottom-right."""
    return [
        _comp(title.replace("\n", " "), x=0, y=0, width=BOARD_COLS),
        _accent_line(accent, 1),
        _comp("{{player}}", x=0, y=2, width=BOARD_COLS, height=2, align="center"),
        _comp(_token(COLOR_BLACK), x=0, y=4, width=8, justify="left"),
        _comp("{{score}}", x=8, y=4, width=14, justify="right"),
        _accent_line(accent, 5),
    ]


def layout_jurassic(title: str, accent: int) -> list[dict[str, Any]]:
    """JURASSIC / PARK stacked left; player upper-right; score lower-right."""
    return [
        _comp("JURASSIC", x=0, y=0, width=12, justify="left"),
        _comp("PARK", x=0, y=1, width=12, justify="left"),
        _accent_line(accent, 2, x=0, width=12),
        _comp("{{player}}", x=12, y=0, width=10, justify="right"),
        _comp("{{score}}", x=12, y=4, width=10, justify="right"),
        _accent_line(accent, 5),
    ]


def layout_pokemon(title: str, accent: int) -> list[dict[str, Any]]:
    """Title with bolt stripe; player left, score right."""
    return [
        _comp(title.replace("\n", " "), x=0, y=0, width=14, justify="left"),
        _comp(_token(accent) * 8, x=14, y=0, width=8, justify="left"),
        _accent_line(COLOR_VIOLET, 1),
        _comp("{{player}}", x=0, y=2, width=11, justify="left"),
        _comp(_token(accent), x=11, y=2, width=1, height=3, justify="left"),
        _comp("{{score}}", x=12, y=3, width=10, justify="right"),
        _accent_line(accent, 5),
    ]


def layout_xmen(title: str, accent: int) -> list[dict[str, Any]]:
    """THE / UNCANNY / X-MEN left; player top-right; score lower-right."""
    return [
        _comp("THE", x=0, y=0, width=10, justify="left"),
        _comp("UNCANNY", x=0, y=1, width=10, justify="left"),
        _comp("X-MEN", x=0, y=2, width=10, justify="left"),
        _accent_line(accent, 3, x=0, width=10),
        _comp("{{player}}", x=11, y=0, width=11, justify="right"),
        _comp("{{score}}", x=11, y=4, width=11, justify="right"),
        _comp(_token(accent), x=10, y=0, width=1, height=6, justify="left"),
    ]


LAYOUT_DND = "dnd"
LAYOUT_ELVIRA = "elvira"
LAYOUT_GODZILLA = "godzilla"
LAYOUT_JAWS = "jaws"
LAYOUT_JOHN_WICK = "john_wick"
LAYOUT_JURASSIC = "jurassic"
LAYOUT_POKEMON = "pokemon"
LAYOUT_XMEN = "xmen"

LAYOUT_BUILDERS: dict[str, Callable[[str, int], list[dict[str, Any]]]] = {
    LAYOUT_DND: layout_dnd,
    LAYOUT_ELVIRA: layout_elvira,
    LAYOUT_GODZILLA: layout_godzilla,
    LAYOUT_JAWS: layout_jaws,
    LAYOUT_JOHN_WICK: layout_john_wick,
    LAYOUT_JURASSIC: layout_jurassic,
    LAYOUT_POKEMON: layout_pokemon,
    LAYOUT_XMEN: layout_xmen,
}

INTRO_BUILDERS: dict[str, Callable[[], list[list[int]]]] = {
    LAYOUT_DND: icon_sword,
    LAYOUT_ELVIRA: icon_bat,
    LAYOUT_GODZILLA: icon_claws,
    LAYOUT_JAWS: icon_shark_fin,
    LAYOUT_JOHN_WICK: icon_pistol,
    LAYOUT_JURASSIC: icon_footprint,
    LAYOUT_POKEMON: icon_bolt,
    LAYOUT_XMEN: icon_x,
}
