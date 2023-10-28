"""Config flow for Local AI Conversation integration."""
from __future__ import annotations

from functools import partial
import logging
import types
from types import MappingProxyType
from typing import Any
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL, CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    TemplateSelector,
)
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientResponseError,
    ClientError,
)
import asyncio
from asyncio import timeout

from .const import (
    CONF_CHAT_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_K,
    CONF_TOP_P,
    DEFAULT_API_KEY,
    DEFAULT_URL,
    DEFAULT_VERIFY_SSL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    DEFAULT_TOP_P,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    DOMAIN,
)
from .conversation import LocalAIAgent

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY, default=DEFAULT_API_KEY): str,
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)

DEFAULT_OPTIONS = types.MappingProxyType(
    {
        CONF_PROMPT: DEFAULT_PROMPT,
        CONF_CHAT_MODEL: DEFAULT_CHAT_MODEL,
        CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
        CONF_TOP_P: DEFAULT_TOP_P,
        CONF_TOP_K: DEFAULT_TOP_K,
    }
)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Generative AI Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            async with timeout(10):
                await LocalAIAgent.test_connection(self.hass, user_input)
        except (
            ClientConnectorError,
            ClientError,
            asyncio.TimeoutError,
        ) as err:
            _LOGGER.warning("Failed to connect to server:", err)
            errors["base"] = ERROR_CANNOT_CONNECT
        except ClientResponseError as err:
            error_body = await resp.text()
            _LOGGER.info("Client error response error body: %s", error_body)
            if err.status == HTTPStatus.UNAUTHORIZED:
                errors["base"] = ERROR_INVALID_AUTH
            errors["base"] = ERROR_UNKNOWN
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception", err)
            errors["base"] = ERROR_UNKNOWN
        else:
            return self.async_create_entry(
                title="LocalAI Conversation", data=user_input
            )

        SCHEMA = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=user_input[CONF_API_KEY]): str,
                vol.Required(CONF_URL, default=user_input[CONF_URL]): str,
                vol.Required(
                    CONF_VERIFY_SSL, default=user_input[CONF_VERIFY_SSL]
                ): bool,
            }
        )

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA,
            errors=errors,
        )
