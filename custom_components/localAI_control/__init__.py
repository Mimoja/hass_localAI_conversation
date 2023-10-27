from homeassistant import core
from homeassistant.components import conversation
from homeassistant.const import CONF_NAME, CONF_VERIFY_SSL
from homeassistant.helpers.httpx_client import get_async_client


def get_agent(hass: HomeAssistant, entry: ConfigEntry) -> Glances:
    """Return the api for an LocalAI compatible API."""
    entry_data.pop(CONF_NAME, None)
    httpx_client = get_async_client(hass, verify_ssl=entry_data[CONF_VERIFY_SSL])
    return LocalAIAgent(hass, entry_data, httpx_client=httpx_client)

async def async_setup(hass: core.HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the LocaAI Conversation and Control component."""

    try:
        await hass.async_add_executor_job(
            partial(
                palm.get_model, entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
            )
        )
    except ClientError as err:
        if err.reason == "API_KEY_INVALID":
            _LOGGER.error("Invalid API key: %s", err)
            return False
        raise ConfigEntryNotReady(err) from err

    conversation.async_set_agent(hass, entry, )
    return True
