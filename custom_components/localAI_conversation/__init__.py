from __future__ import annotations
from homeassistant import core
from homeassistant.core import HomeAssistant
from homeassistant.components.conversation import agent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL, CONF_API_KEY, CONF_URL
from homeassistant.exceptions import ConfigEntryNotReady, TemplateError
from homeassistant.components import conversation as conv

import logging

from asyncio import timeout

from .const import DOMAIN
from .conversation import LocalAIAgent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the LocaAI Conversation and Control component."""

    _LOGGER.info("Setting Up LocalAI agent!")

    agent = LocalAIAgent(hass, entry)

    try:
        async with timeout(10):
            await LocalAIAgent.test_connection(hass, entry.data)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception", err)
        raise ConfigEntryNotReady(err) from err

    conv.async_set_agent(hass, entry, agent)
    return True
