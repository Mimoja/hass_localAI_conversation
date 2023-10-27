from __future__ import annotations
from homeassistant import core
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL, CONF_API_KEY, CONF_URL
from homeassistant.exceptions import ConfigEntryNotReady, TemplateError
import logging
from .const import DOMAIN
from .conversation import LocalAIAgent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the LocaAI Conversation and Control component."""

    _LOGGER.info("Setting Up LocalAI agent!")
    agent = LocalAIAgent(hass, entry)

    try:
        await hass.async_add_executor_job(partial(agent.check_connection))
    except Error as err:
        if err.reason == "API_KEY_INVALID":
            _LOGGER.error("Invalid API key: %s", err)
            return False
        raise ConfigEntryNotReady(err) from err

    conversation.async_set_agent(
        hass,
        entry,
    )
    return True
