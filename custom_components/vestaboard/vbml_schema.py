"""Shared VBML validation schemas for Vestaboard-x."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.helpers import config_validation as cv

from .const import (
    ALIGN_HORIZONTAL,
    ALIGN_VERTICAL,
    CONF_ALIGN,
    CONF_ATTRIBUTE,
    CONF_COMPONENTS,
    CONF_ENTITY_ID,
    CONF_HEIGHT,
    CONF_JUSTIFY,
    CONF_NAME,
    CONF_PROPS,
    CONF_TEMPLATE,
    CONF_WIDTH,
    CONF_X,
    CONF_Y,
)

_calendar = vol.Schema(
    {
        vol.Required("month"): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
        vol.Required("year"): vol.Coerce(int),
        vol.Optional("defaultDayColor"): vol.All(
            vol.Coerce(int), vol.Range(min=63, max=70)
        ),
        vol.Optional("days"): vol.Coerce(dict[str, int]),
        vol.Optional("hideSMTWTFS"): vol.Coerce(bool),
        vol.Optional("hideDates"): vol.Coerce(bool),
        vol.Optional("hideMonthYear"): vol.Coerce(bool),
    }
)
_character_codes = vol.All(vol.Coerce(int), vol.Range(min=0, max=71))
_random_colors = vol.Schema(
    {vol.Optional("colors"): [vol.All(int, vol.Range(min=63, max=71))]}
)
_raw_characters = vol.All(cv.ensure_list, [vol.All(cv.ensure_list, [_character_codes])])
_style = vol.Schema(
    {
        vol.Optional(CONF_HEIGHT): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
        vol.Optional(CONF_WIDTH): vol.All(vol.Coerce(int), vol.Range(min=1, max=22)),
        vol.Optional(CONF_JUSTIFY): vol.In(ALIGN_HORIZONTAL),
        vol.Optional(CONF_ALIGN): vol.In(ALIGN_VERTICAL),
        vol.Optional("absolutePosition"): vol.Schema(
            {
                vol.Required(CONF_X): vol.All(vol.Coerce(int), vol.Range(min=0, max=21)),
                vol.Required(CONF_Y): vol.All(vol.Coerce(int), vol.Range(min=0, max=5)),
            }
        ),
    }
)
_component = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_TEMPLATE): cv.string,
            vol.Optional("rawCharacters"): _raw_characters,
            vol.Optional("calendar"): _calendar,
            vol.Optional("randomColors"): _random_colors,
            vol.Optional("style"): _style,
        }
    ),
    cv.has_at_least_one_key(
        CONF_TEMPLATE, "rawCharacters", "calendar", "randomColors"
    ),
)

VBML_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PROPS): {cv.string: cv.string},
        vol.Required(CONF_COMPONENTS): vol.All(cv.ensure_list, [_component]),
    }
)


def validate_vbml_payload(data: Any) -> dict[str, Any]:
    """Validate and return a normalized VBML payload.

    Raises vol.Invalid on failure.
    """
    return VBML_SCHEMA(data)
