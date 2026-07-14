"""Persistent named VBML templates for Vestaboard-x."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_templates"
DATA_STORE = "template_store"

# Vestaboard color codes: 63 red, 64 orange, 65 yellow, 66 green, 67 blue, 68 violet, 69 white, 70 black
COLOR_RED = 63
COLOR_ORANGE = 64
COLOR_YELLOW = 65
COLOR_GREEN = 66
COLOR_BLUE = 67
COLOR_VIOLET = 68
COLOR_WHITE = 69
COLOR_BLACK = 70


def _score_k_template(entity_id: str) -> str:
    return (
        "{{ '{:,.0f}K'.format((states('"
        + entity_id
        + "') | float(0) / 1000)) }}"
    )


def _rainbow_border_raw() -> list[list[int]]:
    """Wrap-around rainbow frame matching Vestaboard's welcome-board style.

    Colors progress linearly around the perimeter, starting and ending at the
    bottom-left corner (violet → red → orange → yellow → green → blue → violet).
    """
    red, orange, yellow = COLOR_RED, COLOR_ORANGE, COLOR_YELLOW
    green, blue, violet = COLOR_GREEN, COLOR_BLUE, COLOR_VIOLET
    board = [[0] * 22 for _ in range(6)]
    # Top: red → orange → yellow
    board[0] = [red] * 6 + [orange] * 9 + [yellow] * 7
    # Bottom (LTR): violet → blue → green  (clockwise ends returning to BL)
    board[5] = [violet] * 7 + [blue] * 8 + [green] * 7
    # Sides (corners already set by top/bottom rows)
    for y in (1, 2):
        board[y][0] = red
        board[y][21] = yellow
    for y in (3, 4):
        board[y][0] = violet
        board[y][21] = green
    return board


def _high_scores_intro_template() -> dict[str, Any]:
    """Rainbow intro: NOW DISPLAYING HIGH SCORES FOR {{location}}."""
    location_entity = "sensor.2026_leaderboard_location"
    return {
        "id": "high-scores-intro",
        "name": "High Scores Intro",
        "props": [
            {
                "name": "location",
                "entity_id": location_entity,
            },
        ],
        "vbml": {
            "props": {},
            "components": [
                {
                    "style": {
                        "height": 6,
                        "width": 22,
                        "absolutePosition": {"x": 0, "y": 0},
                    },
                    "rawCharacters": _rainbow_border_raw(),
                },
                {
                    "style": {
                        "justify": "center",
                        "align": "top",
                        "height": 3,
                        "width": 20,
                        "absolutePosition": {"x": 1, "y": 2},
                    },
                    "template": "NOW DISPLAYING\nHIGH SCORES FOR\n{{location}}",
                },
            ],
        },
        "updated_at": "1970-01-01T00:00:00+00:00",
    }


def _game_template(
    *,
    template_id: str,
    name: str,
    title: str,
    player_entity: str,
    score_entity: str,
    accent: int,
) -> dict[str, Any]:
    """Build a corner-dot single-game template."""
    accent_token = "{" + str(accent) + "}"
    black_token = "{" + str(COLOR_BLACK) + "}"
    return {
        "id": template_id,
        "name": name,
        "props": [
            {
                "name": "player",
                "entity_id": player_entity,
            },
            {
                "name": "score",
                "entity_id": score_entity,
                "template": _score_k_template(score_entity),
            },
        ],
        "vbml": {
            "props": {},
            "components": [
                {
                    "style": {
                        "justify": "left",
                        "align": "top",
                        "height": 1,
                        "width": 1,
                        "absolutePosition": {"x": 0, "y": 0},
                    },
                    "template": black_token,
                },
                {
                    "style": {
                        "justify": "left",
                        "align": "top",
                        "height": 1,
                        "width": 1,
                        "absolutePosition": {"x": 21, "y": 0},
                    },
                    "template": accent_token,
                },
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
                        "width": 20,
                        "absolutePosition": {"x": 1, "y": 5},
                    },
                    "template": "TOP SCORE {{score}}",
                },
                {
                    "style": {
                        "justify": "left",
                        "align": "top",
                        "height": 1,
                        "width": 1,
                        "absolutePosition": {"x": 0, "y": 5},
                    },
                    "template": accent_token,
                },
                {
                    "style": {
                        "justify": "left",
                        "align": "top",
                        "height": 1,
                        "width": 1,
                        "absolutePosition": {"x": 21, "y": 5},
                    },
                    "template": black_token,
                },
            ],
        },
        "updated_at": "1970-01-01T00:00:00+00:00",
    }


DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    _high_scores_intro_template(),
    _game_template(
        template_id="dungeons-dragons",
        name="Dungeons & Dragons",
        title="DUNGEONS &\nDRAGONS",
        player_entity="sensor.2026_leaderboard_dungeons_dragons_top_player",
        score_entity="sensor.2026_leaderboard_dungeons_dragons_top_score",
        accent=COLOR_YELLOW,
    ),
    _game_template(
        template_id="elvira-house-of-horrors",
        name="Elvira's House of Horrors",
        title="ELVIRA'S HOUSE\nOF HORRORS",
        player_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_player",
        score_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score",
        accent=COLOR_RED,
    ),
    _game_template(
        template_id="godzilla",
        name="Godzilla",
        title="GODZILLA",
        player_entity="sensor.2026_leaderboard_godzilla_top_player",
        score_entity="sensor.2026_leaderboard_godzilla_top_score",
        accent=COLOR_GREEN,
    ),
    _game_template(
        template_id="jaws",
        name="Jaws",
        title="JAWS",
        player_entity="sensor.2026_leaderboard_jaws_top_player",
        score_entity="sensor.2026_leaderboard_jaws_top_score",
        accent=COLOR_BLUE,
    ),
    _game_template(
        template_id="john-wick",
        name="John Wick",
        title="JOHN WICK",
        player_entity="sensor.2026_leaderboard_john_wick_top_player",
        score_entity="sensor.2026_leaderboard_john_wick_top_score",
        accent=COLOR_WHITE,
    ),
    _game_template(
        template_id="jurassic-park",
        name="Jurassic Park",
        title="JURASSIC PARK",
        player_entity="sensor.2026_leaderboard_jurassic_park_top_player",
        score_entity="sensor.2026_leaderboard_jurassic_park_top_score",
        accent=COLOR_ORANGE,
    ),
    _game_template(
        template_id="pokemon",
        name="Pokemon",
        title="POKEMON",
        player_entity="sensor.2026_leaderboard_pokemon_top_player",
        score_entity="sensor.2026_leaderboard_pokemon_top_score",
        accent=COLOR_YELLOW,
    ),
    _game_template(
        template_id="uncanny-x-men",
        name="The Uncanny X-Men",
        title="THE UNCANNY\nX-MEN",
        player_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_player",
        score_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_score",
        accent=COLOR_VIOLET,
    ),
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def async_get_store(hass: HomeAssistant) -> Store:
    """Return the singleton Store for templates."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if DATA_STORE not in domain_data:
        domain_data[DATA_STORE] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    return domain_data[DATA_STORE]


def _is_legacy_elvira_bars(vbml: Any) -> bool:
    """Return True if VBML still uses the old full red / zebra bars."""
    try:
        dumped = str(vbml)
    except Exception:  # noqa: BLE001
        return False
    return ("{63}" * 16) in dumped or ("{63}{70}" * 8) in dumped


def _uses_legacy_elvira_prop_names(props: list[dict[str, Any]] | None) -> bool:
    """Return True if template still uses elvira_player / elvira_score prop names."""
    names = {str(item.get("name", "")) for item in props or []}
    return "elvira_player" in names or "elvira_score" in names


def _normalize_prop_defs(props: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Drop blank template fields so entity_id resolution is not skipped."""
    cleaned: list[dict[str, Any]] = []
    for prop in props or []:
        item = dict(prop)
        if not str(item.get("template") or "").strip():
            item.pop("template", None)
        cleaned.append(item)
    return cleaned


def _props_have_blank_templates(props: list[dict[str, Any]] | None) -> bool:
    """Return True if any prop carries an empty/whitespace template string."""
    for prop in props or []:
        if "template" in prop and not str(prop.get("template") or "").strip():
            return True
    return False


async def async_load_templates(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Load templates, seeding defaults and merging any missing built-ins."""
    store = async_get_store(hass)
    data = await store.async_load()
    if not data or not data.get("templates"):
        templates = deepcopy(DEFAULT_TEMPLATES)
        await store.async_save({"templates": templates})
        return templates

    templates = list(data.get("templates") or [])
    by_id = {item.get("id"): index for index, item in enumerate(templates)}
    changed = False

    for seed in DEFAULT_TEMPLATES:
        seed_copy = deepcopy(seed)
        existing_index = by_id.get(seed_copy["id"])
        if existing_index is None:
            templates.append(seed_copy)
            by_id[seed_copy["id"]] = len(templates) - 1
            changed = True
            continue

        existing = templates[existing_index]
        if seed_copy["id"] == "elvira-house-of-horrors" and (
            _is_legacy_elvira_bars(existing.get("vbml"))
            or _uses_legacy_elvira_prop_names(existing.get("props"))
        ):
            templates[existing_index] = {
                **existing,
                "props": seed_copy["props"],
                "vbml": seed_copy["vbml"],
                "updated_at": _utc_now_iso(),
            }
            changed = True

    # Strip legacy empty template: "" that blocked entity prop resolution
    for index, item in enumerate(templates):
        props = item.get("props")
        if _props_have_blank_templates(props):
            templates[index] = {
                **item,
                "props": _normalize_prop_defs(props),
            }
            changed = True

    if changed:
        await store.async_save({"templates": templates})
    return templates


async def async_save_templates(
    hass: HomeAssistant, templates: list[dict[str, Any]]
) -> None:
    """Persist the full template list."""
    await async_get_store(hass).async_save({"templates": templates})


async def async_upsert_template(
    hass: HomeAssistant,
    *,
    name: str,
    props: list[dict[str, Any]],
    vbml: dict[str, Any],
    template_id: str | None = None,
) -> dict[str, Any]:
    """Create or update a named template."""
    templates = await async_load_templates(hass)
    name = name.strip()
    if not name:
        raise ValueError("Template name is required")

    now = _utc_now_iso()
    if template_id:
        for index, item in enumerate(templates):
            if item.get("id") == template_id:
                updated = {
                    **item,
                    "name": name,
                    "props": props,
                    "vbml": vbml,
                    "updated_at": now,
                }
                templates[index] = updated
                await async_save_templates(hass, templates)
                return updated
        raise ValueError(f"Unknown template id: {template_id}")

    # Prevent duplicate names (case-insensitive)
    for item in templates:
        if str(item.get("name", "")).lower() == name.lower():
            raise ValueError(f"A template named '{name}' already exists")

    created = {
        "id": str(uuid4()),
        "name": name,
        "props": props,
        "vbml": vbml,
        "updated_at": now,
    }
    templates.append(created)
    await async_save_templates(hass, templates)
    return created


async def async_delete_template(hass: HomeAssistant, template_id: str) -> None:
    """Delete a template by id."""
    templates = await async_load_templates(hass)
    filtered = [item for item in templates if item.get("id") != template_id]
    if len(filtered) == len(templates):
        raise ValueError(f"Unknown template id: {template_id}")
    await async_save_templates(hass, filtered)


async def async_get_template(
    hass: HomeAssistant, template_id: str
) -> dict[str, Any] | None:
    """Return a template by id or exact name."""
    needle = template_id.strip()
    for item in await async_load_templates(hass):
        if item.get("id") == needle or str(item.get("name", "")) == needle:
            return item
    return None
