"""Support for Vestaboard services."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
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
    CONF_REPEAT,
    CONF_SEQUENCE_ID,
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
    SERVICE_PLAY_SEQUENCE,
    SERVICE_SEND_TEMPLATE,
    SERVICE_STOP_SEQUENCE,
)
from .demtoberfest import (
    ANIMATION_DIAGONAL_BLUE_WAVE,
    WAVE_SECONDS,
    build_diagonal_wave_frames,
)
from .game_art import build_reveal_frames
from .helpers import async_get_coordinator_by_device_id
from .template_store import (
    async_get_sequence,
    async_get_template,
    async_load_sequences,
    async_load_templates,
)
from .vbml_schema import VBML_SCHEMA

_LOGGER = logging.getLogger(__name__)
_SEQUENCE_TASK = "display_sequence_task"
_SEQUENCE_TOKEN = "display_sequence_token"
_SEQUENCE_RESTORE = "display_sequence_restore"


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

SERVICE_PLAY_SEQUENCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CONF_SEQUENCE_ID): cv.string,
        vol.Optional(CONF_REPEAT, default=False): cv.boolean,
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


def _intro_raw_grid(intro_vbml: dict[str, Any]) -> list[list[int]] | None:
    """Extract the 6×22 color grid from an intro VBML payload."""
    if raw := intro_vbml.get("raw"):
        return raw
    for component in intro_vbml.get(CONF_COMPONENTS) or []:
        if raw_chars := component.get("rawCharacters"):
            return raw_chars
    return None


def _frame_vbml(grid: list[list[int]]) -> dict[str, Any]:
    return {
        "props": {},
        "components": [
            {
                "style": {
                    "height": 6,
                    "width": 22,
                    "absolutePosition": {"x": 0, "y": 0},
                },
                "rawCharacters": grid,
            }
        ],
    }


async def async_deliver_intro_then_vbml(
    hass: HomeAssistant,
    call: ServiceCall,
    intro_vbml: dict[str, Any],
    score_vbml: dict[str, Any],
) -> None:
    """Animate a pixel-art intro (TL→BR reveal), then show the score board."""
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
            score_rows = coordinator.model.parse_vbml(score_vbml)
        except Exception as ex:
            raise HomeAssistantError(f"Invalid VBML payload: {ex}") from ex

        intro_strategy = intro_vbml.get("strategy", "column")
        score_transition = dict(base_json)
        if CONF_STRATEGY not in score_transition:
            score_transition.update(coordinator.default_transition_settings)
        if CONF_STRATEGY not in call.data:
            score_transition[CONF_STRATEGY] = "column"

        raw = await hass.async_add_executor_job(_intro_raw_grid, intro_vbml)
        if raw:
            frames = await hass.async_add_executor_job(build_reveal_frames, raw)
            try:
                intro_frame_rows = [
                    coordinator.model.parse_vbml(_frame_vbml(grid)) for grid in frames
                ]
            except Exception as ex:
                raise HomeAssistantError(f"Invalid intro VBML: {ex}") from ex
        else:
            try:
                intro_frame_rows = [coordinator.model.parse_vbml(intro_vbml)]
            except Exception as ex:
                raise HomeAssistantError(f"Invalid intro VBML: {ex}") from ex

        previous_persistent = coordinator.persistent_message
        score_duration = call.data.get(CONF_DURATION)

        if coordinator._cancel_cb:
            coordinator._cancel_cb()
            coordinator._cancel_cb = None
        coordinator.temporary_message_expiration = None

        frame_delay = intro_seconds / max(len(intro_frame_rows), 1)
        for index, rows in enumerate(intro_frame_rows):
            frame_trans: dict[str, Any] = {
                CONF_STRATEGY: intro_strategy if index == 0 else "classic",
            }
            if index == 0:
                frame_trans.update(
                    {
                        k: v
                        for k, v in base_json.items()
                        if k in (CONF_STEP_SIZE, CONF_STEP_INTERVAL_MS)
                    }
                )
            await coordinator.write_and_update_state(
                {"characters": rows, **frame_trans}
            )
            if index < len(intro_frame_rows) - 1:
                await asyncio.sleep(frame_delay)

        if score_duration:
            coordinator.persistent_message = previous_persistent
            expiration = dt_now() + timedelta(seconds=score_duration)
            coordinator.temporary_message_expiration = expiration
            await coordinator.write_and_update_state(
                {"characters": score_rows, **score_transition}
            )
            coordinator._cancel_cb = async_track_point_in_time(
                hass, coordinator._handle_temporary_message_expiration, expiration
            )
        else:
            coordinator.persistent_message = score_rows
            await coordinator.write_and_update_state(
                {"characters": score_rows, **score_transition}
            )


def _cancel_temporary(coordinator) -> None:
    """Drop a pending revert so a sequence is not replaced mid-play."""
    if coordinator._cancel_cb:
        coordinator._cancel_cb()
        coordinator._cancel_cb = None
    coordinator.temporary_message_expiration = None


def _copy_rows(rows: list[list[int]] | None) -> list[list[int]] | None:
    if not rows:
        return None
    return [list(row) for row in rows]


async def _coordinators_for_devices(
    hass: HomeAssistant, device_ids: list[str], bypass: bool
) -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    for device_id in device_ids:
        try:
            coordinator = async_get_coordinator_by_device_id(hass, device_id)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        if not bypass and coordinator.quiet_hours():
            continue
        if coordinator.model is None:
            await coordinator.async_request_refresh()
        if coordinator.model is None:
            raise HomeAssistantError("Vestaboard model is not initialized")
        pairs.append((device_id, coordinator))
    return pairs


async def _write_rows(coordinator, rows: list[list[int]], strategy: str) -> None:
    await coordinator.write_and_update_state(
        {"characters": rows, CONF_STRATEGY: strategy}
    )


async def _play_grids(
    pairs: list[tuple[str, Any]],
    grids: list[list[list[int]]],
    total_seconds: float,
    first_strategy: str = "classic",
) -> None:
    """Send the same full-board frames to each device, then wait between them."""
    parsed: list[list[list[list[int]]]] = []
    for _device_id, coordinator in pairs:
        try:
            parsed.append(
                [coordinator.model.parse_vbml(_frame_vbml(grid)) for grid in grids]
            )
        except Exception as ex:
            raise HomeAssistantError(f"Invalid frame: {ex}") from ex
    frame_count = len(grids)
    delay = total_seconds / max(frame_count, 1)
    for index in range(frame_count):
        strategy = first_strategy if index == 0 else "classic"
        for pair_index, (_device_id, coordinator) in enumerate(pairs):
            await _write_rows(coordinator, parsed[pair_index][index], strategy)
        if index < frame_count - 1:
            await asyncio.sleep(delay)


async def _present_template(
    hass: HomeAssistant, pairs: list[tuple[str, Any]], template: dict[str, Any]
) -> None:
    """Show one sequence template without scheduling a revert."""
    if template.get("animation") == ANIMATION_DIAGONAL_BLUE_WAVE:
        frames = await hass.async_add_executor_job(build_diagonal_wave_frames)
        await _play_grids(pairs, frames, WAVE_SECONDS)
        return

    intro = template.get("intro")
    if isinstance(intro, dict) and intro.get(CONF_COMPONENTS):
        raw = await hass.async_add_executor_job(_intro_raw_grid, intro)
        if raw:
            frames = await hass.async_add_executor_job(build_reveal_frames, raw)
            await _play_grids(pairs, frames, DEFAULT_INTRO_DURATION, "column")

    vbml = dict(template.get(CONF_VBML) or {})
    vbml[CONF_PROPS] = await async_resolve_props(
        hass, list(template.get(CONF_PROPS) or [])
    )
    for _device_id, coordinator in pairs:
        try:
            rows = coordinator.model.parse_vbml(vbml)
        except Exception as ex:
            raise HomeAssistantError(f"Invalid VBML payload: {ex}") from ex
        await _write_rows(coordinator, rows, "column")


async def async_deliver_wave(hass: HomeAssistant, call: ServiceCall) -> None:
    """Play the diagonal blue wave once."""
    frames = await hass.async_add_executor_job(build_diagonal_wave_frames)
    bypass = bool(call.data.get(CONF_BYPASS_QUIET_HOURS))
    pairs = await _coordinators_for_devices(hass, list(call.data[CONF_DEVICE_ID]), bypass)
    for _device_id, coordinator in pairs:
        _cancel_temporary(coordinator)
    if not pairs:
        return
    await _play_grids(pairs, frames, WAVE_SECONDS)
    duration = call.data.get(CONF_DURATION)
    for _device_id, coordinator in pairs:
        if duration:
            expiration = dt_now() + timedelta(seconds=duration)
            coordinator.temporary_message_expiration = expiration
            coordinator._cancel_cb = async_track_point_in_time(
                hass, coordinator._handle_temporary_message_expiration, expiration
            )
        else:
            coordinator.persistent_message = _copy_rows(coordinator.data)


async def _restore_snapshot(
    hass: HomeAssistant, snapshot: dict[str, list[list[int]] | None]
) -> None:
    for device_id, rows in snapshot.items():
        if not rows:
            continue
        try:
            coordinator = async_get_coordinator_by_device_id(hass, device_id)
        except ValueError:
            continue
        coordinator.persistent_message = rows
        _cancel_temporary(coordinator)
        try:
            await _write_rows(coordinator, rows, "classic")
        except Exception:  # noqa: BLE001 - keep the sequence from crashing on restore
            _LOGGER.exception("Failed to restore the previous Vestaboard message")


async def _run_display_sequence(
    hass: HomeAssistant,
    call: ServiceCall,
    sequence: dict[str, Any],
    token: object,
) -> None:
    """Play each template in order. Repeat waits out the sequence interval."""
    bypass = bool(call.data.get(CONF_BYPASS_QUIET_HOURS))
    repeat = bool(call.data.get(CONF_REPEAT))
    pairs = await _coordinators_for_devices(
        hass, list(call.data[CONF_DEVICE_ID]), bypass
    )
    domain = hass.data.setdefault(DOMAIN, {})
    if not pairs:
        _LOGGER.info("Display sequence skipped because the board is in quiet hours")
        if domain.get(_SEQUENCE_TOKEN) is token:
            domain.pop(_SEQUENCE_TOKEN, None)
            domain.pop(_SEQUENCE_TASK, None)
        return
    if _SEQUENCE_RESTORE not in domain:
        domain[_SEQUENCE_RESTORE] = {
            device_id: _copy_rows(coordinator.persistent_message)
            for device_id, coordinator in pairs
        }
    for _device_id, coordinator in pairs:
        _cancel_temporary(coordinator)

    try:
        while domain.get(_SEQUENCE_TOKEN) is token:
            started = asyncio.get_running_loop().time()
            for item in sequence.get("items") or []:
                if domain.get(_SEQUENCE_TOKEN) is not token:
                    return
                template_id = str(item.get("template_id") or "")
                template = await async_get_template(hass, template_id)
                if template is None:
                    _LOGGER.warning(
                        "Display sequence %s is missing template %s",
                        sequence.get("name"),
                        template_id,
                    )
                    continue
                await _present_template(hass, pairs, template)
                duration = item.get(CONF_DURATION)
                if (
                    duration is None
                    and template.get("animation") != ANIMATION_DIAGONAL_BLUE_WAVE
                ):
                    duration = sequence.get("default_duration")
                if duration:
                    await asyncio.sleep(float(duration))
            if not repeat:
                break
            elapsed = asyncio.get_running_loop().time() - started
            await _restore_snapshot(hass, domain.get(_SEQUENCE_RESTORE) or {})
            gap = float(sequence.get("repeat_seconds") or 900) - elapsed
            if gap > 0 and domain.get(_SEQUENCE_TOKEN) is token:
                await asyncio.sleep(gap)
    finally:
        if domain.get(_SEQUENCE_TOKEN) is token:
            await _restore_snapshot(hass, domain.get(_SEQUENCE_RESTORE) or {})
            domain.pop(_SEQUENCE_RESTORE, None)
            domain.pop(_SEQUENCE_TOKEN, None)
            domain.pop(_SEQUENCE_TASK, None)


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


async def async_refresh_play_sequence_schema(hass: HomeAssistant) -> None:
    """Refresh the play_sequence dropdown from saved display sequences."""
    sequences = await async_load_sequences(hass)
    options = [
        {"label": item.get("name") or item.get("id"), "value": item.get("id")}
        for item in sequences
        if item.get("id")
    ]
    if not options:
        options = [{"label": "(no display sequences)", "value": ""}]

    service.async_set_service_schema(
        hass,
        DOMAIN,
        SERVICE_PLAY_SEQUENCE,
        {
            "name": "Play display sequence",
            "description": (
                "Play the templates in a display sequence, such as "
                "Pinball Scores or Demtoberfest 2026."
            ),
            "fields": {
                CONF_DEVICE_ID: {
                    "name": "Device",
                    "description": "Vestaboard to play the sequence on.",
                    "required": True,
                    "selector": {
                        "device": {"integration": DOMAIN, "multiple": True}
                    },
                },
                CONF_SEQUENCE_ID: {
                    "name": "Display sequence",
                    "description": "Pinball Scores or Demtoberfest 2026.",
                    "required": True,
                    "selector": {
                        "select": {
                            "mode": "dropdown",
                            "options": options,
                        }
                    },
                },
                CONF_REPEAT: {
                    "name": "Repeat",
                    "description": (
                        "Start the sequence again every 15 minutes until stopped. "
                        "Demtoberfest 2026 is built for this."
                    ),
                    "selector": {"boolean": {}},
                },
                CONF_BYPASS_QUIET_HOURS: {
                    "name": "Bypass quiet hours",
                    "description": (
                        "Ignore quiet hours and play the sequence."
                    ),
                    "selector": {"boolean": {}},
                },
            },
        },
    )


async def _async_refresh_service_schemas(hass: HomeAssistant) -> None:
    """Seed stored templates and sequences, then refresh action dropdowns."""
    await async_refresh_send_template_schema(hass)
    await async_refresh_play_sequence_schema(hass)


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

        if saved.get("animation") == ANIMATION_DIAGONAL_BLUE_WAVE:
            await async_deliver_wave(hass, call)
            return

        intro = saved.get("intro")
        if isinstance(intro, dict) and intro.get(CONF_COMPONENTS):
            await async_deliver_intro_then_vbml(hass, call, dict(intro), vbml)
        else:
            await async_deliver_vbml(hass, call, vbml)

    async def _async_service_play_sequence(call: ServiceCall) -> None:
        """Play a display sequence in the background."""
        sequence_id = (call.data.get(CONF_SEQUENCE_ID) or "").strip()
        if not sequence_id:
            raise HomeAssistantError("Select a display sequence")
        sequence = await async_get_sequence(hass, sequence_id)
        if sequence is None:
            raise HomeAssistantError(f"Unknown display sequence: {sequence_id}")

        domain = hass.data.setdefault(DOMAIN, {})
        token = object()
        domain[_SEQUENCE_TOKEN] = token
        previous = domain.get(_SEQUENCE_TASK)
        if previous and not previous.done():
            previous.cancel()

        async def _runner() -> None:
            try:
                await _run_display_sequence(hass, call, sequence, token)
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception(
                    "Display sequence %s failed", sequence.get("name")
                )

        domain[_SEQUENCE_TASK] = hass.async_create_task(_runner())

    async def _async_service_stop_sequence(_call: ServiceCall) -> None:
        """Stop the display sequence that is currently playing."""
        task = hass.data.get(DOMAIN, {}).get(_SEQUENCE_TASK)
        if task and not task.done():
            task.cancel()

    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_SEQUENCE,
        _async_service_play_sequence,
        schema=SERVICE_PLAY_SEQUENCE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_SEQUENCE,
        _async_service_stop_sequence,
    )

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
    hass.async_create_task(_async_refresh_service_schemas(hass))
