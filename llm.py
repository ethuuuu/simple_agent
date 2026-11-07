"""
llm.py - the ONE place that knows how to talk to the local model.

oMLX serves models on this Mac behind an OpenAI-compatible HTTP API
(http://127.0.0.1:8000/v1). So we use the standard `openai` Python SDK and
simply point it at localhost. Nothing leaves the machine.

Configure with environment variables (no code edits needed to switch models):
    OMLX_BASE_URL  default http://127.0.0.1:8000/v1
    OMLX_API_KEY   the api_key from ~/.omlx/settings.json ("auth" section)
    MODEL          the model id as listed by:  curl localhost:8000/v1/models
"""
import os

from openai import OpenAI

BASE_URL = os.getenv("OMLX_BASE_URL", "http://127.0.0.1:8000/v1")
MODEL = os.getenv("MODEL", "gemma-4-26B-A4B-it-QAT-MLX-4bit")

# A single shared client. Long timeout because a 26-27B model on a MacBook Air
# can take a while to read a big prompt (prefill) before it starts answering.
client = OpenAI(base_url=BASE_URL, api_key=os.getenv("OMLX_API_KEY", "local"), timeout=600)


def chat(messages, tools=None):
    """Send the conversation to the model and return its reply message."""
    kwargs = {"model": MODEL, "messages": messages, "temperature": 0.2}
    if tools:
        kwargs["tools"] = tools
    return client.chat.completions.create(**kwargs).choices[0].message
