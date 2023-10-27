from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from homeassistant.components.conversation import agent
from homeassistant.config_entries import ConfigEntry

from urllib.parse import urljoin

ENDPOINT_MODELS = "models"

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


class LocalAIAgent(agent.AbstractConversationAgent):
    """LocalAI conversation agent."""

    def get_client(self, hass: HomeAssistant, entry: ConfigEntry):
        return async_get_clientsession(hass, verify_ssl=entry.data[CONF_VERIFY_SSL])

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.config_entry = entry
        self.client: get_client(hass, entry)
        self.history: dict[str, list[dict]] = {}

    @property
    def attribution(self):
        """Return the attribution."""
        return {
            "name": "LocaAI Conversation and Control",
            "url": "https://github.com/mimoja",
        }

    async def async_process(
        self, user_input: agent.ConversationInput
    ) -> agent.ConversationResult:
        """Process a sentence."""
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech("Test response")
        return agent.ConversationResult(conversation_id=None, response=response)

    def create_headers(config: dict[str, Any]):
        headers = {"Content-Type": "application/json"}
        api_key = config[CONF_API_KEY]
        if api_key != DEFAULT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def test_connection(hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Test connectivity to AI is OK."""
        headers = LocalAIAgent.create_headers(config)
        data = {}
        session = async_get_clientsession(hass)

        async with session.post(
            urljoin(config[CONF_URL], ENDPOINT_MODELS),
            headers=headers,
            data=data,
            verify_ssl=config[CONF_VERIFY_SSL],
        ) as res:
            res.raise_for_status()
        return cast(dict, await resp.json())


"""

    message = AlexaResponse(
        name="AddOrUpdateReport", namespace="Alexa.Discovery", payload=payload
    )

    message_serialized = message.serialize()
    session = async_get_clientsession(hass)

    assert config.endpoint is not None
    return await session.post(
        config.endpoint, headers=headers, json=message_serialized, allow_redirects=True
    )






    async def async_process_old(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        " " "Process a sentence. " " "
        raw_prompt = self.entry.options.get(CONF_PROMPT, DEFAULT_PROMPT)
        model = self.entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        max_tokens = self.entry.options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        top_p = self.entry.options.get(CONF_TOP_P, DEFAULT_TOP_P)
        temperature = self.entry.options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)

        if user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id]
        else:
            conversation_id = ulid.ulid()
            try:
                prompt = self._async_generate_prompt(raw_prompt)
            except TemplateError as err:
                _LOGGER.error("Error rendering prompt: %s", err)
                intent_response = intent.IntentResponse(language=user_input.language)
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    f"Sorry, I had a problem with my template: {err}",
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            messages = [{"role": "system", "content": prompt}]

        messages.append({"role": "user", "content": user_input.text})

        _LOGGER.debug("Prompt for %s: %s", model, messages)

        try:
            result = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                top_p=top_p,
                temperature=temperature,
                user=conversation_id,
            )
        except error.LocalAIError as err:
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem talking to Custom LocalAI compatible server: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        _LOGGER.debug("Response %s", result)
        response = result["choices"][0]["message"]
        messages.append(response)
        self.history[conversation_id] = messages

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response["content"])
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    def _async_generate_prompt(self, raw_prompt: str) -> str:
        " " "Generate a prompt for the user. " " "
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
            },
            parse_result=False,
        )

"""
