"""Persistent named VBML templates for Vestaboard-x."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .game_art import (
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_RED,
    COLOR_VIOLET,
    COLOR_WHITE,
    COLOR_YELLOW,
    LAYOUT_BANNER,
    LAYOUT_BUILDERS,
    LAYOUT_FRAME,
    LAYOUT_LABELED,
    LAYOUT_PLAYER_FOCUS,
    LAYOUT_SCORE_FOCUS,
    LAYOUT_SPLIT,
    LAYOUT_STACK,
    LAYOUT_TITLE_LEFT,
    _intro_vbml,
    icon_bat,
    icon_bolt,
    icon_claws,
    icon_footprint,
    icon_pistol,
    icon_shark_fin,
    icon_sword,
    icon_x,
)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_templates"
DATA_STORE = "template_store"

# Bump when seeded game layouts/intros change so stores refresh.
LAYOUT_VERSION = 2


def _score_comma_template(entity_id: str) -> str:
    """Format the full score with thousands separators (e.g. 1,233,532,321)."""
    return (
        "{{ '{:,.0f}'.format(states('"
        + entity_id
        + "') | float(0)) }}"
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


LOCATION_ANNOUNCEMENT_ID = "location-announcement"


def _location_announcement_template() -> dict[str, Any]:
    """Rainbow location board: NOW DISPLAYING HIGH SCORES FOR {{location}}."""
    location_entity = "sensor.2026_leaderboard_location"
    return {
        "id": LOCATION_ANNOUNCEMENT_ID,
        "name": "Location Announcement",
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
    layout: str,
    intro_icon: list[list[int]],
) -> dict[str, Any]:
    """Build a game template with a unique layout and pixel-art intro."""
    builder = LAYOUT_BUILDERS[layout]
    return {
        "id": template_id,
        "name": name,
        "layout": layout,
        "layout_version": LAYOUT_VERSION,
        "props": [
            {
                "name": "player",
                "entity_id": player_entity,
            },
            {
                "name": "score",
                "entity_id": score_entity,
                "template": _score_comma_template(score_entity),
            },
        ],
        "intro": _intro_vbml(intro_icon),
        "vbml": {
            "props": {},
            "components": builder(title, accent),
        },
        "updated_at": "1970-01-01T00:00:00+00:00",
    }


DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    _location_announcement_template(),
    _game_template(
        template_id="dungeons-dragons",
        name="Dungeons & Dragons",
        title="DUNGEONS &\nDRAGONS",
        player_entity="sensor.2026_leaderboard_dungeons_dragons_top_player",
        score_entity="sensor.2026_leaderboard_dungeons_dragons_top_score",
        accent=COLOR_YELLOW,
        layout=LAYOUT_STACK,
        intro_icon=icon_sword(),
    ),
    _game_template(
        template_id="elvira-house-of-horrors",
        name="Elvira's House of Horrors",
        title="ELVIRA'S HOUSE\nOF HORRORS",
        player_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_player",
        score_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score",
        accent=COLOR_RED,
        layout=LAYOUT_BANNER,
        intro_icon=icon_bat(),
    ),
    _game_template(
        template_id="godzilla",
        name="Godzilla",
        title="GODZILLA",
        player_entity="sensor.2026_leaderboard_godzilla_top_player",
        score_entity="sensor.2026_leaderboard_godzilla_top_score",
        accent=COLOR_GREEN,
        layout=LAYOUT_TITLE_LEFT,
        intro_icon=icon_claws(),
    ),
    _game_template(
        template_id="jaws",
        name="Jaws",
        title="JAWS",
        player_entity="sensor.2026_leaderboard_jaws_top_player",
        score_entity="sensor.2026_leaderboard_jaws_top_score",
        accent=COLOR_BLUE,
        layout=LAYOUT_LABELED,
        intro_icon=icon_shark_fin(),
    ),
    _game_template(
        template_id="john-wick",
        name="John Wick",
        title="JOHN WICK",
        player_entity="sensor.2026_leaderboard_john_wick_top_player",
        score_entity="sensor.2026_leaderboard_john_wick_top_score",
        accent=COLOR_WHITE,
        layout=LAYOUT_SCORE_FOCUS,
        intro_icon=icon_pistol(),
    ),
    _game_template(
        template_id="jurassic-park",
        name="Jurassic Park",
        title="JURASSIC PARK",
        player_entity="sensor.2026_leaderboard_jurassic_park_top_player",
        score_entity="sensor.2026_leaderboard_jurassic_park_top_score",
        accent=COLOR_ORANGE,
        layout=LAYOUT_PLAYER_FOCUS,
        intro_icon=icon_footprint(),
    ),
    _game_template(
        template_id="pokemon",
        name="Pokemon",
        title="POKEMON",
        player_entity="sensor.2026_leaderboard_pokemon_top_player",
        score_entity="sensor.2026_leaderboard_pokemon_top_score",
        accent=COLOR_YELLOW,
        layout=LAYOUT_SPLIT,
        intro_icon=icon_bolt(),
    ),
    _game_template(
        template_id="uncanny-x-men",
        name="The Uncanny X-Men",
        title="THE UNCANNY\nX-MEN",
        player_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_player",
        score_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_score",
        accent=COLOR_VIOLET,
        layout=LAYOUT_FRAME,
        intro_icon=icon_x(),
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


def _uses_k_score_format(props: list[dict[str, Any]] | None) -> bool:
    """Return True if a score prop still uses thousands/K formatting."""
    for prop in props or []:
        template = str(prop.get("template") or "")
        if "/ 1000" in template or ":,.0f}K" in template:
            return True
    return False


def _uses_combined_top_score_line(vbml: Any) -> bool:
    """Return True if VBML still packs label + score on one line."""
    return "TOP SCORE {{score}}" in str(vbml)


def _is_location_announcement(item: dict[str, Any]) -> bool:
    """Match current or legacy ids/names for the rainbow location board."""
    template_id = str(item.get("id") or "")
    name = str(item.get("name") or "").lower()
    return template_id in {LOCATION_ANNOUNCEMENT_ID, "high-scores-intro"} or name in {
        "location announcement",
        "high scores intro",
    }


def _has_rainbow_border(vbml: Any) -> bool:
    """Return True if VBML includes a rawCharacters rainbow frame."""
    try:
        components = (vbml or {}).get("components") or []
    except AttributeError:
        return False
    return any(isinstance(c, dict) and c.get("rawCharacters") for c in components)


def _has_location_prop(props: list[dict[str, Any]] | None) -> bool:
    """Return True if props include a location binding with an entity_id."""
    for prop in props or []:
        if (
            str(prop.get("name") or "") == "location"
            and str(prop.get("entity_id") or "").strip()
        ):
            return True
    return False


def _sort_templates(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep seeded templates in default order; custom ones follow alphabetically."""
    seed_order = {
        item["id"]: index for index, item in enumerate(DEFAULT_TEMPLATES)
    }
    # Legacy id maps to the location announcement slot
    seed_order["high-scores-intro"] = seed_order[LOCATION_ANNOUNCEMENT_ID]

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        template_id = str(item.get("id") or "")
        if template_id in seed_order:
            return (seed_order[template_id], "")
        return (1000, str(item.get("name") or "").lower())

    return sorted(templates, key=sort_key)


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
    seeded_game_ids = {
        item["id"]
        for item in DEFAULT_TEMPLATES
        if item.get("id") != LOCATION_ANNOUNCEMENT_ID
    }
    location_seed = deepcopy(_location_announcement_template())

    # Ensure rainbow location announcement exists (migrate legacy id/name)
    location_index = next(
        (i for i, item in enumerate(templates) if _is_location_announcement(item)),
        None,
    )
    if location_index is None:
        templates.insert(0, location_seed)
        changed = True
    else:
        existing = templates[location_index]
        if (
            existing.get("id") != LOCATION_ANNOUNCEMENT_ID
            or existing.get("name") != location_seed["name"]
            or not _has_rainbow_border(existing.get("vbml"))
            or "NOW DISPLAYING" not in str(existing.get("vbml"))
            or not _has_location_prop(existing.get("props"))
        ):
            templates[location_index] = {
                **existing,
                "id": LOCATION_ANNOUNCEMENT_ID,
                "name": location_seed["name"],
                "props": location_seed["props"],
                "vbml": location_seed["vbml"],
                "updated_at": _utc_now_iso(),
            }
            changed = True

    by_id = {item.get("id"): index for index, item in enumerate(templates)}

    for seed in DEFAULT_TEMPLATES:
        seed_copy = deepcopy(seed)
        if seed_copy["id"] == LOCATION_ANNOUNCEMENT_ID:
            continue  # handled above
        existing_index = by_id.get(seed_copy["id"])
        if existing_index is None:
            templates.append(seed_copy)
            by_id[seed_copy["id"]] = len(templates) - 1
            changed = True
            continue

        existing = templates[existing_index]
        refresh_layout = False
        if seed_copy["id"] == "elvira-house-of-horrors" and (
            _is_legacy_elvira_bars(existing.get("vbml"))
            or _uses_legacy_elvira_prop_names(existing.get("props"))
        ):
            refresh_layout = True
        if seed_copy["id"] in seeded_game_ids and (
            _uses_k_score_format(existing.get("props"))
            or _uses_combined_top_score_line(existing.get("vbml"))
            or not existing.get("intro")
            or int(existing.get("layout_version") or 0) < LAYOUT_VERSION
        ):
            refresh_layout = True
        if refresh_layout:
            templates[existing_index] = {
                **existing,
                "props": seed_copy["props"],
                "vbml": seed_copy["vbml"],
                "intro": seed_copy.get("intro"),
                "layout": seed_copy.get("layout"),
                "layout_version": seed_copy.get("layout_version", LAYOUT_VERSION),
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

    templates = _sort_templates(templates)
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
