"""Demtoberfest 2026 boards and the display sequence that plays them."""

from __future__ import annotations

from typing import Any

from .game_art import BOARD_COLS, BOARD_ROWS, COLOR_BLUE, COLOR_WHITE

ANIMATION_DIAGONAL_BLUE_WAVE = "diagonal-blue-wave"
WAVE_SECONDS = 8
HOLD_SECONDS = 120
REPEAT_SECONDS = 900
EVENT_VERSION = 1
SEQUENCE_VERSION = 1

ANNOUNCEMENT_ID = "demtoberfest-announcement"
WAVE_ID = "demtoberfest-blue-wave"
REELECT_ID = "demtoberfest-reelect"
PINBALL_ID = "demtoberfest-pinball"
INSTAGRAM_ID = "demtoberfest-instagram"
SEQUENCE_ID = "demtoberfest-2026"


def build_diagonal_wave_frames() -> list[list[list[int]]]:
    """One frame per diagonal, step 0 through 26.

    On step ``d``, cell ``(x, y)`` is blue only when ``x + y == d``.
    Every other cell is white. Step 0 is only the top-left cell.
    Step 26 is only the bottom-right cell.
    """
    frames: list[list[list[int]]] = []
    for step in range(BOARD_COLS + BOARD_ROWS - 1):
        board = [[COLOR_WHITE for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        for y in range(BOARD_ROWS):
            for x in range(BOARD_COLS):
                if x + y == step:
                    board[y][x] = COLOR_BLUE
        frames.append(board)
    return frames


def _text(template: str, y: int) -> dict[str, Any]:
    return {
        "style": {
            "justify": "center",
            "align": "center",
            "height": 1,
            "width": BOARD_COLS,
            "absolutePosition": {"x": 0, "y": y},
        },
        "template": template,
    }


def _blue_corner(x: int, y: int) -> dict[str, Any]:
    return {
        "style": {
            "justify": "left",
            "align": "top",
            "height": 1,
            "width": 1,
            "absolutePosition": {"x": x, "y": y},
        },
        "template": "{67}",
    }


def _board(*components: dict[str, Any]) -> dict[str, Any]:
    return {"props": {}, "components": list(components)}


def _template(
    template_id: str,
    name: str,
    components: list[dict[str, Any]],
    *,
    animation: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": template_id,
        "name": name,
        "props": [],
        "vbml": _board(*components),
        "event_version": EVENT_VERSION,
        "updated_at": "1970-01-01T00:00:00+00:00",
    }
    if animation:
        item["animation"] = animation
    return item


def _wave_template() -> dict[str, Any]:
    """Store a middle frame for the editor. Playback builds every diagonal."""
    preview = build_diagonal_wave_frames()[13]
    return {
        "id": WAVE_ID,
        "name": "Blue wave",
        "props": [],
        "animation": ANIMATION_DIAGONAL_BLUE_WAVE,
        "event_version": EVENT_VERSION,
        "vbml": {
            "props": {},
            "components": [
                {
                    "style": {
                        "height": BOARD_ROWS,
                        "width": BOARD_COLS,
                        "absolutePosition": {"x": 0, "y": 0},
                    },
                    "rawCharacters": preview,
                }
            ],
        },
        "updated_at": "1970-01-01T00:00:00+00:00",
    }


DEMTOBERFEST_TEMPLATES: list[dict[str, Any]] = [
    _template(
        ANNOUNCEMENT_ID,
        "Announcement",
        [
            _blue_corner(0, 0),
            _blue_corner(BOARD_COLS - 1, 0),
            _text("DEMTOBERFEST", 2),
            _text("OCTOBER 11TH, 2026", 4),
            _blue_corner(0, BOARD_ROWS - 1),
            _blue_corner(BOARD_COLS - 1, BOARD_ROWS - 1),
        ],
    ),
    _wave_template(),
    _template(
        REELECT_ID,
        "Re-elect Jon Crowley and Alyson Forbes",
        [
            _text("RE-ELECT", 1),
            _text("JON CROWLEY", 3),
            _text("AND ALYSON FORBES", 4),
        ],
    ),
    _template(
        PINBALL_ID,
        "More pinball in the basement",
        [
            _text("MORE PINBALL IN", 0),
            _text("THE BASEMENT", 1),
            _text("WATCH YOUR HEAD", 3),
            _text("GOING DOWN THE STAIRS", 4),
        ],
    ),
    _template(
        INSTAGRAM_ID,
        "Follow @ahforward on Instagram",
        [
            _text("FOLLOW @AHFORWARD", 2),
            _text("ON INSTAGRAM", 3),
        ],
    ),
]

DEMTOBERFEST_SEQUENCE: dict[str, Any] = {
    "id": SEQUENCE_ID,
    "name": "Demtoberfest 2026",
    "description": (
        "House event for October 11, 2026. Message screens stay up for "
        "2 minutes. The blue wave plays through once."
    ),
    "sequence_version": SEQUENCE_VERSION,
    "repeat_seconds": REPEAT_SECONDS,
    "items": [
        {"template_id": ANNOUNCEMENT_ID, "duration": HOLD_SECONDS},
        {"template_id": WAVE_ID},
        {"template_id": REELECT_ID, "duration": HOLD_SECONDS},
        {"template_id": PINBALL_ID, "duration": HOLD_SECONDS},
        {"template_id": INSTAGRAM_ID, "duration": HOLD_SECONDS},
    ],
}
