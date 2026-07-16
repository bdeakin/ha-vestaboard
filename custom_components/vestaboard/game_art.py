"""Pixel-art intro boards and layout builders for Stern game templates."""

from __future__ import annotations

from typing import Any

# Vestaboard color codes
COLOR_RED = 63
COLOR_ORANGE = 64
COLOR_YELLOW = 65
COLOR_GREEN = 66
COLOR_BLUE = 67
COLOR_VIOLET = 68
COLOR_WHITE = 69
COLOR_BLACK = 70


def _blank() -> list[list[int]]:
    return [[0] * 22 for _ in range(6)]


def _set(board: list[list[int]], x: int, y: int, color: int) -> None:
    if 0 <= y < 6 and 0 <= x < 22:
        board[y][x] = color


def _fill_row(board: list[list[int]], y: int, color: int, x0: int = 0, x1: int = 22) -> None:
    for x in range(x0, x1):
        _set(board, x, y, color)


def _token(color: int) -> str:
    return "{" + str(color) + "}"


def _corner_accents(accent: int) -> list[dict[str, Any]]:
    """Black UL / accent UR / accent BL / black BR corner dots."""
    black = _token(COLOR_BLACK)
    acc = _token(accent)
    return [
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": black,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 21, "y": 0},
            },
            "template": acc,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 0, "y": 5},
            },
            "template": acc,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 21, "y": 5},
            },
            "template": black,
        },
    ]


def _intro_vbml(raw: list[list[int]]) -> dict[str, Any]:
    return {
        "props": {},
        "components": [
            {
                "style": {
                    "height": 6,
                    "width": 22,
                    "absolutePosition": {"x": 0, "y": 0},
                },
                "rawCharacters": raw,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Intro icons (6x22 pixel art)
# ---------------------------------------------------------------------------


def icon_sword() -> list[list[int]]:
    """Dungeons & Dragons — vertical sword."""
    b = _blank()
    cx = 10
    # blade tip + shaft
    _set(b, cx, 0, COLOR_WHITE)
    for y in (1, 2, 3):
        _set(b, cx, y, COLOR_WHITE)
        _set(b, cx + 1, y, COLOR_WHITE)
    # crossguard
    for x in range(cx - 3, cx + 5):
        _set(b, x, 4, COLOR_YELLOW)
    # pommel
    _set(b, cx, 5, COLOR_YELLOW)
    _set(b, cx + 1, 5, COLOR_YELLOW)
    return b


def icon_bat() -> list[list[int]]:
    """Elvira — bat silhouette."""
    b = _blank()
    # wings
    for x in range(2, 9):
        _set(b, x, 2, COLOR_RED)
        _set(b, x, 3, COLOR_RED)
    for x in range(13, 20):
        _set(b, x, 2, COLOR_RED)
        _set(b, x, 3, COLOR_RED)
    # body / head
    for x in range(9, 13):
        _set(b, x, 1, COLOR_RED)
        _set(b, x, 2, COLOR_RED)
        _set(b, x, 3, COLOR_RED)
    _set(b, 10, 0, COLOR_RED)
    _set(b, 11, 0, COLOR_RED)
    # wing tips lower
    _set(b, 3, 4, COLOR_RED)
    _set(b, 4, 4, COLOR_RED)
    _set(b, 17, 4, COLOR_RED)
    _set(b, 18, 4, COLOR_RED)
    return b


def icon_claws() -> list[list[int]]:
    """Godzilla — three claw slash marks."""
    b = _blank()
    for i, x0 in enumerate((4, 9, 14)):
        for y in range(6):
            _set(b, x0 + y // 2, y, COLOR_GREEN)
            _set(b, x0 + y // 2 + 1, y, COLOR_GREEN)
    return b


def icon_shark_fin() -> list[list[int]]:
    """Jaws — shark fin above water."""
    b = _blank()
    # water line
    _fill_row(b, 4, COLOR_BLUE)
    _fill_row(b, 5, COLOR_BLUE)
    # fin
    _set(b, 11, 0, COLOR_WHITE)
    for x in range(10, 13):
        _set(b, x, 1, COLOR_WHITE)
    for x in range(9, 14):
        _set(b, x, 2, COLOR_WHITE)
    for x in range(8, 15):
        _set(b, x, 3, COLOR_WHITE)
    return b


def icon_pistol() -> list[list[int]]:
    """John Wick — side-view pistol."""
    b = _blank()
    # barrel + slide
    for x in range(5, 16):
        _set(b, x, 1, COLOR_WHITE)
        _set(b, x, 2, COLOR_WHITE)
    # muzzle
    _set(b, 16, 1, COLOR_WHITE)
    _set(b, 16, 2, COLOR_WHITE)
    # grip
    for y in range(2, 6):
        _set(b, 6, y, COLOR_WHITE)
        _set(b, 7, y, COLOR_WHITE)
        _set(b, 8, y, COLOR_WHITE)
    # trigger guard hint
    _set(b, 9, 3, COLOR_WHITE)
    return b


def icon_footprint() -> list[list[int]]:
    """Jurassic Park — dinosaur footprint."""
    b = _blank()
    # heel pad
    for y in range(3, 6):
        for x in range(8, 14):
            _set(b, x, y, COLOR_ORANGE)
    # three toes
    for x in (6, 7, 8):
        _set(b, x, 1, COLOR_ORANGE)
        _set(b, x, 2, COLOR_ORANGE)
    for x in (10, 11, 12):
        _set(b, x, 0, COLOR_ORANGE)
        _set(b, x, 1, COLOR_ORANGE)
    for x in (14, 15, 16):
        _set(b, x, 1, COLOR_ORANGE)
        _set(b, x, 2, COLOR_ORANGE)
    return b


def icon_bolt() -> list[list[int]]:
    """Pokemon — lightning bolt."""
    b = _blank()
    # zigzag bolt centered
    coords = [
        (12, 0),
        (13, 0),
        (11, 1),
        (12, 1),
        (10, 2),
        (11, 2),
        (9, 3),
        (10, 3),
        (11, 3),
        (12, 3),
        (13, 3),
        (11, 4),
        (12, 4),
        (10, 5),
        (11, 5),
    ]
    for x, y in coords:
        _set(b, x, y, COLOR_YELLOW)
    return b


def icon_x() -> list[list[int]]:
    """X-Men — large X."""
    b = _blank()
    for i in range(6):
        _set(b, 7 + i, i, COLOR_VIOLET)
        _set(b, 8 + i, i, COLOR_VIOLET)
        _set(b, 14 - i, i, COLOR_VIOLET)
        _set(b, 15 - i, i, COLOR_VIOLET)
    return b


# ---------------------------------------------------------------------------
# Varied score layouts (always: game → player → score, TTB or LTR)
# ---------------------------------------------------------------------------


def layout_stack_classic(title: str, accent: int) -> list[dict[str, Any]]:
    """Top-to-bottom: title, player, TOP SCORE, score + corner dots."""
    return [
        *_corner_accents(accent),
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 2,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 1},
            },
            "template": title,
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 3},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 4},
            },
            "template": "TOP SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 20,
                "absolutePosition": {"x": 1, "y": 5},
            },
            "template": "{{score}}",
        },
    ]


def layout_accent_banner(title: str, accent: int) -> list[dict[str, Any]]:
    """Accent bar under title, then player, then score."""
    bar = _token(accent) * 22
    return [
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 2,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": title,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 2},
            },
            "template": bar,
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 3},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 4},
            },
            "template": "TOP SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 5},
            },
            "template": "{{score}}",
        },
    ]


def layout_title_left(title: str, accent: int) -> list[dict[str, Any]]:
    """Left-to-right: title column, then player / score column."""
    return [
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "center",
                "align": "center",
                "height": 6,
                "width": 10,
                "absolutePosition": {"x": 1, "y": 0},
            },
            "template": title,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 11, "y": 0},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 1},
            },
            "template": "PLAYER",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 2},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 4},
            },
            "template": "SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 5},
            },
            "template": "{{score}}",
        },
    ]


def layout_labeled_rows(title: str, accent: int) -> list[dict[str, Any]]:
    """Top-to-bottom labeled rows: GAME / PLAYER / SCORE."""
    return [
        *_corner_accents(accent),
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 6,
                "absolutePosition": {"x": 1, "y": 1},
            },
            "template": "GAME",
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 14,
                "absolutePosition": {"x": 7, "y": 1},
            },
            "template": title.replace("\n", " "),
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 6,
                "absolutePosition": {"x": 1, "y": 3},
            },
            "template": "PLAYER",
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 14,
                "absolutePosition": {"x": 7, "y": 3},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 6,
                "absolutePosition": {"x": 1, "y": 5},
            },
            "template": "SCORE",
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 14,
                "absolutePosition": {"x": 7, "y": 5},
            },
            "template": "{{score}}",
        },
    ]


def layout_score_focus(title: str, accent: int) -> list[dict[str, Any]]:
    """Title top, player, then score emphasized on bottom two rows."""
    return [
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": title.replace("\n", " "),
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 1},
            },
            "template": _token(accent) * 22,
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 2},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 3},
            },
            "template": "TOP SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 2,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 4},
            },
            "template": "{{score}}",
        },
    ]


def layout_player_focus(title: str, accent: int) -> list[dict[str, Any]]:
    """Title, large centered player, score on bottom with corner accents."""
    return [
        *_corner_accents(accent),
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 20,
                "absolutePosition": {"x": 1, "y": 1},
            },
            "template": title.replace("\n", " "),
        },
        {
            "style": {
                "justify": "center",
                "align": "center",
                "height": 2,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 2},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 20,
                "absolutePosition": {"x": 1, "y": 4},
            },
            "template": "TOP SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 20,
                "absolutePosition": {"x": 1, "y": 5},
            },
            "template": "{{score}}",
        },
    ]


def layout_split_panels(title: str, accent: int) -> list[dict[str, Any]]:
    """Title across top; player left panel, score right panel."""
    return [
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 2,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": title,
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 10, "y": 2},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 10, "y": 3},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 10, "y": 4},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 1,
                "absolutePosition": {"x": 10, "y": 5},
            },
            "template": _token(accent),
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 0, "y": 3},
            },
            "template": "PLAYER",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 0, "y": 4},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 3},
            },
            "template": "SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 10,
                "absolutePosition": {"x": 12, "y": 4},
            },
            "template": "{{score}}",
        },
    ]


def layout_frame_bars(title: str, accent: int) -> list[dict[str, Any]]:
    """Accent bars framing title → player → TOP SCORE → score."""
    return [
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 0},
            },
            "template": _token(accent) * 22,
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 1},
            },
            "template": title.replace("\n", " "),
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 2},
            },
            "template": "{{player}}",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 3},
            },
            "template": "TOP SCORE",
        },
        {
            "style": {
                "justify": "center",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 4},
            },
            "template": "{{score}}",
        },
        {
            "style": {
                "justify": "left",
                "align": "top",
                "height": 1,
                "width": 22,
                "absolutePosition": {"x": 0, "y": 5},
            },
            "template": _token(accent) * 22,
        },
    ]


LAYOUT_STACK = "stack_classic"
LAYOUT_BANNER = "accent_banner"
LAYOUT_TITLE_LEFT = "title_left"
LAYOUT_LABELED = "labeled_rows"
LAYOUT_SCORE_FOCUS = "score_focus"
LAYOUT_PLAYER_FOCUS = "player_focus"
LAYOUT_SPLIT = "split_panels"
LAYOUT_FRAME = "frame_bars"

LAYOUT_BUILDERS = {
    LAYOUT_STACK: layout_stack_classic,
    LAYOUT_BANNER: layout_accent_banner,
    LAYOUT_TITLE_LEFT: layout_title_left,
    LAYOUT_LABELED: layout_labeled_rows,
    LAYOUT_SCORE_FOCUS: layout_score_focus,
    LAYOUT_PLAYER_FOCUS: layout_player_focus,
    LAYOUT_SPLIT: layout_split_panels,
    LAYOUT_FRAME: layout_frame_bars,
}