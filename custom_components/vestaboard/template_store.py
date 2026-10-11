"""Persistent named VBML templates for Vestaboard-x."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .demtoberfest import DEMTOBERFEST_SEQUENCE, DEMTOBERFEST_TEMPLATES
from .game_art import (
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_RED,
    COLOR_VIOLET,
    COLOR_WHITE,
    COLOR_YELLOW,
    INTRO_BUILDERS,
    LAYOUT_BUILDERS,
    LAYOUT_DND,
    LAYOUT_ELVIRA,
    LAYOUT_GODZILLA,
    LAYOUT_JAWS,
    LAYOUT_JOHN_WICK,
    LAYOUT_JURASSIC,
    LAYOUT_POKEMON,
    LAYOUT_XMEN,
    _intro_vbml,
)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_templates"
DATA_STORE = "template_store"

# Bump when seeded game layouts/intros change so stores refresh.
LAYOUT_VERSION = 3


def _score_compact_template(entity_id: str) -> str:
    """Compact score: full number, or K / M when needed for width."""
    return (
        "{% set s = states('"
        + entity_id
        + "') | float(0) %}"
        "{% if s >= 1000000 %}"
        "{{ '{:,.1f}M'.format(s / 1000000) }}"
        "{% elif s >= 10000 %}"
        "{{ '{:,.0f}K'.format(s / 1000) }}"
        "{% else %}"
        "{{ '{:,.0f}'.format(s) }}"
        "{% endif %}"
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
) -> dict[str, Any]:
    """Build a game template with a unique layout and pixel-art intro."""
    builder = LAYOUT_BUILDERS[layout]
    intro_raw = INTRO_BUILDERS[layout]()
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
                "template": _score_compact_template(score_entity),
            },
        ],
        "intro": _intro_vbml(intro_raw),
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
        layout=LAYOUT_DND,
    ),
    _game_template(
        template_id="elvira-house-of-horrors",
        name="Elvira's House of Horrors",
        title="ELVIRA'S HOUSE\nOF HORRORS",
        player_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_player",
        score_entity="sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score",
        accent=COLOR_RED,
        layout=LAYOUT_ELVIRA,
    ),
    _game_template(
        template_id="godzilla",
        name="Godzilla",
        title="GODZILLA",
        player_entity="sensor.2026_leaderboard_godzilla_top_player",
        score_entity="sensor.2026_leaderboard_godzilla_top_score",
        accent=COLOR_GREEN,
        layout=LAYOUT_GODZILLA,
    ),
    _game_template(
        template_id="jaws",
        name="Jaws",
        title="JAWS",
        player_entity="sensor.2026_leaderboard_jaws_top_player",
        score_entity="sensor.2026_leaderboard_jaws_top_score",
        accent=COLOR_BLUE,
        layout=LAYOUT_JAWS,
    ),
    _game_template(
        template_id="john-wick",
        name="John Wick",
        title="JOHN WICK",
        player_entity="sensor.2026_leaderboard_john_wick_top_player",
        score_entity="sensor.2026_leaderboard_john_wick_top_score",
        accent=COLOR_WHITE,
        layout=LAYOUT_JOHN_WICK,
    ),
    _game_template(
        template_id="jurassic-park",
        name="Jurassic Park",
        title="JURASSIC PARK",
        player_entity="sensor.2026_leaderboard_jurassic_park_top_player",
        score_entity="sensor.2026_leaderboard_jurassic_park_top_score",
        accent=COLOR_ORANGE,
        layout=LAYOUT_JURASSIC,
    ),
    _game_template(
        template_id="pokemon",
        name="Pokemon",
        title="POKEMON",
        player_entity="sensor.2026_leaderboard_pokemon_top_player",
        score_entity="sensor.2026_leaderboard_pokemon_top_score",
        accent=COLOR_YELLOW,
        layout=LAYOUT_POKEMON,
    ),
    _game_template(
        template_id="uncanny-x-men",
        name="The Uncanny X-Men",
        title="THE UNCANNY\nX-MEN",
        player_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_player",
        score_entity="sensor.2026_leaderboard_the_uncanny_x_men_top_score",
        accent=COLOR_VIOLET,
        layout=LAYOUT_XMEN,
    ),
]

DEFAULT_TEMPLATES.extend(DEMTOBERFEST_TEMPLATES)

PINBALL_SEQUENCE_ID = "pinball-scores"
PINBALL_DEFAULT_DURATION = 30


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


def _default_sequences() -> list[dict[str, Any]]:
    """Pinball Scores, then Demtoberfest 2026."""
    pinball_items = [
        {"template_id": item["id"]}
        for item in DEFAULT_TEMPLATES
        if item.get("id") == LOCATION_ANNOUNCEMENT_ID or item.get("layout")
    ]
    return [
        {
            "id": PINBALL_SEQUENCE_ID,
            "name": "Pinball Scores",
            "description": (
                "Location announcement, then each Stern game. "
                "Play holds each board for 30 seconds."
            ),
            "sequence_version": 1,
            "default_duration": PINBALL_DEFAULT_DURATION,
            "items": pinball_items,
        },
        deepcopy(DEMTOBERFEST_SEQUENCE),
    ]


def _merge_sequences(
    sequences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """Insert missing built-in sequences and fill in any missing templates."""
    changed = False
    by_id = {item.get("id"): item for item in sequences}
    merged = list(sequences)
    for seed in _default_sequences():
        existing = by_id.get(seed["id"])
        if existing is None:
            merged.append(deepcopy(seed))
            by_id[seed["id"]] = merged[-1]
            changed = True
            continue
        if int(existing.get("sequence_version") or 0) < int(seed["sequence_version"]):
            existing["name"] = seed["name"]
            existing["description"] = seed.get("description")
            existing["items"] = deepcopy(seed["items"])
            existing["sequence_version"] = seed["sequence_version"]
            if "repeat_seconds" in seed:
                existing["repeat_seconds"] = seed["repeat_seconds"]
            else:
                existing.pop("repeat_seconds", None)
            if "default_duration" in seed:
                existing["default_duration"] = seed["default_duration"]
            else:
                existing.pop("default_duration", None)
            changed = True
            continue
        have = {item.get("template_id") for item in existing.get("items") or []}
        for item in seed["items"]:
            if item["template_id"] not in have:
                existing.setdefault("items", []).append(deepcopy(item))
                have.add(item["template_id"])
                changed = True
    return merged, changed


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


async def async_load_library(
    hass: HomeAssistant,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load templates and display sequences, seeding anything missing."""
    store = async_get_store(hass)
    data = await store.async_load()
    if not data or not data.get("templates"):
        templates = deepcopy(DEFAULT_TEMPLATES)
        sequences = _default_sequences()
        await store.async_save({"templates": templates, "sequences": sequences})
        return templates, sequences

    templates = list(data.get("templates") or [])
    by_id = {item.get("id"): index for index, item in enumerate(templates)}
    changed = False
    seeded_game_ids = {
        item["id"] for item in DEFAULT_TEMPLATES if item.get("layout")
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
        if seed_copy.get("event_version"):
            if existing_index is None:
                templates.append(seed_copy)
                by_id[seed_copy["id"]] = len(templates) - 1
                changed = True
            else:
                existing = templates[existing_index]
                if int(existing.get("event_version") or 0) < int(
                    seed_copy["event_version"]
                ):
                    templates[existing_index] = {
                        **existing,
                        "name": seed_copy["name"],
                        "props": seed_copy["props"],
                        "vbml": seed_copy["vbml"],
                        "animation": seed_copy.get("animation"),
                        "event_version": seed_copy["event_version"],
                        "updated_at": _utc_now_iso(),
                    }
                    if not seed_copy.get("animation"):
                        templates[existing_index].pop("animation", None)
                    changed = True
            continue

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

    sequences, sequences_changed = _merge_sequences(list(data.get("sequences") or []))
    if sequences_changed:
        changed = True

    templates = _sort_templates(templates)
    if changed:
        await store.async_save({"templates": templates, "sequences": sequences})
    return templates, sequences


async def async_load_templates(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Load templates, seeding defaults and merging any missing built-ins."""
    templates, _sequences = await async_load_library(hass)
    return templates


async def async_load_sequences(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Load display sequences, seeding Pinball Scores and Demtoberfest 2026."""
    _templates, sequences = await async_load_library(hass)
    return sequences


async def async_get_sequence(
    hass: HomeAssistant, sequence_id: str
) -> dict[str, Any] | None:
    """Return a display sequence by id or exact name."""
    needle = sequence_id.strip()
    for item in await async_load_sequences(hass):
        if item.get("id") == needle or str(item.get("name", "")) == needle:
            return item
    return None


async def async_save_templates(
    hass: HomeAssistant, templates: list[dict[str, Any]]
) -> None:
    """Persist templates without dropping display sequences."""
    data = await async_get_store(hass).async_load() or {}
    sequences = data.get("sequences") or _default_sequences()
    await async_get_store(hass).async_save(
        {"templates": templates, "sequences": sequences}
    )


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
    """Delete a template by id and drop it from display sequences."""
    templates, sequences = await async_load_library(hass)
    filtered = [item for item in templates if item.get("id") != template_id]
    if len(filtered) == len(templates):
        raise ValueError(f"Unknown template id: {template_id}")
    for sequence in sequences:
        sequence["items"] = [
            item
            for item in sequence.get("items") or []
            if item.get("template_id") != template_id
        ]
    await async_get_store(hass).async_save(
        {"templates": filtered, "sequences": sequences}
    )


async def async_get_template(
    hass: HomeAssistant, template_id: str
) -> dict[str, Any] | None:
    """Return a template by id or exact name."""
    needle = template_id.strip()
    for item in await async_load_templates(hass):
        if item.get("id") == needle or str(item.get("name", "")) == needle:
            return item
    return None
