from __future__ import annotations
from homeassistant import core
from homeassistant.core import HomeAssistant
from homeassistant.components.conversation import agent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL, CONF_API_KEY, CONF_URL
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    ConfigEntryAuthFailed,
    TemplateError,
)
from homeassistant.components import conversation as conv

from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientResponseError,
    ClientError,
)

import logging, json, asyncio

from asyncio import timeout
from http import HTTPStatus

from .const import DOMAIN
from .localai_agent import LocalAIAgent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the LocaAI Conversation and Control component."""
    _LOGGER.debug("Setting Up LocalAI agent: %s", str(entry.data))

    agent = LocalAIAgent(hass, entry)

    try:
        async with timeout(10):
            await LocalAIAgent.test_connection(hass, entry.data)
    except ClientResponseError as err:
        if err.status == HTTPStatus.UNAUTHORIZED:
            _LOGGER.warning(f"API_KEY is invalid for {entry.data[CONF_URL]} : {err}")

            # Not rasing ConfigEntryAuthFailed as we have no ConfigFlow setup
            raise ConfigEntryNotReady(
                f"API_KEY is invalid for {entry.data[CONF_URL]}"
            ) from err
        _LOGGER.info(f"Response for {entry.data[CONF_URL]} returned error: {err}")
        raise ConfigEntryNotReady(err) from err
    except (
        ClientConnectorError,
        ClientError,
        asyncio.TimeoutError,
    ) as err:
        _LOGGER.warning(f"Could not connect to localAI: {err}")
        raise ConfigEntryNotReady(err) from err
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception(f"Unexpected exception: {err}")
        raise ConfigEntryNotReady(err) from err

    _LOGGER.debug("Sucessfully connected to localAI")

    conv.async_set_agent(hass, entry, agent)
    return True
