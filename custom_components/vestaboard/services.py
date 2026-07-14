"""Support for Vestaboard services."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, HomeAssistantError, ServiceCall, callback
from homeassistant.helpers import config_validation as cv, template as template_helper
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util.dt import now as dt_now

from .const import (
    ALIGN_CENTER,
    ALIGN_HORIZONTAL,
    ALIGN_VERTICAL,
    CONF_ALIGN,
    CONF_ATTRIBUTE,
    CONF_BYPASS_QUIET_HOURS,
    CONF_COMPONENTS,
    CONF_DURATION,
    CONF_ENTITY_ID,
    CONF_HEIGHT,
    CONF_JUSTIFY,
    CONF_MESSAGE,
    CONF_NAME,
    CONF_PROPS,
    CONF_STEP_INTERVAL_MS,
    CONF_STEP_SIZE,
    CONF_STRATEGY,
    CONF_TEMPLATE,
    CONF_TRANSITIONS,
    CONF_VBML,
    CONF_WIDTH,
    CONF_X,
    CONF_Y,
    DOMAIN,
    SERVICE_MESSAGE,
)
from .helpers import async_get_coordinator_by_device_id

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
        # Styles to set the size of the rendered array of arrays is purposefully missing and controlled by code
        vol.Required(CONF_COMPONENTS): vol.All(cv.ensure_list, [_component]),
    }
)


def _validate_position(value: dict[str, Any]) -> dict[str, Any]:
    """Require x and y together when absolute positioning is used."""
    has_x = CONF_X in value and value[CONF_X] is not None
    has_y = CONF_Y in value and value[CONF_Y] is not None
    if has_x != has_y:
        raise vol.Invalid("Absolute position requires both x and y")
    return value


_ui_component = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_TEMPLATE): cv.string,
            vol.Optional(CONF_JUSTIFY): vol.In(ALIGN_HORIZONTAL),
            vol.Optional(CONF_ALIGN): vol.In(ALIGN_VERTICAL),
            vol.Optional(CONF_HEIGHT): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=6)
            ),
            vol.Optional(CONF_WIDTH): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=22)
            ),
            vol.Optional(CONF_X): vol.All(vol.Coerce(int), vol.Range(min=0, max=21)),
            vol.Optional(CONF_Y): vol.All(vol.Coerce(int), vol.Range(min=0, max=5)),
        }
    ),
    _validate_position,
)

_prop = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_ENTITY_ID): cv.entity_id,
            vol.Optional(CONF_ATTRIBUTE): cv.string,
            vol.Optional(CONF_TEMPLATE): cv.string,
        }
    ),
    cv.has_at_least_one_key(CONF_ENTITY_ID, CONF_TEMPLATE),
)

SERVICE_MESSAGE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(CONF_MESSAGE): cv.string,
            vol.Optional(CONF_JUSTIFY, default=ALIGN_CENTER): vol.In(ALIGN_HORIZONTAL),
            vol.Optional(CONF_ALIGN, default=ALIGN_CENTER): vol.In(ALIGN_VERTICAL),
            vol.Optional(CONF_PROPS): vol.All(cv.ensure_list, [_prop]),
            vol.Optional(CONF_COMPONENTS): vol.All(cv.ensure_list, [_ui_component]),
            vol.Optional(CONF_VBML): VBML_SCHEMA,
            vol.Optional(CONF_STRATEGY): vol.In(CONF_TRANSITIONS),
            vol.Optional(CONF_STEP_SIZE): cv.positive_int,
            vol.Optional(CONF_STEP_INTERVAL_MS): cv.positive_int,
            vol.Optional(CONF_DURATION): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=43200)
            ),
            vol.Optional(CONF_BYPASS_QUIET_HOURS): cv.boolean,
        }
    ),
    cv.has_at_least_one_key(CONF_MESSAGE, CONF_VBML, CONF_COMPONENTS),
)


def _normalize_ui_component(component: dict[str, Any]) -> dict[str, Any]:
    """Convert flat UI component fields into a VBML component."""
    style: dict[str, Any] = {}
    if justify := component.get(CONF_JUSTIFY):
        style[CONF_JUSTIFY] = justify
    if align := component.get(CONF_ALIGN):
        style[CONF_ALIGN] = align
    if height := component.get(CONF_HEIGHT):
        style[CONF_HEIGHT] = height
    if width := component.get(CONF_WIDTH):
        style[CONF_WIDTH] = width
    if CONF_X in component and CONF_Y in component:
        style["absolutePosition"] = {
            CONF_X: component[CONF_X],
            CONF_Y: component[CONF_Y],
        }

    result: dict[str, Any] = {CONF_TEMPLATE: component[CONF_TEMPLATE]}
    if style:
        result["style"] = style
    return result


def _stringify_prop_value(value: Any) -> str:
    """Convert a Home Assistant value into a VBML prop string."""
    if value is None:
        return ""
    return str(value)


async def async_resolve_props(
    hass: HomeAssistant, props: list[dict[str, Any]] | None
) -> dict[str, str]:
    """Resolve entity/template prop definitions into VBML prop strings."""
    if not props:
        return {}

    resolved: dict[str, str] = {}
    for prop in props:
        name = prop[CONF_NAME]
        if CONF_TEMPLATE in prop:
            try:
                rendered = template_helper.Template(
                    prop[CONF_TEMPLATE], hass
                ).async_render(parse_result=False)
            except Exception as ex:
                raise HomeAssistantError(
                    f"Failed to render template for prop '{name}': {ex}"
                ) from ex
            resolved[name] = _stringify_prop_value(rendered)
            continue

        entity_id = prop[CONF_ENTITY_ID]
        state = hass.states.get(entity_id)
        if state is None:
            raise HomeAssistantError(
                f"Entity '{entity_id}' for prop '{name}' was not found"
            )

        if attribute := prop.get(CONF_ATTRIBUTE):
            if attribute not in state.attributes:
                raise HomeAssistantError(
                    f"Attribute '{attribute}' not found on entity '{entity_id}' "
                    f"for prop '{name}'"
                )
            resolved[name] = _stringify_prop_value(state.attributes[attribute])
        else:
            resolved[name] = _stringify_prop_value(state.state)

    return resolved


async def async_build_vbml(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Build a VBML payload from service call data.

    Priority: raw vbml > structured components/props > plain message.
    """
    if vbml := call.data.get(CONF_VBML):
        return vbml

    if components := call.data.get(CONF_COMPONENTS):
        return {
            CONF_PROPS: await async_resolve_props(hass, call.data.get(CONF_PROPS)),
            CONF_COMPONENTS: [_normalize_ui_component(c) for c in components],
        }

    align = call.data.get(CONF_ALIGN, ALIGN_CENTER)
    justify = call.data.get(CONF_JUSTIFY, ALIGN_CENTER)
    return {
        CONF_COMPONENTS: [
            {
                "style": {CONF_ALIGN: align, CONF_JUSTIFY: justify},
                CONF_TEMPLATE: call.data.get(CONF_MESSAGE, "")
                .replace("  ", "{70}{70}")
                .replace("\n\n", "\n{70}\n"),
            }
        ]
    }


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Vestaboard integration."""

    async def _async_service_message(call: ServiceCall) -> None:
        """Send a message to a Vestaboard."""
        vbml = await async_build_vbml(hass, call)

        base_json: dict[str, Any] = {}
        if strategy := call.data.get(CONF_STRATEGY):
            base_json[CONF_STRATEGY] = strategy
            if step_size := call.data.get(CONF_STEP_SIZE):
                base_json[CONF_STEP_SIZE] = step_size
            if step_interval := call.data.get(CONF_STEP_INTERVAL_MS):
                base_json[CONF_STEP_INTERVAL_MS] = step_interval

        for device_id in call.data[CONF_DEVICE_ID]:
            json = dict(base_json)
            coordinator = async_get_coordinator_by_device_id(hass, device_id)
            if not call.data.get(CONF_BYPASS_QUIET_HOURS) and coordinator.quiet_hours():
                continue

            if coordinator.model is None:
                await coordinator.async_request_refresh()
            if coordinator.model is None:
                raise HomeAssistantError("Vestaboard model is not initialized")
            try:
                rows = coordinator.model.parse_vbml(vbml)
            except Exception as ex:
                raise HomeAssistantError(f"Invalid VBML payload: {ex}") from ex
            json["characters"] = rows

            if CONF_STRATEGY not in json:
                json.update(coordinator.default_transition_settings)

            if duration := call.data.get(CONF_DURATION):  # This is a temporary message
                if coordinator._cancel_cb:
                    coordinator._cancel_cb()
                expiration = dt_now() + timedelta(seconds=duration)
                coordinator.temporary_message_expiration = expiration
                await coordinator.write_and_update_state(json)
                coordinator._cancel_cb = async_track_point_in_time(
                    hass, coordinator._handle_temporary_message_expiration, expiration
                )
            else:
                coordinator.persistent_message = rows
                expiration = coordinator.temporary_message_expiration
                if not (expiration and expiration > dt_now()):
                    await coordinator.write_and_update_state(json)

    hass.services.async_register(
        DOMAIN,
        SERVICE_MESSAGE,
        _async_service_message,
        schema=SERVICE_MESSAGE_SCHEMA,
    )
