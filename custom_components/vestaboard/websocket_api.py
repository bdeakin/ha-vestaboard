"""WebSocket API for Vestaboard-x VBML tooling."""

from __future__ import annotations

import json
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .helpers import async_get_coordinator_by_device_id
from .services import async_refresh_send_template_schema, async_resolve_props
from .template_store import (
    async_delete_template,
    async_load_templates,
    async_upsert_template,
)
from .vbml_schema import validate_vbml_payload

_PROP_REF = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


@callback
def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Register Vestaboard-x websocket commands."""
    websocket_api.async_register_command(hass, websocket_list_devices)
    websocket_api.async_register_command(hass, websocket_validate_vbml)
    websocket_api.async_register_command(hass, websocket_resolve_props)
    websocket_api.async_register_command(hass, websocket_list_templates)
    websocket_api.async_register_command(hass, websocket_save_template)
    websocket_api.async_register_command(hass, websocket_delete_template)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/list_devices",
    }
)
@websocket_api.async_response
async def websocket_list_devices(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return configured Vestaboard devices."""
    device_registry = dr.async_get(hass)
    devices: list[dict[str, str]] = []
    for device in device_registry.devices.values():
        if not any(
            (entry := hass.config_entries.async_get_entry(entry_id))
            and entry.domain == DOMAIN
            for entry_id in device.config_entries
        ):
            continue
        devices.append(
            {
                "id": device.id,
                "name": device.name_by_user or device.name or "Vestaboard",
            }
        )
    connection.send_result(msg["id"], {"devices": devices})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/validate_vbml",
        vol.Required("vbml"): vol.Any(dict, str),
        vol.Optional("device_id"): str,
    }
)
@websocket_api.async_response
async def websocket_validate_vbml(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Validate VBML JSON syntax and schema; optionally parse for a device."""
    errors: list[str] = []
    warnings: list[str] = []
    vbml_raw = msg["vbml"]

    if isinstance(vbml_raw, str):
        try:
            vbml_data = json.loads(vbml_raw)
        except json.JSONDecodeError as err:
            connection.send_result(
                msg["id"],
                {
                    "valid": False,
                    "errors": [
                        f"JSON syntax error: {err.msg} "
                        f"(line {err.lineno}, col {err.colno})"
                    ],
                    "warnings": [],
                },
            )
            return
    else:
        vbml_data = vbml_raw

    try:
        vbml = validate_vbml_payload(vbml_data)
    except vol.Invalid as err:
        connection.send_result(
            msg["id"],
            {
                "valid": False,
                "errors": [f"VBML schema error: {err}"],
                "warnings": [],
            },
        )
        return

    props = set((vbml.get("props") or {}).keys())
    for index, component in enumerate(vbml.get("components") or []):
        template = component.get("template") or ""
        for match in _PROP_REF.finditer(template):
            name = match.group(1)
            if name not in props:
                warnings.append(
                    f"Component[{index}] references prop '{{{{{name}}}}}' "
                    "which is not defined in props"
                )

    device_id = msg.get("device_id")
    if device_id:
        try:
            coordinator = async_get_coordinator_by_device_id(hass, device_id)
            if coordinator.model is None:
                await coordinator.async_request_refresh()
            if coordinator.model is None:
                errors.append("Vestaboard model is not initialized")
            else:
                try:
                    coordinator.model.parse_vbml(vbml)
                except Exception as ex:  # noqa: BLE001 - surface to UI
                    errors.append(f"VBML parse error: {ex}")
        except ValueError as ex:
            errors.append(str(ex))

    connection.send_result(
        msg["id"],
        {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/resolve_props",
        vol.Required("props"): list,
    }
)
@websocket_api.async_response
async def websocket_resolve_props(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Resolve prop definitions to string values for the VBML editor."""
    try:
        resolved = await async_resolve_props(hass, msg["props"])
    except Exception as ex:  # noqa: BLE001 - surface to UI
        connection.send_result(
            msg["id"],
            {"ok": False, "error": str(ex), "props": {}},
        )
        return
    connection.send_result(msg["id"], {"ok": True, "props": resolved})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/list_templates",
    }
)
@websocket_api.async_response
async def websocket_list_templates(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return saved VBML templates."""
    templates = await async_load_templates(hass)
    connection.send_result(msg["id"], {"templates": templates})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_template",
        vol.Required("name"): str,
        vol.Required("props"): list,
        vol.Required("vbml"): vol.Any(dict, str),
        vol.Optional("id"): str,
    }
)
@websocket_api.async_response
async def websocket_save_template(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Create or update a named VBML template."""
    vbml_raw = msg["vbml"]
    if isinstance(vbml_raw, str):
        try:
            vbml = json.loads(vbml_raw)
        except json.JSONDecodeError as err:
            connection.send_result(
                msg["id"],
                {"ok": False, "error": f"VBML JSON is invalid: {err.msg}"},
            )
            return
    else:
        vbml = vbml_raw

    try:
        vbml = validate_vbml_payload(vbml)
    except vol.Invalid as err:
        connection.send_result(
            msg["id"],
            {"ok": False, "error": f"VBML schema error: {err}"},
        )
        return

    try:
        saved = await async_upsert_template(
            hass,
            name=msg["name"],
            props=msg["props"],
            vbml=vbml,
            template_id=msg.get("id"),
        )
    except ValueError as err:
        connection.send_result(msg["id"], {"ok": False, "error": str(err)})
        return

    await async_refresh_send_template_schema(hass)
    connection.send_result(msg["id"], {"ok": True, "template": saved})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_template",
        vol.Required("id"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_template(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a saved template."""
    try:
        await async_delete_template(hass, msg["id"])
    except ValueError as err:
        connection.send_result(msg["id"], {"ok": False, "error": str(err)})
        return
    await async_refresh_send_template_schema(hass)
    connection.send_result(msg["id"], {"ok": True})
