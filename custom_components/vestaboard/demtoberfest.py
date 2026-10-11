"""Demtoberfest 2026 boards and the display sequence that plays them."""

from __future__ import annotations

from typing import Any

from .game_art import BOARD_COLS, BOARD_ROWS

ANIMATION_DIAGONAL_BLUE_WAVE = "diagonal-blue-wave"
# This house board is a white-background Vestaboard. Blue stays 67.
# The white flap is 70; 69 is the black flap on this model.
API_BLUE = 67
API_WHITE = 70
# Bits only spin forward, about 14 flaps a second (a full reel is ~5.2 s).
# With any strategy but classic, every bit spins through the reel, even
# unchanged ones, and the board does not show a new message until the last
# one lands. So the wave is two messages, all blue then all white, each with
# a native stagger, and each wait covers the stagger plus one bit's spin.
CASCADE_STRATEGY = "column"
CASCADE_STEP_SIZE = 1
CASCADE_STEP_INTERVAL_MS = 200
# Steps in the strategy: columns for "column". Use 27 for "diagonal".
CASCADE_STEPS = BOARD_COLS
# White -> blue under a strategy is a full turn plus a short hop (~6 s seen).
CASCADE_SPIN_SECONDS = 7.0
CASCADE_MARGIN_SECONDS = 3.0
# Classic reset to white first: only changed bits move, at most ~5 s.
CASCADE_SETTLE_SECONDS = 8.0
CASCADE_BLUE_HOLD_SECONDS = 2.0
HOLD_SECONDS = 15
REPEAT_SECONDS = 900
EVENT_VERSION = 4
SEQUENCE_VERSION = 5

ANNOUNCEMENT_ID = "demtoberfest-announcement"
WAVE_ID = "demtoberfest-blue-wave"
REELECT_ID = "demtoberfest-reelect"
PINBALL_ID = "demtoberfest-pinball"
INSTAGRAM_ID = "demtoberfest-instagram"
SEQUENCE_ID = "demtoberfest-2026"


def solid_board(code: int) -> list[list[int]]:
    """A full 6×22 board of one character code. Never uses blank (0)."""
    if code == 0:
        raise ValueError("Blank is not a cascade color")
    return [[code for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]


def transition_seconds() -> float:
    """How long one staggered full-board transition needs to land."""
    steps = -(-CASCADE_STEPS // CASCADE_STEP_SIZE)
    return (
        (steps - 1) * CASCADE_STEP_INTERVAL_MS / 1000
        + CASCADE_SPIN_SECONDS
        + CASCADE_MARGIN_SECONDS
    )


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
    """Store the all-blue midpoint. Playback is `_play_diagonal_cascade`."""
    preview = solid_board(API_BLUE)
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
        "15 seconds. The blue wave sweeps the board from white to blue and "
        "back with the board's own transition."
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
