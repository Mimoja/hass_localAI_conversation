from homeassistant.helpers import intent, httpx_client
from homeassistant.components.conversation import agent

class LocalAIAgent(agent.AbstractConversationAgent):
    """LocalAI conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, httpx_client: httpx_client) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.config_entry = entry
        self.client: httpx_client
        self.history: dict[str, list[dict]] = {}

    @property
    def attribution(self):
        """Return the attribution."""
        return {"name": "LocaAI Conversation and Control", "url": "https://github.com/mimoja"}


    @abstractmethod
    async def async_process(self, user_input: agent.ConversationInput) -> agent.ConversationResult:
        """Process a sentence."""
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech("Test response")
        return agent.ConversationResult(
            conversation_id=None,
            response=response
        )

"""
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
