"""Constants for the LocalAI Conversation integration."""

DOMAIN = "localAI_conversation"

DEFAULT_API_KEY = "sk-00000000000000000"
DEFAULT_URL = "http://localhost:8080"
DEFAULT_VERIFY_SSL = True

CONF_PROMPT = "prompt"
DEFAULT_PROMPT = """This smart home is controlled by Home Assistant.

An overview of the areas and the devices in this smart home:
{%- for area in areas() %}
  {%- set area_info = namespace(printed=false) %}
  {%- for device in area_devices(area) -%}
    {%- if not device_attr(device, "disabled_by") and not device_attr(device, "entry_type") and device_attr(device, "name") %}
      {%- if not area_info.printed %}

{{ area_name(area) }}:
        {%- set area_info.printed = true %}
      {%- endif %}
- {{ device_attr(device, "name") }}{% if device_attr(device, "model") and (device_attr(device, "model") | string) not in (device_attr(device, "name") | string) %} ({{ device_attr(device, "model") }}){% endif %}
    {%- endif %}
  {%- endfor %}
{%- endfor %}

Answer the user's questions about the world truthfully.

"""
CONF_CHAT_MODEL = "chat_model"
DEFAULT_CHAT_MODEL = "models/chat-bison-001"
CONF_TEMPERATURE = "temperature"
DEFAULT_TEMPERATURE = 0.25
CONF_TOP_P = "top_p"
DEFAULT_TOP_P = 0.95
CONF_TOP_K = "top_k"
DEFAULT_TOP_K = 40

ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"
