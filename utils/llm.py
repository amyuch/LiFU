# utils/llm.py
"""
General-Purpose LLM Interface for \name\ Pipeline
- Single source of truth for API client
- Prompt + response + token logging
- Retry, timeout, error handling
- NO hardware-specific logic
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any
import openai
from openai import OpenAI, APIError, RateLimitError, Timeout
from pathlib import Path
import yaml

# === Logging ===
log = logging.getLogger("llm")
log.setLevel(logging.INFO)

# === Load Config ===
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
if not CONFIG_PATH.exists():
    raise FileNotFoundError("config.yaml not found in project root")

CONFIG = yaml.safe_load(CONFIG_PATH.read_text())
LLM_CONFIG = CONFIG.get("llm", {})

os.environ["OPENAI_API_BASE"] = LLM_CONFIG.get("base_url")
os.environ["OPENAI_API_KEY"] = LLM_CONFIG.get("api_key")

# === LLM Client ===
# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY", LLM_CONFIG.get("api_key")),
#     base_url=os.getenv("OPENAI_API_BASE", LLM_CONFIG.get("base_url")),
#     timeout=LLM_CONFIG.get("timeout_sec", 600),
# )
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
    timeout=openai.Timeout(LLM_CONFIG.get("time_sec"), connect=LLM_CONFIG.get("time_sec"))
)

# === General Call ===
def call(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Tuple[str, int, int]:
    """
    General LLM call.
    Returns: (response_text, prompt_tokens, completion_tokens)
    """
    model = model or LLM_CONFIG.get("model", "gpt-4o")
    temperature = temperature or LLM_CONFIG.get("temperature", 0.2)
    max_tokens = max_tokens or LLM_CONFIG.get("max_tokens", 2048)
    system_prompt = system_prompt or LLM_CONFIG.get("system_prompt", "You are a helpful assistant.")

    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        p_tokens = response.usage.prompt_tokens
        c_tokens = response.usage.completion_tokens

        log.info(f"[LLM] Success | {model} | {p_tokens}+{c_tokens} tokens")
        return content, p_tokens, c_tokens

    except RateLimitError as e:
        log.error(f"[LLM] Rate limit: {e}")
        return "", 0, 0
    except Timeout as e:
        log.error(f"[LLM] Timeout: {e}")
        return "", 0, 0
    except APIError as e:
        log.error(f"[LLM] API error {e.status_code}: {e.message}")
        return "", 0, 0
    except Exception as e:
        log.error(f"[LLM] Unexpected error: {e}")
        return "", 0, 0