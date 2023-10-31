from __future__ import annotations
from homeassistant.core import HomeAssistant

from homeassistant.components.conversation import agent, DefaultAgent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.util import ulid
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    TemplateError,
    HomeAssistantError,
)
from homeassistant.helpers import intent, template
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError

from urllib.parse import urljoin
import logging, json
from http import HTTPStatus
import pydantic

ENDPOINT_MODELS = "models"
ENDPOINT_CHAT_COMPLETION = "chat/completions"


_LOGGER = logging.getLogger(__name__)


from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL, CONF_API_KEY, CONF_URL

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
    DOMAIN,
)

from typing import List


def _buildFunctions(hass: HomeAssistant):
    services = hass.services.async_services()
    for service in services:
        _LOGGER.info("- Service: %s", service)

    functions = [
        {
            "name": "get_services",
            "description": "Get all list of all known services",
        },
        {
            "name": "get_service_info",
            "description": "Get all functions for a given service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service to inspect",
                    },
                },
                "required": ["service"],
            },
        },
        {
            "name": "call_service",
            "description": "Call a function with a service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service to call",
                    },
                    "function": {
                        "type": "string",
                        "description": "The function to call",
                    },
                },
                "required": ["service", "function"],
            },
        },
    ]
    return functions


class LocalAIAgent(DefaultAgent):
    """LocalAI conversation agent."""

    def _get_session(self):
        return async_get_clientsession(
            self.hass, verify_ssl=self.config_entry.data[CONF_VERIFY_SSL]
        )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.config_entry = entry
        self.session: self._get_session()
        self.history: dict[str, list[dict]] = {}

    @property
    def attribution(self):
        """Return the attribution."""
        return {
            "name": "LocaAI Conversation and Control",
            "url": "https://github.com/mimoja",
        }

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def test_connection(hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Test connectivity to AI is OK."""
        headers = LocalAIAgent.create_headers(config[CONF_API_KEY])
        data = {}
        session = async_get_clientsession(hass)

        async with session.get(
            urljoin(config[CONF_URL], ENDPOINT_MODELS),
            headers=headers,
            data=data,
            verify_ssl=config[CONF_VERIFY_SSL],
            raise_for_status=True,
        ) as res:
            await res.json()

    def create_headers(api_key: str):
        headers = {"Content-Type": "application/json"}
        if api_key != DEFAULT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _format_error_response(
        self, user_input: agent.ConversationInput, error_str: str, conversation_id
    ) -> agent.ConversationResult:
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_error(
            intent.IntentResponseErrorCode.UNKNOWN,
            error_str,
        )
        return agent.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    async def async_send_to_ai(self, messages):
        model = self.config_entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        top_p = self.config_entry.options.get(CONF_TOP_P, DEFAULT_TOP_P)
        temperature = self.config_entry.options.get(
            CONF_TEMPERATURE, DEFAULT_TEMPERATURE
        )
        url = self.config_entry.data.get(CONF_URL, DEFAULT_URL)
        verify_ssl = self.config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        api_key = self.config_entry.data.get(CONF_API_KEY, DEFAULT_API_KEY)

        _LOGGER.debug("Prompt for %s: %s", model, messages)

        headers = LocalAIAgent.create_headers(api_key)
        data = {
            "model": model,
            "messages": messages,
            "functions": _buildFunctions(self.hass),
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }
        _LOGGER.debug(
            "Sending request %s",
            json.dumps({"header": headers, "body": data}),
        )

        async with self.session.post(
            urljoin(url + "/", ENDPOINT_CHAT_COMPLETION),
            headers=headers,
            data=json.dumps(data),
            verify_ssl=verify_ssl,
        ) as res:
            if res.status != HTTPStatus.OK:
                _LOGGER.warning("LocalAI Call failed with http code %s", res.status)
            try:
                res.raise_for_status()
            except ClientResponseError as err:
                _LOGGER.error(f"Request failed: {err}")
                raise Exception(f"Request failed: {err}")

            try:
                result = await res.json()
            except ValueError as err:
                # If json decoder could not parse the response
                _LOGGER.exception("Failed to parse response")
                raise Exception(f"Response misformated: {err}")

            try:
                choices = result["choices"]
            except KeyError as err:
                _LOGGER.exception("No field choices in response from AI %s", result)
                raise Exception(f"No Answer provided: {err}")

            try:
                response = choices[0]["message"]
            except KeyError as err:
                _LOGGER.exception(
                    "No field message in choices in response from AI %s", result
                )
                raise Exception(f"No Answer provided: {err}")

            _LOGGER.debug("Result %s", result)
            _LOGGER.debug("Response %s", response)

            messages.append(response)
            return messages

    async def async_process(
        self, user_input: agent.ConversationInput
    ) -> agent.ConversationResult:
        """Process a sentence."""
        _LOGGER.debug("Processing in %s: %s", user_input.language, user_input.text)

        if "session" not in dir(self) or not self.session:
            self.session = self._get_session()

        if user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id]
        else:
            conversation_id = ulid.ulid()
            try:
                raw_prompt = self.config_entry.options.get(CONF_PROMPT, DEFAULT_PROMPT)
                prompt = self._async_generate_prompt(raw_prompt)
            except TemplateError as err:
                _LOGGER.error(f"Error rendering prompt: {err}")
                return self._format_error_response(
                    user_input,
                    f"Sorry, I had a problem with my template: {err}",
                    conversation_id,
                )

            messages = [{"role": "system", "content": prompt}]

        messages.append({"role": "user", "content": user_input.text})

        # Main execution
        messages = await self.async_send_to_ai(messages)

        try:
            self.history[conversation_id] = messages
        except Exception as err:
            return self._format_error_response(
                user_input,
                f"{err}",
                conversation_id,
            )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(messages[-1]["content"])
        return agent.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    def _async_generate_prompt(self, raw_prompt: str) -> str:
        """Generate a prompt for the user."""
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
            },
            parse_result=False,
        )
