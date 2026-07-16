"""Constants for the Vestaboard integration."""

from typing import Final

DOMAIN: Final = "vestaboard"

# justify (horizontal) and align (vertical) values
ALIGN_BOTTOM: Final = "bottom"
ALIGN_CENTER: Final = "center"
ALIGN_JUSTIFIED: Final = "justified"
ALIGN_LEFT: Final = "left"
ALIGN_RIGHT: Final = "right"
ALIGN_TOP: Final = "top"
ALIGN_HORIZONTAL: Final = [ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER, ALIGN_JUSTIFIED]
ALIGN_VERTICAL: Final = [ALIGN_TOP, ALIGN_BOTTOM, ALIGN_CENTER, ALIGN_JUSTIFIED]

CONF_ALIGN: Final = "align"
CONF_ATTRIBUTE: Final = "attribute"
CONF_BYPASS_QUIET_HOURS: Final = "bypass_quiet_hours"
CONF_COMPONENTS: Final = "components"
CONF_DURATION: Final = "duration"
CONF_ENABLEMENT_TOKEN: Final = "enablement_token"
CONF_ENTITY_ID: Final = "entity_id"
CONF_HEIGHT: Final = "height"
CONF_INTRO_DURATION: Final = "intro_duration"
CONF_JUSTIFY: Final = "justify"
CONF_MESSAGE: Final = "message"
DEFAULT_INTRO_DURATION: Final = 8
CONF_MODEL: Final = "model"
CONF_NAME: Final = "name"
CONF_PROPS: Final = "props"
CONF_QUIET_END: Final = "quiet_end"
CONF_QUIET_START: Final = "quiet_start"
CONF_STEP_INTERVAL_MS: Final = "step_interval_ms"
CONF_STEP_SIZE: Final = "step_size"
CONF_STRATEGY: Final = "strategy"
CONF_TEMPLATE: Final = "template"
CONF_TEMPLATE_ID: Final = "template_id"
CONF_TRANSITIONS: Final = (
    "classic",
    "column",
    "reverse-column",
    "edges-to-center",
    "row",
    "diagonal",
    "random",
)
CONF_VBML: Final = "vbml"
CONF_WIDTH: Final = "width"
CONF_X: Final = "x"
CONF_Y: Final = "y"

DATA_HASS_CONFIG: Final = "hass_config"

COLOR_BLACK: Final = "black"
COLOR_WHITE: Final = "white"

SERVICE_MESSAGE: Final = "message"
SERVICE_SEND_TEMPLATE: Final = "send_template"
