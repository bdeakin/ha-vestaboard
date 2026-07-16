"""Support for Vestaboard services."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, HomeAssistantError, ServiceCall, callback
from homeassistant.helpers import config_validation as cv, service, template as template_helper
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
    CONF_INTRO_DURATION,
    CONF_JUSTIFY,
    CONF_MESSAGE,
    CONF_NAME,
    CONF_PROPS,
    CONF_STEP_INTERVAL_MS,
    CONF_STEP_SIZE,
    CONF_STRATEGY,
    CONF_TEMPLATE,
    CONF_TEMPLATE_ID,
    CONF_TRANSITIONS,
    CONF_VBML,
    CONF_WIDTH,
    CONF_X,
    CONF_Y,
    DEFAULT_INTRO_DURATION,
    DOMAIN,
    SERVICE_MESSAGE,
    SERVICE_SEND_TEMPLATE,
)
from .helpers import async_get_coordinator_by_device_id
from .template_store import async_get_template, async_load_templates
from .vbml_schema import VBML_SCHEMA


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

SERVICE_SEND_TEMPLATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CONF_TEMPLATE_ID): cv.string,
        vol.Optional(CONF_STRATEGY): vol.In(CONF_TRANSITIONS),
        vol.Optional(CONF_STEP_SIZE): cv.positive_int,
        vol.Optional(CONF_STEP_INTERVAL_MS): cv.positive_int,
        vol.Optional(CONF_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=43200)
        ),
        vol.Optional(CONF_INTRO_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=3, max=60)
        ),
        vol.Optional(CONF_BYPASS_QUIET_HOURS): cv.boolean,
    }
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
    """Resolve entity/template prop definitions into VBML prop strings.

    A non-empty ``template`` (Jinja) wins over ``entity_id``. Blank/whitespace
    templates are ignored so entity-backed props (e.g. player name) still resolve.
    """
    if not props:
        return {}

    resolved: dict[str, str] = {}
    for prop in props:
        name = prop[CONF_NAME]
        template = (prop.get(CONF_TEMPLATE) or "").strip()
        if template:
            try:
                rendered = template_helper.Template(
                    template, hass
                ).async_render(parse_result=False)
            except Exception as ex:
                raise HomeAssistantError(
                    f"Failed to render template for prop '{name}': {ex}"
                ) from ex
            resolved[name] = _stringify_prop_value(rendered)
            continue

        entity_id = prop.get(CONF_ENTITY_ID)
        if not entity_id:
            raise HomeAssistantError(
                f"Prop '{name}' needs an entity_id or a non-empty template"
            )
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

    When both ``vbml`` and structured ``props`` are provided, resolve the props
    and merge them into ``vbml["props"]`` so saved game templates stay live.
    """
    if vbml := call.data.get(CONF_VBML):
        # Copy so we do not mutate the service call data in place
        vbml = dict(vbml)
        if call.data.get(CONF_PROPS):
            resolved = await async_resolve_props(hass, call.data.get(CONF_PROPS))
            merged = dict(vbml.get(CONF_PROPS) or {})
            merged.update(resolved)
            vbml[CONF_PROPS] = merged
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


async def async_deliver_vbml(
    hass: HomeAssistant, call: ServiceCall, vbml: dict[str, Any]
) -> None:
    """Parse VBML and write it to one or more Vestaboard devices."""
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


async def async_deliver_intro_then_vbml(
    hass: HomeAssistant,
    call: ServiceCall,
    intro_vbml: dict[str, Any],
    score_vbml: dict[str, Any],
) -> None:
    """Show a pixel-art intro briefly, then the score board.

    The score layout is stored as the new persistent message. The intro is
    written as a temporary message so expiration reveals the score.
    """
    intro_seconds = int(
        call.data.get(CONF_INTRO_DURATION, DEFAULT_INTRO_DURATION)
    )
    base_json: dict[str, Any] = {}
    if strategy := call.data.get(CONF_STRATEGY):
        base_json[CONF_STRATEGY] = strategy
        if step_size := call.data.get(CONF_STEP_SIZE):
            base_json[CONF_STEP_SIZE] = step_size
        if step_interval := call.data.get(CONF_STEP_INTERVAL_MS):
            base_json[CONF_STEP_INTERVAL_MS] = step_interval

    for device_id in call.data[CONF_DEVICE_ID]:
        coordinator = async_get_coordinator_by_device_id(hass, device_id)
        if not call.data.get(CONF_BYPASS_QUIET_HOURS) and coordinator.quiet_hours():
            continue

        if coordinator.model is None:
            await coordinator.async_request_refresh()
        if coordinator.model is None:
            raise HomeAssistantError("Vestaboard model is not initialized")

        try:
            intro_rows = coordinator.model.parse_vbml(intro_vbml)
            score_rows = coordinator.model.parse_vbml(score_vbml)
        except Exception as ex:
            raise HomeAssistantError(f"Invalid VBML payload: {ex}") from ex

        transition = dict(base_json)
        if CONF_STRATEGY not in transition:
            transition.update(coordinator.default_transition_settings)

        # Score becomes the persistent board once the intro expires
        previous_persistent = coordinator.persistent_message
        score_duration = call.data.get(CONF_DURATION)

        if score_duration:
            # Intro → score (temporary) → previous persistent
            coordinator.persistent_message = previous_persistent

            async def _after_intro(
                _now, *, _coord=coordinator, _score=score_rows, _trans=transition
            ) -> None:
                _coord.temporary_message_expiration = None
                if _coord._cancel_cb:
                    _coord._cancel_cb()
                    _coord._cancel_cb = None
                expiration = dt_now() + timedelta(seconds=score_duration)
                _coord.temporary_message_expiration = expiration
                await _coord.write_and_update_state(
                    {"characters": _score, **_trans}
                )
                _coord._cancel_cb = async_track_point_in_time(
                    hass, _coord._handle_temporary_message_expiration, expiration
                )

            if coordinator._cancel_cb:
                coordinator._cancel_cb()
            expiration = dt_now() + timedelta(seconds=intro_seconds)
            coordinator.temporary_message_expiration = expiration
            await coordinator.write_and_update_state(
                {"characters": intro_rows, **transition}
            )
            coordinator._cancel_cb = async_track_point_in_time(
                hass, _after_intro, expiration
            )
        else:
            coordinator.persistent_message = score_rows
            if coordinator._cancel_cb:
                coordinator._cancel_cb()
            expiration = dt_now() + timedelta(seconds=intro_seconds)
            coordinator.temporary_message_expiration = expiration
            await coordinator.write_and_update_state(
                {"characters": intro_rows, **transition}
            )
            coordinator._cancel_cb = async_track_point_in_time(
                hass, coordinator._handle_temporary_message_expiration, expiration
            )

async def async_refresh_send_template_schema(hass: HomeAssistant) -> None:
    """Refresh the send_template service UI dropdown from saved templates."""
    templates = await async_load_templates(hass)
    options = [
        {"label": item.get("name") or item.get("id"), "value": item.get("id")}
        for item in templates
        if item.get("id")
    ]
    if not options:
        options = [{"label": "(no saved templates)", "value": ""}]

    service.async_set_service_schema(
        hass,
        DOMAIN,
        SERVICE_SEND_TEMPLATE,
        {
            "name": "Send saved template",
            "description": (
                "Send a VBML layout saved in the Vestaboard-x panel "
                "(e.g. a game top-score board)."
            ),
            "fields": {
                CONF_DEVICE_ID: {
                    "name": "Device",
                    "description": "Vestaboard to send the message to.",
                    "required": True,
                    "selector": {
                        "device": {"integration": DOMAIN, "multiple": True}
                    },
                },
                CONF_TEMPLATE_ID: {
                    "name": "Template",
                    "description": (
                        "Saved template from the Vestaboard-x panel "
                        "(populated from current panel templates)."
                    ),
                    "required": True,
                    "selector": {
                        "select": {
                            "mode": "dropdown",
                            "sort": True,
                            "options": options,
                        }
                    },
                },
                CONF_STRATEGY: {
                    "name": "Transition strategy",
                    "description": "Animation style when a new message is sent.",
                    "selector": {
                        "select": {
                            "translation_key": "strategy",
                            "options": list(CONF_TRANSITIONS),
                        }
                    },
                },
                CONF_STEP_SIZE: {
                    "name": "Step size",
                    "description": (
                        "Number of columns/rows/bits to animate at the same time."
                    ),
                    "selector": {
                        "number": {
                            "min": 1,
                            "max": 132,
                            "unit_of_measurement": "columns/rows/bits",
                        }
                    },
                },
                CONF_STEP_INTERVAL_MS: {
                    "name": "Step interval",
                    "description": "Delay between starting each animation step.",
                    "selector": {
                        "number": {
                            "min": 1,
                            "max": 3000,
                            "unit_of_measurement": "milliseconds",
                        }
                    },
                },
                CONF_DURATION: {
                    "name": "Duration",
                    "description": (
                        "After any intro, display the score board temporarily, "
                        "then revert to the previous persistent message."
                    ),
                    "selector": {
                        "number": {
                            "min": 10,
                            "max": 43200,
                            "unit_of_measurement": "seconds",
                        }
                    },
                },
                CONF_INTRO_DURATION: {
                    "name": "Intro duration",
                    "description": (
                        "How long to show the game's pixel-art intro before the "
                        f"score board (default {DEFAULT_INTRO_DURATION}s)."
                    ),
                    "selector": {
                        "number": {
                            "min": 3,
                            "max": 60,
                            "unit_of_measurement": "seconds",
                        }
                    },
                },
                CONF_BYPASS_QUIET_HOURS: {
                    "name": "Bypass quiet hours",
                    "description": (
                        "Ignore quiet hours setting and send the message "
                        "to the Vestaboard."
                    ),
                    "selector": {"boolean": {}},
                },
            },
        },
    )


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Vestaboard integration."""

    async def _async_service_message(call: ServiceCall) -> None:
        """Send a message to a Vestaboard."""
        vbml = await async_build_vbml(hass, call)
        await async_deliver_vbml(hass, call, vbml)

    async def _async_service_send_template(call: ServiceCall) -> None:
        """Send a VBML template saved in the Vestaboard-x panel."""
        template_id = (call.data.get(CONF_TEMPLATE_ID) or "").strip()
        if not template_id:
            raise HomeAssistantError("Select a Vestaboard-x template")
        saved = await async_get_template(hass, template_id)
        if saved is None:
            raise HomeAssistantError(
                f"Unknown Vestaboard-x template: {template_id}"
            )

        vbml = dict(saved.get(CONF_VBML) or {})
        # Always replace VBML props with a fresh resolve from entity bindings —
        # never trust snapshot values that may have been saved for editor preview.
        vbml[CONF_PROPS] = await async_resolve_props(
            hass, list(saved.get(CONF_PROPS) or [])
        )

        intro = saved.get("intro")
        if isinstance(intro, dict) and intro.get(CONF_COMPONENTS):
            await async_deliver_intro_then_vbml(hass, call, dict(intro), vbml)
        else:
            await async_deliver_vbml(hass, call, vbml)

    hass.services.async_register(
        DOMAIN,
        SERVICE_MESSAGE,
        _async_service_message,
        schema=SERVICE_MESSAGE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TEMPLATE,
        _async_service_send_template,
        schema=SERVICE_SEND_TEMPLATE_SCHEMA,
    )
    hass.async_create_task(async_refresh_send_template_schema(hass))
