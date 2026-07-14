"""Frontend panel registration for Vestaboard-x."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "vestaboard-x"
PANEL_STATIC_PATH = f"/{DOMAIN}_static"
PANEL_FILENAME = "vestaboard-x-panel.js"
DATA_FRONTEND_READY = "frontend_ready"


def _integration_version() -> str:
    """Read version from manifest.json for cache-busting."""
    manifest = Path(__file__).with_name("manifest.json")
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("version", "0")
    except (OSError, json.JSONDecodeError):
        return "0"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Register static assets and the Vestaboard-x sidebar panel."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_FRONTEND_READY):
        return

    www_path = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PANEL_STATIC_PATH,
                str(www_path),
                cache_headers=False,
            )
        ]
    )

    version = await hass.async_add_executor_job(_integration_version)
    js_url = f"{PANEL_STATIC_PATH}/{PANEL_FILENAME}?v={version}"

    try:
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Vestaboard-x",
            sidebar_icon="mdi:bulletin-board",
            frontend_url_path=PANEL_URL_PATH,
            config={
                "_panel_custom": {
                    "name": "vestaboard-x-panel",
                    "embed_iframe": False,
                    "trust_external": False,
                    "js_url": js_url,
                }
            },
            require_admin=False,
        )
    except ValueError:
        # Panel already registered (e.g. reload)
        _LOGGER.debug("Vestaboard-x panel already registered")

    domain_data[DATA_FRONTEND_READY] = True
